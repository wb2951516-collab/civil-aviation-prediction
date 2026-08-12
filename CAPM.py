from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import tkinter.font as tkfont
import os
import sys
import logging
import subprocess
import threading
from datetime import datetime, timedelta
import warnings
import json
import calendar
from typing import Dict, List, Tuple
# 解决高分屏字体过小和模糊问题
import ctypes
try:
    # 启用高 DPI 感知 (Windows 8.1+)
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        # 兼容旧版 Windows (Windows Vista/7/8)
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

warnings.filterwarnings('ignore')

from capm.backtest import recommend_weights_from_backtest, rolling_backtest
from capm.config_store import ConfigStore
from capm.datasource import ExternalDataManager
from capm.growth import apply_annual_growth_adjustment, growth_sanity_check
from capm.holiday import (
    apply_holiday_effects,
    build_intervention_exog,
    compute_holiday_effect,
    compute_month_spring_travel_days,
    compute_spring_travel_span,
    get_spring_festival_date,
)
from capm.logging_setup import configure_logging
from capm.manuals import MANUALS, REMOVED_NOTES
from capm.markov import analyze_regimes
from capm.models import ensemble_forecast, holt_winters_forecast, sarima_forecast, sarimax_intervention_forecast, simple_seasonal_forecast
from capm.theme import COLORS as T_COLORS
from capm.theme import apply_theme, card_frame


REQUIRED_MODULES = [
    "pandas",
    "numpy",
    "matplotlib",
    "statsmodels",
    "openpyxl",
]


def _early_log_path() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    logs_dir = os.path.join(base, "CAPM", "logs")
    try:
        os.makedirs(logs_dir, exist_ok=True)
    except Exception:
        pass
    return os.path.join(logs_dir, "early_crash.log")


def check_dependencies() -> Tuple[bool, List[str]]:
    import importlib

    missing = []
    for name in REQUIRED_MODULES:
        try:
            importlib.import_module(name)
        except Exception:
            missing.append(name)
    return len(missing) == 0, missing


class TreeviewTooltip:
    def __init__(self, tree: ttk.Treeview, text_provider, delay_ms: int = 450):
        self.tree = tree
        self.text_provider = text_provider
        self.delay_ms = int(delay_ms)
        self.tip = None
        self.label = None
        self._after = None
        self._press_after = None
        self._last_iid = None

        self.tree.bind("<Motion>", self._on_motion, add="+")
        self.tree.bind("<Leave>", self._hide, add="+")
        self.tree.bind("<ButtonPress-1>", self._on_press, add="+")
        self.tree.bind("<ButtonRelease-1>", self._on_release, add="+")

    def _on_motion(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid:
            self._hide()
            return
        if iid == self._last_iid:
            return
        self._last_iid = iid
        self._schedule_show(event, iid)

    def _on_press(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        if self._press_after is not None:
            try:
                self.tree.after_cancel(self._press_after)
            except Exception:
                pass
        self._press_after = self.tree.after(650, lambda: self._show(event, iid))

    def _on_release(self, event):
        if self._press_after is not None:
            try:
                self.tree.after_cancel(self._press_after)
            except Exception:
                pass
            self._press_after = None

    def _schedule_show(self, event, iid):
        if self._after is not None:
            try:
                self.tree.after_cancel(self._after)
            except Exception:
                pass
        self._after = self.tree.after(self.delay_ms, lambda: self._show(event, iid))

    def _show(self, event, iid):
        self._after = None
        text = ""
        try:
            text = str(self.text_provider(iid) or "").strip()
        except Exception:
            text = ""
        if not text:
            self._hide()
            return

        if self.tip is None:
            self.tip = tk.Toplevel(self.tree)
            self.tip.wm_overrideredirect(True)
            self.tip.attributes("-topmost", True)
            self.label = tk.Label(
                self.tip,
                text=text,
                justify=tk.LEFT,
                background="#111827",
                foreground="#F9FAFB",
                relief=tk.SOLID,
                borderwidth=1,
                padx=10,
                pady=6,
            )
            self.label.pack()
        else:
            self.label.configure(text=text)

        x = self.tree.winfo_rootx() + int(event.x) + 16
        y = self.tree.winfo_rooty() + int(event.y) + 16
        self.tip.geometry(f"+{x}+{y}")

    def _hide(self, event=None):
        if self._after is not None:
            try:
                self.tree.after_cancel(self._after)
            except Exception:
                pass
            self._after = None
        if self.tip is not None:
            try:
                self.tip.destroy()
            except Exception:
                pass
            self.tip = None
            self.label = None
        self._last_iid = None


APP_WINDOW_TITLE = "民航旅客运输量预测系统 (最终版)"


def _try_activate_existing_window() -> bool:
    if os.name != "nt":
        return False
    try:
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
        user32.FindWindowW.restype = wintypes.HWND
        user32.ShowWindow.argtypes = [wintypes.HWND, wintypes.INT]
        user32.ShowWindow.restype = wintypes.BOOL
        user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        user32.SetForegroundWindow.restype = wintypes.BOOL

        hwnd = user32.FindWindowW(None, APP_WINDOW_TITLE)
        if not hwnd:
            return False

        SW_RESTORE = 9
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        return True
    except Exception:
        logging.exception("激活已运行窗口失败")
        return False


def _bring_window_to_front(root: tk.Tk):
    try:
        root.deiconify()
    except Exception:
        pass
    try:
        root.lift()
    except Exception:
        pass
    try:
        root.focus_force()
    except Exception:
        pass
    try:
        root.attributes("-topmost", True)
        root.after(250, lambda: root.attributes("-topmost", False))
    except Exception:
        pass


class FinalForecastApp:
    def __init__(self, root):
        self.root = root
        self.style = ttk.Style(self.root)
        try:
            self.base_scaling = float(self.root.tk.call("tk", "scaling"))
        except Exception:
            self.base_scaling = 1.0

        self.ui_scale_var = tk.DoubleVar(value=1.0)
        self.view_mode_var = tk.StringVar(value="舒适")

        self._fonts = {}
        self._ui_ready = False
        try:
            self.root.report_callback_exception = self._handle_tk_exception
        except Exception:
            pass
        self.root.title("民航旅客运输量预测系统 (最终版)")
        self.root.geometry("1400x900")

        # 应用现代化主题
        try:
            apply_theme(self.root)
        except Exception:
            pass

        # 初始化数据
        self.data = None
        self.forecast_data = None
        self.model_results = {}

        # 外部数据源（GDP / ASK 管理控制台）
        self.external_mgr = ExternalDataManager()
        self.external_enabled = True          # 外部因子是否参与预测（管理控制台开关）
        self.external_status_text = "外部数据未加载"

        self.config_store = ConfigStore()
        self.config = self.config_store.load()
        self.profile = self.config_store.get_active_profile()
        self.active_profile_name = self.config.get("active_profile", "default")

        self.holiday_cfg = dict(self.profile.get("holiday", {}))
        self.growth_cfg = dict(self.profile.get("growth", {}))
        self.model_cfg = dict(self.profile.get("model", {}))
        self.spring_festival_dates = dict(self.profile.get("spring_festival_dates", {}))

        self.lunar_config = {
            "spring_festival_effect": float(self.holiday_cfg.get("spring_festival_effect", 1.15)),
            "summer_vacation_effect": float(self.holiday_cfg.get("summer_vacation_effect", 1.10)),
            "may_day_effect": float(self.holiday_cfg.get("may_day_effect", 1.05)),
            "national_day_effect": float(self.holiday_cfg.get("national_day_effect", 1.08)),
            "winter_peak_effect": float(self.holiday_cfg.get("winter_peak_effect", 1.03)),
            "annual_growth_rate": float(self.growth_cfg.get("annual_growth_rate", 0.027)),
            "spring_travel_before_days": int(self.holiday_cfg.get("spring_travel_before_days", 15)),
            "spring_travel_after_days": int(self.holiday_cfg.get("spring_travel_after_days", 24)),
        }

        # 创建界面
        self.create_widgets()

        self.root.after(10, self.load_sample_data)

    def show_help_info(self):
        """显示帮助信息"""
        help_text = (
            "Civil aviation passenger traffic volume prediction model\n"
            "版权所有人：SuperM"
        )
        messagebox.showinfo("关于系统", help_text)

    def _handle_tk_exception(self, exc_type, exc_value, exc_tb):
        logging.exception("GUI异常", exc_info=(exc_type, exc_value, exc_tb))
        try:
            from capm.app_paths import AppPaths

            log_path = AppPaths().log_path()
        except Exception:
            log_path = None
        msg = f"{exc_value}"
        if log_path:
            msg += f"\n\n日志位置：{log_path}"
        try:
            messagebox.showerror("发生错误", msg)
        except Exception:
            pass

    def _bind_drag_scroll(self, widget):
        """绑定拖拽滚动事件"""
        widget.bind("<ButtonPress-1>", self._on_drag_start, add="+")
        widget.bind("<B1-Motion>", self._on_drag_motion, add="+")
        if isinstance(widget, ttk.Treeview):
            widget._drag_start_y = None
            widget._drag_start_x = None

    def _on_drag_start(self, event):
        widget = event.widget
        if isinstance(widget, tk.Canvas):
            widget.scan_mark(event.x, event.y)
        else:
            widget._drag_start_y = event.y
            widget._drag_start_x = event.x

    def _on_drag_motion(self, event):
        widget = event.widget
        if isinstance(widget, tk.Canvas):
            widget.scan_dragto(event.x, event.y, gain=1)
            return

        if getattr(widget, '_drag_start_y', None) is None:
            return

        dy = widget._drag_start_y - event.y
        dx = widget._drag_start_x - event.x

        if isinstance(widget, ttk.Treeview):
            if abs(dy) > 5:
                steps = int(dy / 20)
                if steps != 0:
                    widget.yview_scroll(-steps, "units")
                    widget._drag_start_y = event.y
            
            if abs(dx) > 5:
                 steps = int(dx / 20)
                 if steps != 0:
                     widget.xview_scroll(-steps, "units")
                     widget._drag_start_x = event.x

    def _apply_ui_settings(self):
        if not getattr(self, "_ui_ready", False):
            return

        mode = str(self.view_mode_var.get() or "舒适")
        if mode not in ["紧凑", "舒适", "宽松"]:
            mode = "舒适"
            self.view_mode_var.set(mode)

        scale = float(self.ui_scale_var.get() or 1.0)
        if scale < 0.8:
            scale = 0.8
            self.ui_scale_var.set(scale)
        if scale > 1.5:
            scale = 1.5
            self.ui_scale_var.set(scale)

        try:
            self.root.tk.call("tk", "scaling", float(self.base_scaling) * float(scale))
        except Exception:
            pass

        base_font = tkfont.nametofont("TkDefaultFont")
        family = base_font.cget("family")

        mode_base = {"紧凑": 10, "舒适": 11, "宽松": 12}[mode]
        # 增大基础行高以增加上下内边距
        mode_row = {"紧凑": 28, "舒适": 36, "宽松": 44}[mode]
        mode_pad = {"紧凑": 6, "舒适": 10, "宽松": 14}[mode]

        tree_size = max(9, int(round(mode_base * scale)))
        heading_size = max(10, int(round((mode_base + 1) * scale)))
        row_height = max(24, int(round(mode_row * scale)))

        if "tree" not in self._fonts:
            self._fonts["tree"] = tkfont.Font(self.root, family=family, size=tree_size)
            self._fonts["tree_heading"] = tkfont.Font(self.root, family=family, size=heading_size, weight="bold")
            self._fonts["toolbar"] = tkfont.Font(self.root, family=family, size=max(9, int(round(10 * scale))))
        else:
            self._fonts["tree"].configure(size=tree_size)
            self._fonts["tree_heading"].configure(size=heading_size)
            self._fonts["toolbar"].configure(size=max(9, int(round(10 * scale))))

        # 配置 Treeview 样式，增加行高（现代化外观）
        self.style.configure("Forecast.Treeview", font=self._fonts["tree"], rowheight=row_height,
                              background=T_COLORS["bg_card"], fieldbackground=T_COLORS["bg_card"],
                              foreground=T_COLORS["text_main"], borderwidth=0)
        self.style.map("Forecast.Treeview", background=[("selected", T_COLORS["selected"])],
                       foreground=[("selected", T_COLORS["text_main"])])
        # 增加表头内边距和字体
        self.style.configure("Forecast.Treeview.Heading", font=self._fonts["tree_heading"],
                              padding=(int(10*scale), int(8*scale)),
                              background="#E8EDF5", foreground=T_COLORS["text_main"],
                              borderwidth=0, relief="flat")
        self.style.map("Forecast.Treeview.Heading", background=[("active", "#DDE6F2")])
        self.style.configure("Forecast.Horizontal.TScale", padding=(mode_pad, 0),
                              background=T_COLORS["bg_window"], troughcolor="#D8DEE8",
                              bordercolor=T_COLORS["border"])
        self.style.configure("Forecast.TLabel", font=self._fonts["toolbar"], background=T_COLORS["bg_window"])

        # 文本框字体缩放
        text_font_size = max(9, int(round(10 * scale)))
        if hasattr(self, "stats_text"):
            self.stats_text.configure(font=('Consolas', text_font_size))
        if hasattr(self, "info_text"):
            # 注意：info_text 可能被 destroy 或未创建，这里检查属性
            pass

        # 比例缩放：调整所有列宽
        if hasattr(self, "forecast_tree"):
            try:
                self.forecast_tree.configure(style="Forecast.Treeview")
                self.forecast_tree.column("年份", width=int(90 * scale), minwidth=int(70 * scale), anchor=tk.CENTER, stretch=False)
                self.forecast_tree.column("月份", width=int(80 * scale), minwidth=int(60 * scale), anchor=tk.CENTER, stretch=False)
                self.forecast_tree.column("旅客运输量", width=int(180 * scale), minwidth=int(130 * scale), anchor=tk.E, stretch=True)
                self.forecast_tree.column("春运天数", width=int(100 * scale), minwidth=int(80 * scale), anchor=tk.CENTER, stretch=False)
                self.forecast_tree.column("增长率", width=int(110 * scale), minwidth=int(90 * scale), anchor=tk.E, stretch=False)
            except Exception:
                pass

        if hasattr(self, "history_tree"):
            try:
                self.history_tree.configure(style="Forecast.Treeview")
                self.history_tree.column("年份", width=int(90 * scale), minwidth=int(70 * scale), anchor=tk.CENTER, stretch=False)
                self.history_tree.column("月份", width=int(80 * scale), minwidth=int(60 * scale), anchor=tk.CENTER, stretch=False)
                self.history_tree.column("旅客运输量", width=int(180 * scale), minwidth=int(130 * scale), anchor=tk.E, stretch=True)
            except Exception:
                pass

        # 同步更新现有图表（如果有）
        self._refresh_all_charts()

        if hasattr(self, "forecast_zoom_value_label"):
            try:
                self.forecast_zoom_value_label.configure(text=f"{int(round(scale * 100))}%")
            except Exception:
                pass

    def _refresh_all_charts(self):
        """刷新所有图表以适应新的缩放比例"""
        # 刷新预测图表
        if hasattr(self, "_last_history") and getattr(self, "_last_history", None) is not None:
            try:
                self.plot_forecast(self._last_history, self._last_forecast)
            except Exception:
                pass
        
        # 刷新分析图表
        if hasattr(self, "_last_analysis_ts") and getattr(self, "_last_analysis_ts", None) is not None:
            try:
                self.update_analysis_charts(self._last_analysis_ts, self._last_analysis_decomp, self._last_analysis_stats)
            except Exception:
                pass

    def _on_ui_scale_change(self, _=None):
        self._apply_ui_settings()

    def _set_scale(self, scale: float):
        try:
            self.ui_scale_var.set(float(scale))
        except Exception:
            pass
        self._apply_ui_settings()

    def _reset_scale(self):
        self._set_scale(1.0)

    def _on_ctrl_mousewheel_zoom(self, event):
        delta = 0
        try:
            delta = int(event.delta)
        except Exception:
            delta = 0
        step = 0.05
        if delta > 0:
            self._set_scale(min(1.5, float(self.ui_scale_var.get()) + step))
        elif delta < 0:
            self._set_scale(max(0.8, float(self.ui_scale_var.get()) - step))

    def _forecast_tooltip_text(self, iid: str) -> str:
        values = self.forecast_tree.item(iid, "values")
        if not values or len(values) < 5:
            return ""
        year, month, passenger, spring_days, growth = values[:5]
        s = [
            f"年份：{year}    月份：{month}",
            f"旅客运输量：{passenger}",
            f"春运天数：{spring_days} 天",
            f"月度增长率：{growth}",
            "按住 Ctrl 滚轮可缩放视图",
        ]
        return "\n".join(s)

    def create_widgets(self):
        """创建界面组件"""
        # 标题
        title_frame = tk.Frame(self.root, bg='#f0f0f0')
        title_frame.pack(fill=tk.X, padx=20, pady=10)

        # 帮助按钮 (放置在右上角)
        help_btn = ttk.Button(title_frame, text="❓ 帮助", width=8, command=self.show_help_info)
        help_btn.pack(side=tk.RIGHT, anchor=tk.N, padx=10)

        tk.Label(title_frame, text="民航旅客运输量预测系统 (最终版)",
                 font=('微软雅黑', 20, 'bold'), bg='#f0f0f0').pack()

        tk.Label(title_frame, text="春运比例拆分 + 年度增长率校准 + 精选算法集成 (V1.1)",
                 font=('微软雅黑', 11), bg='#f0f0f0', fg='#666').pack()

        # 控制面板（卡片化分组）
        control_frame = tk.Frame(self.root, bg=T_COLORS["bg_window"])
        control_frame.pack(fill=tk.X, padx=14, pady=(2, 8))

        # ---- 左侧：数据操作区 ----
        left_buttons = card_frame(control_frame, "数据操作")
        left_buttons.pack(side=tk.LEFT, fill=tk.X)

        ttk.Button(left_buttons, text="导入Excel数据", style="Modern.TButton",
                   command=self.import_data).pack(side=tk.LEFT, padx=4, pady=4)
        ttk.Button(left_buttons, text="手动录入数据", style="Secondary.TButton",
                   command=self.manual_input).pack(side=tk.LEFT, padx=4, pady=4)
        ttk.Button(left_buttons, text="数据预处理", style="Secondary.TButton",
                   command=self.data_preprocessing).pack(side=tk.LEFT, padx=4, pady=4)
        ttk.Button(left_buttons, text="管理控制台", style="Modern.TButton",
                   command=self.open_admin_console).pack(side=tk.LEFT, padx=4, pady=4)

        # ---- 右侧：模型与预测区 ----
        right_controls = card_frame(control_frame, "模型与预测")
        right_controls.pack(side=tk.RIGHT)

        # 精选算法集合（V1.1：线性回归已移除，详见算法手册）
        self.model_var = tk.StringVar(value="ensemble")
        models = [("融合模型", "ensemble"), ("Holt-Winters", "hw"), ("SARIMA", "sarima")]
        for text, value in models:
            ttk.Radiobutton(right_controls, text=text, variable=self.model_var,
                            value=value).pack(side=tk.LEFT, padx=3, pady=4)

        # 模式：自动推荐（默认）/ 手动选择
        self.model_mode_var = tk.StringVar(value="auto")
        ttk.Checkbutton(right_controls, text="自动推荐", variable=self.model_mode_var,
                        onvalue="auto", offvalue="manual").pack(side=tk.LEFT, padx=(8, 2), pady=4)

        ttk.Button(right_controls, text="运行预测", style="Modern.TButton",
                   command=self.run_forecast).pack(side=tk.LEFT, padx=6, pady=4)
        ttk.Button(right_controls, text="算法手册", style="Toolbar.TButton",
                   command=self.open_manual_viewer).pack(side=tk.LEFT, padx=2, pady=4)

        # 主内容区域
        main_notebook = ttk.Notebook(self.root)
        main_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Tab 1: 数据管理
        self.create_data_tab(main_notebook)

        # Tab 2: 模型分析
        self.create_analysis_tab(main_notebook)

        # Tab 3: 预测结果
        self.create_forecast_tab(main_notebook)

        # Tab 4: 配置参数
        self.create_config_tab(main_notebook)

        self._ui_ready = True
        self._apply_ui_settings()

        # 状态栏
        self.status_bar = tk.Label(self.root, text="就绪", bd=1, relief=tk.SUNKEN,
                                   anchor=tk.W, bg='#e0e0e0')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_data_tab(self, notebook):
        """创建数据管理标签页"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="📊 数据管理")

        # 顶部工具栏 (新增缩放控制)
        top_bar = tk.Frame(tab, bg="#f0f0f0")
        top_bar.pack(fill=tk.X, padx=10, pady=(5, 5))

        tk.Label(top_bar, text="显示比例", bg="#f0f0f0").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Scale(
            top_bar, from_=0.8, to=1.5, orient=tk.HORIZONTAL, length=200,
            variable=self.ui_scale_var, command=self._on_ui_scale_change,
            style="Forecast.Horizontal.TScale"
        ).pack(side=tk.LEFT)
        ttk.Button(top_bar, text="重置", command=self._reset_scale).pack(side=tk.LEFT, padx=10)
        tk.Label(top_bar, text="支持Ctrl+滚轮缩放 / 拖拽滚动", bg="#f0f0f0", fg="#666").pack(side=tk.RIGHT)

        # 主内容区域 (使用 PanedWindow 实现等比例同步缩放)
        self.data_paned = ttk.PanedWindow(tab, orient=tk.HORIZONTAL)
        self.data_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 左侧：历史数据
        left_frame = tk.Frame(self.data_paned)
        self.data_paned.add(left_frame, weight=1)

        tk.Label(left_frame, text="历史数据", font=('微软雅黑', 12, 'bold')).pack(anchor=tk.W, pady=(0, 5))

        # 创建历史数据表格
        columns = ('年份', '月份', '旅客运输量')
        self.history_tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=15, style="Forecast.Treeview")

        for col in columns:
            self.history_tree.heading(col, text=col)
        
        # 初始列宽（会在 _apply_ui_settings 中被 scale 调整）
        self.history_tree.column("年份", width=90, anchor=tk.CENTER, stretch=False)
        self.history_tree.column("月份", width=80, anchor=tk.CENTER, stretch=False)
        self.history_tree.column("旅客运输量", width=180, anchor=tk.E, stretch=True)

        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定拖拽和斑马纹
        self._bind_drag_scroll(self.history_tree)
        self.history_tree.tag_configure("odd", background=T_COLORS["row_alt"])
        self.history_tree.bind("<Control-MouseWheel>", self._on_ctrl_mousewheel_zoom, add="+")

        # 右侧：数据统计和导出
        right_frame = tk.Frame(self.data_paned, bg='#f9f9f9')
        self.data_paned.add(right_frame, weight=1)

        tk.Label(right_frame, text="数据统计", font=('微软雅黑', 12, 'bold'),
                 bg='#f9f9f9').pack(anchor=tk.W, padx=10, pady=5)

        # 统计信息文本框
        self.stats_text = scrolledtext.ScrolledText(right_frame, width=30, height=12,
                                                    font=('Consolas', 10))
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 导出按钮区域
        export_frame = tk.Frame(right_frame, bg='#f9f9f9')
        export_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(export_frame, text="数据导出", font=('微软雅黑', 12, 'bold'),
                 bg='#f9f9f9').pack(anchor=tk.W)

        # 导出按钮
        button_frame = tk.Frame(export_frame, bg='#f9f9f9')
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(button_frame, text="导出历史数据",
                   command=self.export_original_data).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="清空数据",
                   command=self.clear_data).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="数据诊断",
                   command=self.data_diagnosis).pack(side=tk.LEFT, padx=2)

    def create_analysis_tab(self, notebook):
        """创建模型分析标签页"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="📈 模型分析")

        # 分析图表区域
        analysis_frame = tk.Frame(tab)
        analysis_frame.pack(fill=tk.BOTH, expand=True)

        self.analysis_container = analysis_frame
        self.analysis_fig = None
        self.analysis_axs = None
        self.analysis_canvas = None
        self.analysis_placeholder = tk.Label(analysis_frame, text="图表将在分析后生成", fg="#666")
        self.analysis_placeholder.pack(fill=tk.BOTH, expand=True)

        # 模型配置框架
        config_frame = tk.Frame(tab, bg='#f9f9f9')
        config_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(config_frame, text="模型配置", font=('微软雅黑', 12, 'bold'),
                 bg='#f9f9f9').pack(anchor=tk.W)

        # 节假日效应开关
        self.holiday_var = tk.BooleanVar(value=bool(self.holiday_cfg.get("enabled", True)))
        ttk.Checkbutton(config_frame, text="启用节假日效应",
                        variable=self.holiday_var).pack(anchor=tk.W, pady=2)

        # 权重配置（精选集合：Holt-Winters / SARIMA）
        weight_frame = tk.Frame(config_frame, bg=T_COLORS["bg_card"])
        weight_frame.pack(fill=tk.X, pady=5)

        tk.Label(weight_frame, text="融合权重:", bg=T_COLORS["bg_card"]).pack(side=tk.LEFT, padx=5)

        tk.Label(weight_frame, text="HW:", bg=T_COLORS["bg_card"]).pack(side=tk.LEFT, padx=5)
        weights = self.model_cfg.get("weights", {}) if isinstance(self.model_cfg.get("weights", {}), dict) else {}
        self.hw_weight_var = tk.DoubleVar(value=float(weights.get("hw", 0.5)))
        ttk.Spinbox(weight_frame, from_=0.0, to=1.0, increment=0.05,
                    textvariable=self.hw_weight_var, width=5).pack(side=tk.LEFT, padx=2)

        tk.Label(weight_frame, text="SARIMA:", bg=T_COLORS["bg_card"]).pack(side=tk.LEFT, padx=5)
        self.sarima_weight_var = tk.DoubleVar(value=float(weights.get("sarima", 0.5)))
        ttk.Spinbox(weight_frame, from_=0.0, to=1.0, increment=0.05,
                    textvariable=self.sarima_weight_var, width=5).pack(side=tk.LEFT, padx=2)

        tk.Label(weight_frame, text="(权重自动归一化，回测可推荐)", bg=T_COLORS["bg_card"],
                 fg=T_COLORS["text_sub"]).pack(side=tk.LEFT, padx=8)

        advanced_frame = tk.Frame(config_frame, bg=T_COLORS["bg_card"])
        advanced_frame.pack(fill=tk.X, pady=5)

        weight_mode = self.model_cfg.get("weight_mode", "auto")
        self.weight_mode_var = tk.StringVar(value=weight_mode if weight_mode in ["manual", "auto"] else "auto")
        ttk.Radiobutton(advanced_frame, text="手动权重", variable=self.weight_mode_var, value="manual").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(advanced_frame, text="自动权重(回测)", variable=self.weight_mode_var, value="auto").pack(side=tk.LEFT, padx=5)

        # 预测引擎：干预集成(默认, 节假日/COVID 入 exog, 无后处理) / 传统管线
        engine = self.model_cfg.get("engine", "intervention")
        self.engine_var = tk.StringVar(value=engine if engine in ["intervention", "legacy"] else "intervention")
        ttk.Label(advanced_frame, text="引擎:", background=T_COLORS["bg_card"]).pack(side=tk.LEFT, padx=(12, 2))
        ttk.Radiobutton(advanced_frame, text="干预集成", variable=self.engine_var, value="intervention").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(advanced_frame, text="传统管线", variable=self.engine_var, value="legacy").pack(side=tk.LEFT, padx=2)

        sarima_cfg = self.model_cfg.get("sarima", {}) if isinstance(self.model_cfg.get("sarima", {}), dict) else {}
        self.sarima_auto_var = tk.BooleanVar(value=bool(sarima_cfg.get("auto_tune", False)))
        ttk.Checkbutton(advanced_frame, text="SARIMA自动调参", variable=self.sarima_auto_var).pack(side=tk.LEFT, padx=10)

        hw_cfg = self.model_cfg.get("holt_winters", {}) if isinstance(self.model_cfg.get("holt_winters", {}), dict) else {}
        self.hw_auto_var = tk.BooleanVar(value=bool(hw_cfg.get("auto_tune", False)))
        ttk.Checkbutton(advanced_frame, text="HW自动调参", variable=self.hw_auto_var).pack(side=tk.LEFT, padx=10)

        ttk.Button(advanced_frame, text="模型回测评估", style="Secondary.TButton",
                   command=self.run_backtest).pack(side=tk.RIGHT, padx=5)
        ttk.Button(advanced_frame, text="状态转移分析", style="Secondary.TButton",
                   command=self.open_regime_analysis).pack(side=tk.RIGHT, padx=5)

    def create_forecast_tab(self, notebook):
        """创建预测结果标签页"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="📋 预测结果")

        top_bar = tk.Frame(tab, bg="#f0f0f0")
        top_bar.pack(fill=tk.X, padx=10, pady=(10, 6))

        tk.Label(top_bar, text="视图模式", bg="#f0f0f0").pack(side=tk.LEFT, padx=(0, 6))
        self.view_mode_combo = ttk.Combobox(top_bar, textvariable=self.view_mode_var, values=["紧凑", "舒适", "宽松"], width=8, state="readonly")
        self.view_mode_combo.pack(side=tk.LEFT)
        self.view_mode_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_ui_settings(), add="+")

        tk.Label(top_bar, text="显示比例", bg="#f0f0f0").pack(side=tk.LEFT, padx=(16, 6))
        self.zoom_scale = ttk.Scale(
            top_bar,
            from_=0.8,
            to=1.5,
            orient=tk.HORIZONTAL,
            length=220,
            variable=self.ui_scale_var,
            command=self._on_ui_scale_change,
            style="Forecast.Horizontal.TScale",
        )
        self.zoom_scale.pack(side=tk.LEFT)
        self.forecast_zoom_value_label = tk.Label(top_bar, text="100%", bg="#f0f0f0", width=5, anchor="w")
        self.forecast_zoom_value_label.pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(top_bar, text="重置", command=self._reset_scale).pack(side=tk.LEFT, padx=(10, 0))
        tk.Label(top_bar, text="Ctrl+滚轮缩放", bg="#f0f0f0", fg="#666").pack(side=tk.RIGHT)

        # 主内容区域 (使用 PanedWindow 实现等比例同步缩放)
        self.forecast_paned = ttk.PanedWindow(tab, orient=tk.HORIZONTAL)
        self.forecast_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        left_frame = tk.Frame(self.forecast_paned)
        self.forecast_paned.add(left_frame, weight=1)

        header = tk.Frame(left_frame)
        header.pack(fill=tk.X, pady=(0, 6))
        tk.Label(header, text="预测结果", font=('微软雅黑', 12, 'bold')).pack(side=tk.LEFT, anchor=tk.W)
        tk.Label(header, text="单位：与导入数据口径一致", fg="#666").pack(side=tk.LEFT, padx=(10, 0))

        columns = ('年份', '月份', '旅客运输量', '春运天数', '增长率')
        table_frame = tk.Frame(left_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        self.forecast_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15, style="Forecast.Treeview")
        for col in columns:
            self.forecast_tree.heading(col, text=col)

        # 初始列宽（会在 _apply_ui_settings 中被 scale 调整）
        self.forecast_tree.column("年份", width=90, anchor=tk.CENTER, stretch=False)
        self.forecast_tree.column("月份", width=80, anchor=tk.CENTER, stretch=False)
        self.forecast_tree.column("旅客运输量", width=180, anchor=tk.E, stretch=True)
        self.forecast_tree.column("春运天数", width=100, anchor=tk.CENTER, stretch=False)
        self.forecast_tree.column("增长率", width=110, anchor=tk.E, stretch=False)

        v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.forecast_tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.forecast_tree.xview)
        self.forecast_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.forecast_tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.forecast_tree.tag_configure("odd", background=T_COLORS["row_alt"])
        self.forecast_tree.tag_configure("spring", background=T_COLORS["row_spring"])
        self.forecast_tree.tag_configure("pos", foreground=T_COLORS["success"])
        self.forecast_tree.tag_configure("neg", foreground=T_COLORS["danger"])

        self.forecast_tooltip = TreeviewTooltip(self.forecast_tree, self._forecast_tooltip_text)
        self.forecast_tree.bind("<Control-MouseWheel>", self._on_ctrl_mousewheel_zoom, add="+")
        self._bind_drag_scroll(self.forecast_tree)

        right_frame = tk.Frame(self.forecast_paned)
        self.forecast_paned.add(right_frame, weight=1)

        tk.Label(right_frame, text="预测可视化", font=('微软雅黑', 12, 'bold')).pack(anchor=tk.W, pady=(0, 6))

        self.forecast_container = right_frame
        self.forecast_fig = None
        self.forecast_ax = None
        self.forecast_canvas = None
        self.forecast_placeholder = tk.Label(right_frame, text="图表将在预测后生成", fg="#666")
        self.forecast_placeholder.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 导出按钮区域
        export_frame = tk.Frame(right_frame, bg='#f9f9f9')
        export_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(export_frame, text="预测结果导出", font=('微软雅黑', 12, 'bold'),
                 bg='#f9f9f9').pack(anchor=tk.W)

        # 导出按钮
        button_frame = tk.Frame(export_frame, bg='#f9f9f9')
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(button_frame, text="📥 导出预测结果",
                   command=self.export_forecast_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📊 导出增长分析",
                   command=self.export_growth_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📋 导出完整报告",
                   command=self.export_full_report).pack(side=tk.LEFT, padx=5)

    def ensure_analysis_canvas(self):
        if getattr(self, "analysis_canvas", None) is not None:
            return
        self.analysis_fig, self.analysis_axs = plt.subplots(2, 2, figsize=(10, 8))
        self.analysis_canvas = FigureCanvasTkAgg(self.analysis_fig, self.analysis_container)
        self.analysis_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        if getattr(self, "analysis_placeholder", None) is not None:
            self.analysis_placeholder.destroy()
            self.analysis_placeholder = None

    def ensure_forecast_canvas(self):
        if getattr(self, "forecast_canvas", None) is not None:
            return
        self.forecast_fig, self.forecast_ax = plt.subplots(figsize=(8, 5))
        self.forecast_canvas = FigureCanvasTkAgg(self.forecast_fig, self.forecast_container)
        self.forecast_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        if getattr(self, "forecast_placeholder", None) is not None:
            self.forecast_placeholder.destroy()
            self.forecast_placeholder = None

    def create_config_tab(self, notebook):
        """创建配置参数标签页"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="⚙️ 配置参数")

        # 配置面板
        config_frame = tk.Frame(tab, bg='#f9f9f9')
        config_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(config_frame, text="系统配置参数",
                 font=('微软雅黑', 14, 'bold'), bg='#f9f9f9').pack(pady=(0, 20))

        profile_frame = tk.Frame(config_frame, bg="#f9f9f9")
        profile_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(profile_frame, text="配置方案:", bg="#f9f9f9", width=10, anchor="w").pack(side=tk.LEFT)
        profile_names = sorted(list(self.config.get("profiles", {}).keys())) if isinstance(self.config.get("profiles", {}), dict) else ["default"]
        self.profile_var = tk.StringVar(value=self.active_profile_name if self.active_profile_name in profile_names else (profile_names[0] if profile_names else "default"))
        self.profile_combo = ttk.Combobox(profile_frame, textvariable=self.profile_var, values=profile_names, width=20, state="readonly")
        self.profile_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(profile_frame, text="加载", command=self.load_profile_from_ui).pack(side=tk.LEFT, padx=5)
        ttk.Button(profile_frame, text="另存为", command=self.save_profile_as).pack(side=tk.LEFT, padx=5)
        ttk.Button(profile_frame, text="删除", command=self.delete_profile_from_ui).pack(side=tk.LEFT, padx=5)
        ttk.Button(profile_frame, text="重新加载配置文件", command=self.reload_config_file).pack(side=tk.RIGHT, padx=5)

        config_items = [
            ("春运效应系数:", "spring_festival_effect", float(self.lunar_config.get("spring_festival_effect", 1.15))),
            ("暑假效应系数:", "summer_vacation_effect", float(self.lunar_config.get("summer_vacation_effect", 1.10))),
            ("五一效应系数:", "may_day_effect", float(self.lunar_config.get("may_day_effect", 1.05))),
            ("十一效应系数:", "national_day_effect", float(self.lunar_config.get("national_day_effect", 1.08))),
            ("冬季高峰效应:", "winter_peak_effect", float(self.lunar_config.get("winter_peak_effect", 1.03))),
            ("年度环比增长率:", "annual_growth_rate", float(self.lunar_config.get("annual_growth_rate", 0.027))),
        ]

        self.config_vars = {}

        for i, (label_text, var_name, default_value) in enumerate(config_items):
            frame = tk.Frame(config_frame, bg='#f9f9f9')
            frame.pack(fill=tk.X, pady=5)

            tk.Label(frame, text=label_text, bg='#f9f9f9', width=15, anchor='w').pack(side=tk.LEFT)

            if var_name == 'annual_growth_rate':
                # 增长率使用百分比输入
                var = tk.DoubleVar(value=default_value * 100)
                self.config_vars[var_name] = var
                spinbox = ttk.Spinbox(frame, from_=0.0, to=20.0, increment=0.1,
                                      textvariable=var, width=8)
                spinbox.pack(side=tk.LEFT, padx=10)
                tk.Label(frame, text="%", bg='#f9f9f9').pack(side=tk.LEFT)
            else:
                var = tk.DoubleVar(value=default_value)
                self.config_vars[var_name] = var
                spinbox = ttk.Spinbox(frame, from_=0.8, to=1.5, increment=0.01,
                                      textvariable=var, width=8)
                spinbox.pack(side=tk.LEFT, padx=10)

        spring_frame = tk.LabelFrame(config_frame, text="春运时间设置", bg="#f9f9f9")
        spring_frame.pack(fill=tk.X, pady=10)

        self.spring_before_var = tk.IntVar(value=int(self.holiday_cfg.get("spring_travel_before_days", 15)))
        self.spring_after_var = tk.IntVar(value=int(self.holiday_cfg.get("spring_travel_after_days", 24)))

        row1 = tk.Frame(spring_frame, bg="#f9f9f9")
        row1.pack(fill=tk.X, pady=5)
        tk.Label(row1, text="春节前天数:", bg="#f9f9f9", width=12, anchor="w").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Spinbox(row1, from_=0, to=30, increment=1, textvariable=self.spring_before_var, width=6).pack(side=tk.LEFT, padx=5)
        tk.Label(row1, text="春节后天数:", bg="#f9f9f9", width=12, anchor="w").pack(side=tk.LEFT, padx=(20, 0))
        ttk.Spinbox(row1, from_=0, to=60, increment=1, textvariable=self.spring_after_var, width=6).pack(side=tk.LEFT, padx=5)
        ttk.Button(row1, text="春运可视化预览", command=self.open_spring_travel_preview).pack(side=tk.RIGHT, padx=10)

        months = self.holiday_cfg.get("spring_travel_months", [1, 2, 3])
        if not isinstance(months, list):
            months = [1, 2, 3]
        months = [int(m) for m in months]
        self.spring_month_vars = {m: tk.BooleanVar(value=(m in months)) for m in [12, 1, 2, 3]}

        row2 = tk.Frame(spring_frame, bg="#f9f9f9")
        row2.pack(fill=tk.X, pady=5)
        tk.Label(row2, text="春运影响月份:", bg="#f9f9f9", width=12, anchor="w").pack(side=tk.LEFT, padx=(10, 0))
        for m in [12, 1, 2, 3]:
            ttk.Checkbutton(row2, text=f"{m}月", variable=self.spring_month_vars[m]).pack(side=tk.LEFT, padx=5)

        row3 = tk.Frame(spring_frame, bg="#f9f9f9")
        row3.pack(fill=tk.X, pady=5)
        tk.Label(row3, text="春运测试年份:", bg="#f9f9f9", width=12, anchor="w").pack(side=tk.LEFT, padx=(10, 0))
        self.spring_test_year_var = tk.IntVar(value=2026)
        ttk.Spinbox(row3, from_=2000, to=2100, increment=1, textvariable=self.spring_test_year_var, width=8).pack(side=tk.LEFT, padx=5)

        # 按钮区域
        button_frame = tk.Frame(config_frame, bg='#f9f9f9')
        button_frame.pack(fill=tk.X, pady=20)

        ttk.Button(button_frame, text="保存配置",
                   command=self.save_config).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="重置默认",
                   command=self.reset_config).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="测试春运计算",
                   command=self.test_spring_festival).pack(side=tk.LEFT, padx=10)

        # 说明区域
        info_frame = tk.Frame(config_frame, bg='#f9f9f9')
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        info_text = scrolledtext.ScrolledText(info_frame, width=40, height=10,
                                              font=('微软雅黑', 10))
        info_text.pack(fill=tk.BOTH, expand=True)

        before_days = int(self.holiday_cfg.get("spring_travel_before_days", 15))
        after_days = int(self.holiday_cfg.get("spring_travel_after_days", 24))
        total_days = before_days + after_days + 1
        growth_pct = float(self.growth_cfg.get("annual_growth_rate", 0.027)) * 100
        config_info = f"""
        系统配置说明：

        1. 春运效应计算：
           - 春运时间窗口：春节前{before_days}天到春节后{after_days}天（合计{total_days}天）
           - 效应按实际影响天数比例分配到各月份
           - 公式：效应 = 1 + (春运天数/月份天数) × (基础效应-1)

        2. 年度增长率：
           - 每年总旅客运输量环比增长{growth_pct:.2f}%
           - 计算公式：当年总量 = 上年总量 × (1 + {growth_pct:.2f}%)
           - 增长率按月均分配，确保年度总增长率达标

        3. 假日效应：
           - 固定假日：五一、十一、暑假
           - 季节性效应：冬季运输高峰
           - 春运效应：基于春节日期动态计算

        4. 精选算法融合：
           - Holt-Winters：季节性指数平滑
           - SARIMA/SARIMAX：时间序列分析（可接入 GDP/ASK 外生因子）
           - 融合模型：加权平均优化结果（线性回归已移除，详见算法手册）
        """

        info_text.insert(1.0, config_info)
        info_text.configure(state='disabled')

    def load_sample_data(self):
        """加载示例数据"""
        sample_data = [
            (2024, 10, 243533),
            (2024, 11, 178537),
            (2024, 12, 187840),
            (2025, 1, 240783),
            (2025, 2, 251444),
            (2025, 3, 234029),
            (2025, 4, 236668),
            (2025, 5, 241408),
            (2025, 6, 215072),
            (2025, 7, 293708),
            (2025, 8, 309236),
            (2025, 9, 228916)
        ]

        # 清空表格
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        # 添加数据到表格
        for i, data in enumerate(sample_data):
            year, month, val = data
            tag = "odd" if i % 2 == 1 else ""
            formatted_val = f"{val:,}"
            self.history_tree.insert('', 'end', values=(year, month, formatted_val), tags=(tag,))

        # 保存到DataFrame
        self.data = pd.DataFrame(sample_data, columns=['年份', '月份', '旅客运输量'])

        # 更新统计信息
        self.update_stats()

        self.update_status("示例数据已加载")

    def update_stats(self):
        """更新统计信息"""
        if self.data is not None:
            stats_text = f"数据统计信息:\n"
            stats_text += f"数据量: {len(self.data)} 条\n"
            stats_text += f"时间范围: {self.data['年份'].min()}年{self.data['月份'].min()}月 - "
            stats_text += f"{self.data['年份'].max()}年{self.data['月份'].max()}月\n\n"

            stats_text += "月度统计:\n"
            monthly_stats = self.data.groupby('月份')['旅客运输量'].agg(['mean', 'std', 'min', 'max'])
            for month in range(1, 13):
                if month in monthly_stats.index:
                    stats_text += f"{month:2d}月: {monthly_stats.loc[month, 'mean']:.0f} ± {monthly_stats.loc[month, 'std']:.0f}\n"

            stats_text += f"\n总体统计:\n"
            stats_text += f"平均值: {self.data['旅客运输量'].mean():.0f}\n"
            stats_text += f"标准差: {self.data['旅客运输量'].std():.0f}\n"
            stats_text += f"最小值: {self.data['旅客运输量'].min():.0f}\n"
            stats_text += f"最大值: {self.data['旅客运输量'].max():.0f}\n"
            stats_text += f"中位数: {self.data['旅客运输量'].median():.0f}\n"

            # 计算年度增长率（如果数据完整）
            if len(self.data) >= 12:
                yearly_data = self.data.groupby('年份')['旅客运输量'].sum()
                if len(yearly_data) >= 2:
                    growth_rates = []
                    for i in range(1, len(yearly_data)):
                        growth = (yearly_data.iloc[i] - yearly_data.iloc[i - 1]) / yearly_data.iloc[i - 1] * 100
                        growth_rates.append(growth)

                    if growth_rates:
                        stats_text += f"\n年度增长率分析:\n"
                        stats_text += f"平均年度增长率: {np.mean(growth_rates):.2f}%\n"
                        stats_text += f"目标增长率: {self.lunar_config['annual_growth_rate'] * 100:.2f}%\n"

            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text)

    def import_data(self):
        """导入Excel数据"""
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                # 读取Excel文件
                df = pd.read_excel(file_path)

                # 清空表格
                for item in self.history_tree.get_children():
                    self.history_tree.delete(item)

                # 添加数据到表格
                for i, (idx, row) in enumerate(df.iterrows()):
                    # 尝试不同的列名
                    if '年份' in df.columns and '月份' in df.columns and '旅客运输量' in df.columns:
                        year = int(row['年份'])
                        month = int(row['月份'])
                        value = int(row['旅客运输量'])
                    elif len(df.columns) >= 3:
                        year = int(row.iloc[0])
                        month = int(row.iloc[1])
                        value = int(row.iloc[2])
                    else:
                        raise ValueError("Excel文件格式不正确")

                    tag = "odd" if i % 2 == 1 else ""
                    formatted_val = f"{value:,}"
                    self.history_tree.insert('', 'end', values=(year, month, formatted_val), tags=(tag,))

                # 保存数据
                self.data = df.iloc[:, :3].copy()
                if len(self.data.columns) == 3:
                    self.data.columns = ['年份', '月份', '旅客运输量']

                # 更新统计信息
                self.update_stats()

                self.update_status(f"数据导入成功: {os.path.basename(file_path)}")
                messagebox.showinfo("成功", f"成功导入 {len(df)} 条数据")

            except Exception as e:
                logging.exception("导入失败")
                messagebox.showerror("错误", f"导入失败: {str(e)}")

    def manual_input(self):
        """手动录入数据窗口"""
        input_window = tk.Toplevel(self.root)
        input_window.title("手动录入数据")
        input_window.geometry("400x300")

        tk.Label(input_window, text="录入新数据", font=('微软雅黑', 14, 'bold')).pack(pady=10)

        # 输入框架
        input_frame = tk.Frame(input_window)
        input_frame.pack(pady=10)

        entries = {}
        labels = ['年份', '月份', '旅客运输量']

        for i, label in enumerate(labels):
            tk.Label(input_frame, text=label + ":").grid(row=i, column=0, padx=5, pady=5, sticky='e')
            entry = tk.Entry(input_frame, width=20)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entries[label] = entry

        def save_data():
            try:
                year = int(entries['年份'].get())
                month = int(entries['月份'].get())
                value = int(entries['旅客运输量'].get())

                # 验证数据
                if month < 1 or month > 12:
                    raise ValueError("月份必须在1-12之间")
                if value <= 0:
                    raise ValueError("旅客运输量必须为正数")

                # 添加到表格
                count = len(self.history_tree.get_children())
                tag = "odd" if count % 2 == 1 else ""
                formatted_val = f"{value:,}"
                self.history_tree.insert('', 'end', values=(year, month, formatted_val), tags=(tag,))

                # 更新数据
                new_row = pd.DataFrame([[year, month, value]],
                                       columns=['年份', '月份', '旅客运输量'])
                if self.data is None:
                    self.data = new_row
                else:
                    self.data = pd.concat([self.data, new_row], ignore_index=True)

                # 更新统计信息
                self.update_stats()

                input_window.destroy()
                self.update_status("数据录入成功")

            except ValueError as e:
                messagebox.showerror("错误", f"输入错误: {str(e)}")

        # 按钮
        button_frame = tk.Frame(input_window)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="保存", command=save_data).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=input_window.destroy).pack(side=tk.LEFT, padx=10)

    def save_config(self):
        """保存配置"""
        try:
            if hasattr(self, "profile_var"):
                self.active_profile_name = str(self.profile_var.get())

            self.holiday_cfg["enabled"] = bool(self.holiday_var.get()) if hasattr(self, "holiday_var") else bool(self.holiday_cfg.get("enabled", True))
            self.holiday_cfg["spring_festival_effect"] = float(self.config_vars["spring_festival_effect"].get())
            self.holiday_cfg["summer_vacation_effect"] = float(self.config_vars["summer_vacation_effect"].get())
            self.holiday_cfg["may_day_effect"] = float(self.config_vars["may_day_effect"].get())
            self.holiday_cfg["national_day_effect"] = float(self.config_vars["national_day_effect"].get())
            self.holiday_cfg["winter_peak_effect"] = float(self.config_vars["winter_peak_effect"].get())

            if hasattr(self, "spring_before_var"):
                self.holiday_cfg["spring_travel_before_days"] = int(self.spring_before_var.get())
            if hasattr(self, "spring_after_var"):
                self.holiday_cfg["spring_travel_after_days"] = int(self.spring_after_var.get())
            if hasattr(self, "spring_month_vars"):
                self.holiday_cfg["spring_travel_months"] = [m for m, v in self.spring_month_vars.items() if bool(v.get())]

            growth_rate = float(self.config_vars["annual_growth_rate"].get()) / 100.0
            self.growth_cfg["annual_growth_rate"] = growth_rate

            if hasattr(self, "hw_weight_var"):
                self.model_cfg.setdefault("weights", {})
                self.model_cfg["weights"]["hw"] = float(self.hw_weight_var.get())
                self.model_cfg["weights"]["sarima"] = float(self.sarima_weight_var.get())
                self.model_cfg["weights"].pop("linear", None)

            if hasattr(self, "weight_mode_var"):
                self.model_cfg["weight_mode"] = str(self.weight_mode_var.get())
            if hasattr(self, "engine_var"):
                self.model_cfg["engine"] = str(self.engine_var.get())
            if hasattr(self, "sarima_auto_var"):
                self.model_cfg.setdefault("sarima", {})
                self.model_cfg["sarima"]["auto_tune"] = bool(self.sarima_auto_var.get())
            if hasattr(self, "hw_auto_var"):
                self.model_cfg.setdefault("holt_winters", {})
                self.model_cfg["holt_winters"]["auto_tune"] = bool(self.hw_auto_var.get())

            self.profile["holiday"] = self.holiday_cfg
            self.profile["growth"] = self.growth_cfg
            self.profile["model"] = self.model_cfg
            self.profile["spring_festival_dates"] = self.spring_festival_dates

            self.lunar_config["spring_festival_effect"] = float(self.holiday_cfg.get("spring_festival_effect", self.lunar_config["spring_festival_effect"]))
            self.lunar_config["summer_vacation_effect"] = float(self.holiday_cfg.get("summer_vacation_effect", self.lunar_config["summer_vacation_effect"]))
            self.lunar_config["may_day_effect"] = float(self.holiday_cfg.get("may_day_effect", self.lunar_config["may_day_effect"]))
            self.lunar_config["national_day_effect"] = float(self.holiday_cfg.get("national_day_effect", self.lunar_config["national_day_effect"]))
            self.lunar_config["winter_peak_effect"] = float(self.holiday_cfg.get("winter_peak_effect", self.lunar_config["winter_peak_effect"]))
            self.lunar_config["annual_growth_rate"] = float(self.growth_cfg.get("annual_growth_rate", self.lunar_config["annual_growth_rate"]))
            self.lunar_config["spring_travel_before_days"] = int(self.holiday_cfg.get("spring_travel_before_days", self.lunar_config.get("spring_travel_before_days", 15)))
            self.lunar_config["spring_travel_after_days"] = int(self.holiday_cfg.get("spring_travel_after_days", self.lunar_config.get("spring_travel_after_days", 24)))

            self.config_store.upsert_profile(self.active_profile_name, self.profile)
            self.config_store.set_active_profile(self.active_profile_name)
            ok, info = self.config_store.save(self.config_store.load())
            if ok:
                messagebox.showinfo("成功", "配置参数已保存")
            else:
                messagebox.showerror("错误", f"保存配置失败: {info}")

        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")

    def reset_config(self):
        """重置配置"""
        self.config_vars["spring_festival_effect"].set(1.15)
        self.config_vars["summer_vacation_effect"].set(1.10)
        self.config_vars["may_day_effect"].set(1.05)
        self.config_vars["national_day_effect"].set(1.08)
        self.config_vars["winter_peak_effect"].set(1.03)
        self.config_vars["annual_growth_rate"].set(2.7)
        if hasattr(self, "spring_before_var"):
            self.spring_before_var.set(15)
        if hasattr(self, "spring_after_var"):
            self.spring_after_var.set(24)
        if hasattr(self, "spring_month_vars"):
            for m, v in self.spring_month_vars.items():
                v.set(m in [1, 2, 3])

        messagebox.showinfo("成功", "配置参数已重置为默认值")

    def reload_config_file(self):
        try:
            self.config_store.cache = None
            self.config = self.config_store.load()
            self.active_profile_name = self.config.get("active_profile", "default")
            self.profile = self.config_store.get_active_profile()
            self.apply_profile_to_ui(self.profile)
            messagebox.showinfo("成功", "配置文件已重新加载")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def load_profile_from_ui(self):
        try:
            name = str(self.profile_var.get()) if hasattr(self, "profile_var") else self.active_profile_name
            self.config_store.set_active_profile(name)
            self.config = self.config_store.load()
            profiles = self.config.get("profiles", {})
            if not isinstance(profiles, dict) or name not in profiles:
                messagebox.showerror("错误", "配置方案不存在")
                return
            self.active_profile_name = name
            self.profile = dict(profiles[name])
            self.apply_profile_to_ui(self.profile)
            messagebox.showinfo("成功", f"已加载配置方案：{name}")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def save_profile_as(self):
        name = simpledialog.askstring("另存为", "请输入新的配置方案名称：", parent=self.root)
        if not name:
            return
        name = str(name).strip()
        if not name:
            return
        try:
            profile = self.collect_profile_from_ui()
            self.config_store.upsert_profile(name, profile)
            self.config_store.set_active_profile(name)
            ok, info = self.config_store.save(self.config_store.load())
            if not ok:
                messagebox.showerror("错误", f"保存失败: {info}")
                return

            self.config = self.config_store.load()
            self.active_profile_name = name
            if hasattr(self, "profile_combo"):
                profile_names = sorted(list(self.config.get("profiles", {}).keys()))
                self.profile_combo.configure(values=profile_names)
                self.profile_var.set(name)
            messagebox.showinfo("成功", f"已保存为配置方案：{name}")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def delete_profile_from_ui(self):
        try:
            name = str(self.profile_var.get()) if hasattr(self, "profile_var") else self.active_profile_name
            if not messagebox.askyesno("确认", f"确定要删除配置方案“{name}”吗？"):
                return
            ok = self.config_store.delete_profile(name)
            if not ok:
                messagebox.showerror("错误", "删除失败（可能只剩最后一个方案）")
                return
            ok2, info = self.config_store.save(self.config_store.load())
            if not ok2:
                messagebox.showerror("错误", f"保存失败: {info}")
                return
            self.config = self.config_store.load()
            self.active_profile_name = self.config.get("active_profile", "default")
            self.profile = self.config_store.get_active_profile()
            if hasattr(self, "profile_combo"):
                profile_names = sorted(list(self.config.get("profiles", {}).keys()))
                self.profile_combo.configure(values=profile_names)
                self.profile_var.set(self.active_profile_name)
            self.apply_profile_to_ui(self.profile)
            messagebox.showinfo("成功", "配置方案已删除")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def collect_profile_from_ui(self):
        holiday_cfg = dict(self.holiday_cfg)
        growth_cfg = dict(self.growth_cfg)
        model_cfg = dict(self.model_cfg)

        holiday_cfg["enabled"] = bool(self.holiday_var.get()) if hasattr(self, "holiday_var") else bool(holiday_cfg.get("enabled", True))
        holiday_cfg["spring_festival_effect"] = float(self.config_vars["spring_festival_effect"].get())
        holiday_cfg["summer_vacation_effect"] = float(self.config_vars["summer_vacation_effect"].get())
        holiday_cfg["may_day_effect"] = float(self.config_vars["may_day_effect"].get())
        holiday_cfg["national_day_effect"] = float(self.config_vars["national_day_effect"].get())
        holiday_cfg["winter_peak_effect"] = float(self.config_vars["winter_peak_effect"].get())

        holiday_cfg["spring_travel_before_days"] = int(self.spring_before_var.get()) if hasattr(self, "spring_before_var") else int(holiday_cfg.get("spring_travel_before_days", 15))
        holiday_cfg["spring_travel_after_days"] = int(self.spring_after_var.get()) if hasattr(self, "spring_after_var") else int(holiday_cfg.get("spring_travel_after_days", 24))
        holiday_cfg["spring_travel_months"] = [m for m, v in self.spring_month_vars.items() if bool(v.get())] if hasattr(self, "spring_month_vars") else holiday_cfg.get("spring_travel_months", [1, 2, 3])

        growth_cfg["annual_growth_rate"] = float(self.config_vars["annual_growth_rate"].get()) / 100.0

        if hasattr(self, "weight_mode_var"):
            model_cfg["weight_mode"] = str(self.weight_mode_var.get())
        if hasattr(self, "engine_var"):
            model_cfg["engine"] = str(self.engine_var.get())
        model_cfg.setdefault("weights", {})
        if hasattr(self, "hw_weight_var"):
            model_cfg["weights"]["hw"] = float(self.hw_weight_var.get())
            model_cfg["weights"]["sarima"] = float(self.sarima_weight_var.get())
            model_cfg["weights"].pop("linear", None)

        model_cfg.setdefault("sarima", {})
        if hasattr(self, "sarima_auto_var"):
            model_cfg["sarima"]["auto_tune"] = bool(self.sarima_auto_var.get())
        model_cfg.setdefault("holt_winters", {})
        if hasattr(self, "hw_auto_var"):
            model_cfg["holt_winters"]["auto_tune"] = bool(self.hw_auto_var.get())

        return {
            "holiday": holiday_cfg,
            "growth": growth_cfg,
            "model": model_cfg,
            "spring_festival_dates": dict(self.spring_festival_dates),
        }

    def apply_profile_to_ui(self, profile):
        self.profile = dict(profile) if isinstance(profile, dict) else {}
        self.holiday_cfg = dict(self.profile.get("holiday", {}))
        self.growth_cfg = dict(self.profile.get("growth", {}))
        self.model_cfg = dict(self.profile.get("model", {}))
        self.spring_festival_dates = dict(self.profile.get("spring_festival_dates", {}))

        if hasattr(self, "holiday_var"):
            self.holiday_var.set(bool(self.holiday_cfg.get("enabled", True)))

        if hasattr(self, "config_vars"):
            if "spring_festival_effect" in self.config_vars:
                self.config_vars["spring_festival_effect"].set(float(self.holiday_cfg.get("spring_festival_effect", 1.15)))
            if "summer_vacation_effect" in self.config_vars:
                self.config_vars["summer_vacation_effect"].set(float(self.holiday_cfg.get("summer_vacation_effect", 1.10)))
            if "may_day_effect" in self.config_vars:
                self.config_vars["may_day_effect"].set(float(self.holiday_cfg.get("may_day_effect", 1.05)))
            if "national_day_effect" in self.config_vars:
                self.config_vars["national_day_effect"].set(float(self.holiday_cfg.get("national_day_effect", 1.08)))
            if "winter_peak_effect" in self.config_vars:
                self.config_vars["winter_peak_effect"].set(float(self.holiday_cfg.get("winter_peak_effect", 1.03)))
            if "annual_growth_rate" in self.config_vars:
                self.config_vars["annual_growth_rate"].set(float(self.growth_cfg.get("annual_growth_rate", 0.027)) * 100)

        if hasattr(self, "spring_before_var"):
            self.spring_before_var.set(int(self.holiday_cfg.get("spring_travel_before_days", 15)))
        if hasattr(self, "spring_after_var"):
            self.spring_after_var.set(int(self.holiday_cfg.get("spring_travel_after_days", 24)))
        if hasattr(self, "spring_month_vars"):
            months = self.holiday_cfg.get("spring_travel_months", [1, 2, 3])
            if not isinstance(months, list):
                months = [1, 2, 3]
            months = set(int(m) for m in months)
            for m, v in self.spring_month_vars.items():
                v.set(m in months)

        weights = self.model_cfg.get("weights", {}) if isinstance(self.model_cfg.get("weights", {}), dict) else {}
        if hasattr(self, "hw_weight_var"):
            self.hw_weight_var.set(float(weights.get("hw", 0.5)))
            self.sarima_weight_var.set(float(weights.get("sarima", 0.5)))

        if hasattr(self, "weight_mode_var"):
            wm = self.model_cfg.get("weight_mode", "auto")
            self.weight_mode_var.set(wm if wm in ["manual", "auto"] else "auto")

        if hasattr(self, "engine_var"):
            eng = self.model_cfg.get("engine", "intervention")
            self.engine_var.set(eng if eng in ["intervention", "legacy"] else "intervention")

        if hasattr(self, "sarima_auto_var"):
            sarima_cfg = self.model_cfg.get("sarima", {}) if isinstance(self.model_cfg.get("sarima", {}), dict) else {}
            self.sarima_auto_var.set(bool(sarima_cfg.get("auto_tune", False)))
        if hasattr(self, "hw_auto_var"):
            hw_cfg = self.model_cfg.get("holt_winters", {}) if isinstance(self.model_cfg.get("holt_winters", {}), dict) else {}
            self.hw_auto_var.set(bool(hw_cfg.get("auto_tune", False)))

    def open_spring_travel_preview(self):
        try:
            year = int(self.spring_test_year_var.get()) if hasattr(self, "spring_test_year_var") else 2026
            before_days = int(self.spring_before_var.get()) if hasattr(self, "spring_before_var") else 15
            after_days = int(self.spring_after_var.get()) if hasattr(self, "spring_after_var") else 24
            start, end, sf = compute_spring_travel_span(year, self.spring_festival_dates, before_days, after_days)

            months = [m for m, v in self.spring_month_vars.items() if bool(v.get())] if hasattr(self, "spring_month_vars") else [1, 2, 3]
            months = sorted([int(m) for m in months])
            bars = []
            for m in months:
                bars.append((m, compute_month_spring_travel_days(year, m, self.spring_festival_dates, before_days, after_days)))

            win = tk.Toplevel(self.root)
            win.title("春运时间预览")
            win.geometry("900x500")

            top = tk.Frame(win)
            top.pack(fill=tk.X, padx=10, pady=10)
            tk.Label(top, text=f"{year}年 春运窗口预览", font=("微软雅黑", 12, "bold")).pack(anchor="w")
            tk.Label(top, text=f"春节：{sf.date.strftime('%Y-%m-%d')}（来源：{sf.source}）").pack(anchor="w")
            tk.Label(top, text=f"春运：{start.strftime('%Y-%m-%d')} ～ {end.strftime('%Y-%m-%d')}").pack(anchor="w")

            fig, ax = plt.subplots(figsize=(7.5, 3.5))
            x = [str(m) for m, _ in bars]
            y = [d for _, d in bars]
            ax.bar(x, y, color="#2E86C1", alpha=0.85)
            ax.set_xlabel("月份")
            ax.set_ylabel("春运天数")
            ax.set_title("各月春运天数分配")
            ax.grid(True, axis="y", alpha=0.3)

            canvas = FigureCanvasTkAgg(fig, master=win)
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            canvas.draw()
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def test_spring_festival(self):
        """测试春运计算"""
        try:
            year = int(self.spring_test_year_var.get()) if hasattr(self, "spring_test_year_var") else 2026
            before_days = int(self.spring_before_var.get()) if hasattr(self, "spring_before_var") else int(self.holiday_cfg.get("spring_travel_before_days", 15))
            after_days = int(self.spring_after_var.get()) if hasattr(self, "spring_after_var") else int(self.holiday_cfg.get("spring_travel_after_days", 24))
            start, end, sf = compute_spring_travel_span(year, self.spring_festival_dates, before_days, after_days)

            # 计算各月春运天数
            months_days = {}
            months = [m for m, v in self.spring_month_vars.items() if bool(v.get())] if hasattr(self, "spring_month_vars") else [1, 2, 3]
            months = sorted([int(m) for m in months])
            for month in months:
                days = compute_month_spring_travel_days(year, month, self.spring_festival_dates, before_days, after_days)
                if days > 0:
                    months_days[month] = days

            result = f"{year}年春运测试:\n"
            result += f"春节日期: {sf.date.strftime('%Y-%m-%d')} ({sf.source})\n"
            result += f"春运时间: {start.strftime('%m-%d')} 到 {end.strftime('%m-%d')}\n"
            result += "各月春运天数:\n"
            for month, days in months_days.items():
                result += f"  {month}月: {days}天\n"

            messagebox.showinfo("春运测试", result)

        except Exception as e:
            messagebox.showerror("错误", f"测试失败: {str(e)}")

    # ========== 核心计算函数 ==========

    def get_spring_festival_date(self, year: int) -> datetime:
        """获取春节日期"""
        return get_spring_festival_date(int(year), self.spring_festival_dates).date

    def calculate_spring_festival_days(self, year: int, month: int) -> int:
        """计算指定月份中的春运天数"""
        try:
            before_days = int(self.holiday_cfg.get("spring_travel_before_days", self.lunar_config.get("spring_travel_before_days", 15)))
            after_days = int(self.holiday_cfg.get("spring_travel_after_days", self.lunar_config.get("spring_travel_after_days", 24)))
            return compute_month_spring_travel_days(int(year), int(month), self.spring_festival_dates, before_days, after_days)
        except Exception:
            return 0

    def calculate_monthly_spring_festival_effect(self, year: int, month: int) -> float:
        """计算月份中的春运效应系数（按实际天数比例）"""
        # 春运可能影响的月份：1月、2月、3月，有时12月
        if month not in [1, 2, 3, 12]:
            return 1.0

        # 获取春运天数
        spring_days = self.calculate_spring_festival_days(year, month)
        if spring_days == 0:
            return 1.0

        # 月份总天数
        days_in_month = calendar.monthrange(year, month)[1]

        # 计算效应系数
        # 公式：1 + (春运天数/月份总天数) × (基础效应-1)
        base_effect = self.lunar_config['spring_festival_effect']
        effect = 1.0 + (spring_days / days_in_month) * (base_effect - 1.0)

        return effect

    def get_holiday_effect(self, year: int, month: int) -> float:
        """获取节假日效应系数"""
        temp_cfg = dict(self.holiday_cfg)
        if hasattr(self, "holiday_var"):
            temp_cfg["enabled"] = bool(self.holiday_var.get())
        return float(compute_holiday_effect(int(year), int(month), temp_cfg, self.spring_festival_dates))

    def apply_annual_growth_adjustment(self, forecast: pd.Series) -> pd.Series:
        annual_growth_rate = float(self.growth_cfg.get("annual_growth_rate", self.lunar_config.get("annual_growth_rate", 0.027)))
        historical_yearly_total = None
        if self.data is not None and len(self.data) > 0:
            last_year = int(self.data["年份"].max())
            last_year_data = self.data[self.data["年份"] == last_year]
            if len(last_year_data) == 12:
                historical_yearly_total = float(last_year_data["旅客运输量"].sum())
            elif len(last_year_data) > 0:
                historical_yearly_total = float(last_year_data["旅客运输量"].mean() * 12)
        adjusted, growth_rates = apply_annual_growth_adjustment(forecast, annual_growth_rate, historical_yearly_total)
        self.growth_rates = growth_rates
        return adjusted

    def prepare_time_series(self):
        """准备时间序列数据"""
        # 创建日期索引
        dates = []
        values = []

        for _, row in self.data.iterrows():
            year = int(row['年份'])
            month = int(row['月份'])

            try:
                date_obj = datetime(year, month, 1)
                date_str = date_obj.strftime('%Y-%m-%d')
                if date_str not in dates:
                    dates.append(date_str)
                    values.append(int(row['旅客运输量']))
            except Exception as e:
                print(f"创建日期错误: {e}")
                continue

        # 创建时间序列
        if dates:
            ts = pd.Series(values, index=pd.to_datetime(dates))
            ts = ts.sort_index()
            return ts
        else:
            raise ValueError("无法创建时间序列，日期数据无效")

    def run_forecast(self):
        """执行预测（自动推荐 / 手动选择双模式，支持外部因子）"""
        if self.data is None or len(self.data) < 12:
            messagebox.showwarning("警告", "至少需要12个月的历史数据才能进行预测")
            return

        try:
            self.update_status("正在计算预测...")

            # 准备时间序列
            ts = self.prepare_time_series()

            # 外部宏观/行业因子（管理控制台接入）
            factors = None
            if self.external_enabled:
                try:
                    factors = self.external_mgr.get_monthly_factors(ts.index, periods=12)
                except Exception:
                    factors = None

            # 模式：auto = 自动推荐（回测驱动）；manual = 手动选择
            mode = str(getattr(self, "model_mode_var", tk.StringVar(value="auto")).get() or "auto")
            model_type = str(self.model_var.get())
            rec_info = None

            if mode == "auto":
                try:
                    profile = self.collect_profile_from_ui() if hasattr(self, "collect_profile_from_ui") else dict(self.profile)
                    profile.setdefault("spring_festival_dates", dict(self.spring_festival_dates))
                    bt = rolling_backtest(ts, profile, horizon=12, step=12, min_train=24, factors=factors) if len(ts) >= 24 else {"error": "历史数据不足"}
                    if "error" not in bt:
                        rec = bt.get("recommendation") or {}
                        model_type = str(rec.get("model", "ensemble"))
                        weights = rec.get("weights") or recommend_weights_from_backtest(bt)
                        self.hw_weight_var.set(round(float(weights.get("hw", 0.5)), 4))
                        self.sarima_weight_var.set(round(float(weights.get("sarima", 0.5)), 4))
                        self.model_cfg.setdefault("weights", {})
                        self.model_cfg["weights"].update({k: float(v) for k, v in weights.items()})
                        rec_info = {
                            "model": model_type,
                            "weights": {k: round(float(v), 4) for k, v in weights.items()},
                            "method": rec.get("weight_method", "回测"),
                            "summary": bt.get("summary", {}),
                        }
                    else:
                        model_type = "ensemble"
                except Exception:
                    model_type = "ensemble"

            # 每次预测前清空置信带（由 SARIMA 路径填充）
            self.model_conf_int = None
            self.growth_warnings = {}

            # 预测引擎：intervention(默认, 节假日/COVID 入 SARIMAX exog, 无后处理) / legacy(传统后处理管线)
            engine = str(getattr(self, "engine_var", tk.StringVar(value="intervention")).get() or "intervention")
            use_intervention = engine == "intervention"

            # 根据选择的模型进行预测
            if model_type == "ensemble":
                forecast = self.intervention_forecast(ts, factors) if use_intervention else self.ensemble_forecast(ts, factors)
            elif model_type == "hw":
                forecast = self.holt_winters_forecast(ts)
            elif model_type == "sarima":
                forecast = self.sarimax_intervention_forecast(ts, factors) if use_intervention else self.sarima_forecast(ts, factors)
            else:
                forecast = self.intervention_forecast(ts, factors) if use_intervention else self.ensemble_forecast(ts, factors)

            # 记录预测决策信息（供报告/展示）
            self.last_rec_info = rec_info

            if use_intervention:
                # 干预引擎: 节假日/COVID 已在 exog 建模, 无乘法后处理;
                # 增长率改为合理性告警不强制覆盖 (回测实证: 强制覆盖为最大失真源)
                self.apply_growth_sanity_check(forecast)
            else:
                # 应用农历假日效应
                forecast = self.apply_lunar_holiday_effects(forecast)

                # 应用年度增长率调整
                forecast = self.apply_annual_growth_adjustment(forecast)

            # 生成预测结果表格
            self.generate_forecast_table(forecast)

            # 显示预测图表
            self.plot_forecast(ts, forecast)

            if rec_info is not None:
                self.update_status(f"预测完成（自动推荐：{rec_info['model']}，权重方法：{rec_info['method']}）")
            else:
                self.update_status("预测完成")

        except Exception as e:
            logging.exception("预测失败")
            messagebox.showerror("错误", f"预测失败: {str(e)}")
            self.update_status("预测失败")

    def run_backtest(self):
        if self.data is None or len(self.data) < 24:
            messagebox.showwarning("警告", "至少需要24个月的历史数据才能进行回测")
            return
        try:
            ts = self.prepare_time_series()

            factors = None
            if self.external_enabled:
                try:
                    factors = self.external_mgr.get_monthly_factors(ts.index, periods=12)
                except Exception:
                    factors = None

            profile = dict(self.profile)
            holiday_cfg = dict(profile.get("holiday", {}))
            growth_cfg = dict(profile.get("growth", {}))
            model_cfg = dict(profile.get("model", {}))

            holiday_cfg["enabled"] = bool(self.holiday_var.get()) if hasattr(self, "holiday_var") else bool(holiday_cfg.get("enabled", True))
            growth_cfg["annual_growth_rate"] = float(self.growth_cfg.get("annual_growth_rate", self.lunar_config.get("annual_growth_rate", 0.027)))

            model_cfg.setdefault("holt_winters", {})
            model_cfg["holt_winters"]["auto_tune"] = bool(self.hw_auto_var.get()) if hasattr(self, "hw_auto_var") else bool(model_cfg.get("holt_winters", {}).get("auto_tune", False))

            model_cfg.setdefault("sarima", {})
            model_cfg["sarima"]["auto_tune"] = bool(self.sarima_auto_var.get()) if hasattr(self, "sarima_auto_var") else bool(model_cfg.get("sarima", {}).get("auto_tune", False))

            engine = str(getattr(self, "engine_var", tk.StringVar(value="intervention")).get() or "intervention")
            model_cfg["engine"] = engine

            profile["holiday"] = holiday_cfg
            profile["growth"] = growth_cfg
            profile["model"] = model_cfg

            result = rolling_backtest(ts, profile, horizon=12, step=12, min_train=24, factors=factors, engine=engine)
            if "error" in result:
                messagebox.showerror("回测失败", str(result["error"]))
                return

            weights = recommend_weights_from_backtest(result)
            self.model_cfg.setdefault("weights", {})
            self.model_cfg["weights"].update(weights)
            if hasattr(self, "hw_weight_var"):
                self.hw_weight_var.set(round(float(weights.get("hw", 0.5)), 4))
                self.sarima_weight_var.set(round(float(weights.get("sarima", 0.5)), 4))

            summary = result.get("summary", {})
            rec = result.get("recommendation") or {}
            engine_label = "干预集成" if engine == "intervention" else "传统管线"
            text = f"回测评估(滚动12个月 · 引擎: {engine_label})：\n\n"
            for k, name in [("hw", "Holt-Winters"), ("sarima", "SARIMA" + ("(干预)" if engine == "intervention" else "")), ("ensemble", "融合模型")]:
                s = summary.get(k, {})
                text += f"{name} - MAPE: {s.get('mape', float('nan')):.2f}%, RMSE: {s.get('rmse', float('nan')):.2f}, "
                text += f"MDA: {s.get('mda', float('nan')):.2f}, TheilU: {s.get('theil_u', float('nan')):.2f}\n"
            text += f"\n推荐模型：{rec.get('model', 'ensemble')}（权重方法：{rec.get('weight_method', '回测')}）\n"
            text += f"推荐权重：HW={weights.get('hw', 0.5):.3f}, SARIMA={weights.get('sarima', 0.5):.3f}\n"
            text += f"\n说明：MAPE 越低越好；MDA 为方向命中率（越高越好）；Theil U<1 表示优于朴素基准。"

            messagebox.showinfo("模型回测评估", text)
        except Exception as e:
            messagebox.showerror("回测失败", str(e))

    def _prepare_exog(self, ts, factors, periods: int = 12):
        """将月度因子拆分为训练期与预测期外生变量（与 SARIMAX 对齐）"""
        if factors is None or len(ts) == 0:
            return None, None
        try:
            idx = ts.index
            train = factors.reindex(idx)
            if train.isna().any().any():
                train = train.ffill().bfill()
                if train.isna().any().any():
                    return None, None
            last = pd.Timestamp(idx[-1]).to_period("M").to_timestamp()
            fut = pd.date_range(start=(last.to_period("M") + 1).to_timestamp(), periods=int(periods), freq="MS")
            fut_f = factors.reindex(fut)
            if fut_f.isna().any().any():
                fut_f = fut_f.ffill().bfill()
                if fut_f.isna().any().any():
                    return None, None
            return train, fut_f
        except Exception:
            return None, None

    def _prepare_exog_full(self, ts, factors, periods: int = 12):
        """构造覆盖 (历史+未来) 的 ask/gdp 外生变量 DataFrame（供干预引擎）"""
        if factors is None or len(ts) == 0:
            return None
        try:
            train, fut_f = self._prepare_exog(ts, factors, periods)
            if train is None or fut_f is None:
                return None
            return pd.concat([train, fut_f])
        except Exception:
            return None

    def intervention_forecast(self, ts, factors=None):
        """V2 干预集成引擎: HW + SARIMAX(节假日/COVID exog), 无后处理。

        解决两大失真源 (融入来源: V1.1.1 分支):
          ① 季节性双重叠加 → 节假日入 SARIMAX exog, 不再后处理乘法
          ② COVID 结构断点 → covid_step + covid_recovery 干预变量显式建模
        增长率仅告警不强制覆盖 (apply_growth_sanity_check)。
        """
        weights = {"hw": float(self.hw_weight_var.get()), "sarima": float(self.sarima_weight_var.get())}
        sarima_cfg = self.model_cfg.get("sarima", {}) if isinstance(self.model_cfg.get("sarima", {}), dict) else {}
        hw_cfg = self.model_cfg.get("holt_winters", {}) if isinstance(self.model_cfg.get("holt_winters", {}), dict) else {}
        exog_full = self._prepare_exog_full(ts, factors)

        hw = holt_winters_forecast(
            ts,
            periods=12,
            trend=hw_cfg.get("trend", "add"),
            seasonal=hw_cfg.get("seasonal", "add"),
            seasonal_periods=int(hw_cfg.get("seasonal_periods", 12)),
            auto_tune=bool(self.hw_auto_var.get()) if hasattr(self, "hw_auto_var") else bool(hw_cfg.get("auto_tune", False)),
        )
        sar = sarimax_intervention_forecast(
            ts,
            periods=12,
            spring_festival_dates=dict(self.spring_festival_dates),
            holiday_cfg=dict(self.holiday_cfg),
            include_covid=True,
            order=tuple(sarima_cfg.get("order", (1, 1, 1))),
            seasonal_order=tuple(sarima_cfg.get("seasonal_order", (1, 1, 1, 12))),
            exog_data=exog_full,
        )
        w_hw = float(weights.get("hw", 0.5))
        w_s = float(weights.get("sarima", 0.5))
        total = w_hw + w_s
        if total <= 0:
            w_hw = w_s = 0.5
            total = 1.0
        w_hw, w_s = w_hw / total, w_s / total
        idx = hw.forecast.index
        ens = (hw.forecast.reindex(idx).astype(float) * w_hw) + (sar.forecast.reindex(idx).astype(float) * w_s)
        ens = ens.clip(lower=0.0)
        self.model_results = {
            "Holt-Winters": hw.forecast,
            "SARIMAX-干预": sar.forecast,
            "Ensemble": ens,
        }
        self.model_conf_int = sar.meta.get("conf_int")
        return ens

    def sarimax_intervention_forecast(self, ts, factors=None):
        """单模型干预引擎: SARIMAX(节假日/COVID exog), 无后处理"""
        sarima_cfg = self.model_cfg.get("sarima", {}) if isinstance(self.model_cfg.get("sarima", {}), dict) else {}
        exog_full = self._prepare_exog_full(ts, factors)
        out = sarimax_intervention_forecast(
            ts,
            periods=12,
            spring_festival_dates=dict(self.spring_festival_dates),
            holiday_cfg=dict(self.holiday_cfg),
            include_covid=True,
            order=tuple(sarima_cfg.get("order", (1, 1, 1))),
            seasonal_order=tuple(sarima_cfg.get("seasonal_order", (1, 1, 1, 12))),
            exog_data=exog_full,
        )
        self.model_conf_int = out.meta.get("conf_int")
        return out.forecast

    def apply_growth_sanity_check(self, forecast):
        """增长率合理性告警: 不修改预测值, 偏离设定增长率时提示业务判断"""
        annual_growth_rate = float(self.growth_cfg.get("annual_growth_rate", self.lunar_config.get("annual_growth_rate", 0.027)))
        historical_yearly_total = None
        if self.data is not None and len(self.data) > 0:
            last_year = int(self.data["年份"].max())
            last_year_data = self.data[self.data["年份"] == last_year]
            if len(last_year_data) == 12:
                historical_yearly_total = float(last_year_data["旅客运输量"].sum())
            elif len(last_year_data) > 0:
                historical_yearly_total = float(last_year_data["旅客运输量"].mean() * 12)
        unchanged, warnings_info = growth_sanity_check(forecast, annual_growth_rate, historical_yearly_total)
        self.growth_warnings = warnings_info
        alerts = {y: info for y, info in warnings_info.items() if info.get("level") != "ok"}
        if alerts:
            msg = "增长率合理性告警（模型趋势项与设定增长率的偏离）：\n"
            for y, info in alerts.items():
                msg += f"  {y}年: 偏离 {info.get('deviation_pct', 0):+.1f}% (级别: {info.get('level')})\n"
            msg += "\n干预引擎不强制修改预测值，请结合业务判断。"
            self.update_status("预测完成（含增长率告警）")
            try:
                messagebox.showwarning("增长率告警", msg)
            except Exception:
                pass
        return unchanged

    def ensemble_forecast(self, ts, factors=None):
        weights = {"hw": float(self.hw_weight_var.get()), "sarima": float(self.sarima_weight_var.get())}
        sarima_cfg = self.model_cfg.get("sarima", {}) if isinstance(self.model_cfg.get("sarima", {}), dict) else {}
        hw_cfg = self.model_cfg.get("holt_winters", {}) if isinstance(self.model_cfg.get("holt_winters", {}), dict) else {}
        exog_train, exog_future = self._prepare_exog(ts, factors)
        out, components = ensemble_forecast(
            ts,
            weights=weights,
            auto_tune_sarima=bool(self.sarima_auto_var.get()) if hasattr(self, "sarima_auto_var") else bool(sarima_cfg.get("auto_tune", False)),
            auto_tune_hw=bool(self.hw_auto_var.get()) if hasattr(self, "hw_auto_var") else bool(hw_cfg.get("auto_tune", False)),
            sarima_params={"order": sarima_cfg.get("order", [1, 1, 1]), "seasonal_order": sarima_cfg.get("seasonal_order", [1, 1, 1, 12])},
            hw_params={"trend": hw_cfg.get("trend", "add"), "seasonal": hw_cfg.get("seasonal", "add"), "seasonal_periods": hw_cfg.get("seasonal_periods", 12)},
            periods=12,
            exog=exog_train,
            exog_future=exog_future,
        )
        self.model_results = {
            "Holt-Winters": components["Holt-Winters"].forecast,
            "SARIMA": components["SARIMA"].forecast,
            "Ensemble": out.forecast,
        }
        self.model_conf_int = components["SARIMA"].meta.get("conf_int")
        return out.forecast

    def holt_winters_forecast(self, ts):
        hw_cfg = self.model_cfg.get("holt_winters", {}) if isinstance(self.model_cfg.get("holt_winters", {}), dict) else {}
        out = holt_winters_forecast(
            ts,
            periods=12,
            trend=hw_cfg.get("trend", "add"),
            seasonal=hw_cfg.get("seasonal", "add"),
            seasonal_periods=int(hw_cfg.get("seasonal_periods", 12)),
            auto_tune=bool(self.hw_auto_var.get()) if hasattr(self, "hw_auto_var") else bool(hw_cfg.get("auto_tune", False)),
        )
        self.model_conf_int = None  # HW 无置信区间
        return out.forecast

    def sarima_forecast(self, ts, factors=None):
        sarima_cfg = self.model_cfg.get("sarima", {}) if isinstance(self.model_cfg.get("sarima", {}), dict) else {}
        exog_train, exog_future = self._prepare_exog(ts, factors)
        out = sarima_forecast(
            ts,
            periods=12,
            order=tuple(sarima_cfg.get("order", (1, 1, 1))),
            seasonal_order=tuple(sarima_cfg.get("seasonal_order", (1, 1, 1, 12))),
            auto_tune=bool(self.sarima_auto_var.get()) if hasattr(self, "sarima_auto_var") else bool(sarima_cfg.get("auto_tune", False)),
            exog=exog_train,
            exog_future=exog_future,
        )
        self.model_conf_int = out.meta.get("conf_int")
        return out.forecast

    def simple_seasonal_forecast(self, ts):
        return simple_seasonal_forecast(ts, periods=12)

    def apply_lunar_holiday_effects(self, forecast):
        """应用农历假日效应"""
        temp_cfg = dict(self.holiday_cfg)
        if hasattr(self, "holiday_var"):
            temp_cfg["enabled"] = bool(self.holiday_var.get())
        adjusted, spring_info = apply_holiday_effects(forecast, temp_cfg, self.spring_festival_dates)
        self.spring_festival_info = spring_info
        return adjusted

    def generate_forecast_table(self, forecast):
        """生成预测结果表格"""
        # 清空表格
        for item in self.forecast_tree.get_children():
            self.forecast_tree.delete(item)

        # 保存预测数据
        self.forecast_data = []

        # 计算年度增长率
        forecast_df = pd.DataFrame({
            'date': forecast.index,
            'value': forecast.values,
            'year': forecast.index.year,
            'month': forecast.index.month
        })

        yearly_totals = forecast_df.groupby('year')['value'].sum()

        # 添加数据到表格
        for i, (date, value) in enumerate(forecast.items()):
            year = date.year
            month = date.month
            passenger_count = int(value)

            # 获取春运天数
            spring_days = 0
            key = f"{year}-{month:02d}"
            if hasattr(self, 'spring_festival_info') and key in self.spring_festival_info:
                spring_days = self.spring_festival_info[key]['春运天数']

            # 计算月度增长率
            growth_rate = 0
            if i > 0:
                prev_value = forecast.iloc[i - 1]
                if prev_value > 0:
                    growth_rate = (passenger_count - prev_value) / prev_value * 100

            tags = []
            if i % 2 == 1:
                tags.append("odd")
            if int(spring_days) > 0:
                tags.append("spring")
            if growth_rate > 0.01:
                tags.append("pos")
            elif growth_rate < -0.01:
                tags.append("neg")

            self.forecast_tree.insert(
                "",
                "end",
                values=(year, month, f"{passenger_count:,}", spring_days, f"{growth_rate:+.2f}%"),
                tags=tuple(tags),
            )

            self.forecast_data.append({
                '年份': year,
                '月份': month,
                '旅客运输量': passenger_count,
                '春运天数': spring_days,
                '月度增长率': growth_rate,
                '年度增长率': self.growth_rates.get(year, 0) if hasattr(self, 'growth_rates') else 0
            })

    def plot_forecast(self, history, forecast):
        """绘制预测图表"""
        # 保存数据以供缩放时刷新
        self._last_history = history
        self._last_forecast = forecast

        self.ensure_forecast_canvas()
        # 清除现有图表
        self.forecast_ax.clear()

        scale = float(self.ui_scale_var.get()) if hasattr(self, "ui_scale_var") else 1.0
        label_size = max(9, int(round(11 * scale)))
        title_size = max(11, int(round(14 * scale)))
        tick_size = max(8, int(round(9 * scale)))
        legend_size = max(8, int(round(9 * scale)))

        # 绘制历史数据
        self.forecast_ax.plot(history.index, history.values, color=T_COLORS["primary"],
                              label='历史数据', linewidth=2.2, marker='o', markersize=max(4, 6*scale))

        # 绘制预测数据
        self.forecast_ax.plot(forecast.index, forecast.values, color=T_COLORS["danger"],
                              label='预测数据', linewidth=2.2, marker='s', markersize=max(4, 6*scale))

        # 历史/预测分界
        if len(history) > 0 and len(forecast) > 0:
            boundary = forecast.index[0]
            self.forecast_ax.axvline(boundary, color=T_COLORS["border"], linestyle='--', linewidth=1.2, alpha=0.9)

        # 置信带（SARIMA 95% 预测区间）
        conf = getattr(self, "model_conf_int", None)
        if conf is not None and len(conf):
            try:
                lower = conf["lower"].reindex(forecast.index)
                upper = conf["upper"].reindex(forecast.index)
                if lower.notna().any() and upper.notna().any():
                    self.forecast_ax.fill_between(lower.index, lower.values, upper.values,
                                                  color=T_COLORS["primary_light"], alpha=0.15,
                                                  label='SARIMA 95%区间')
            except Exception:
                pass

        # 如果有多模型结果，绘制对比
        if hasattr(self, 'model_results') and self.model_results:
            colors = [T_COLORS["primary_light"], T_COLORS["accent"]]
            for idx, (model_name, model_forecast) in enumerate(self.model_results.items()):
                if model_name != 'Ensemble':
                    self.forecast_ax.plot(model_forecast.index, model_forecast.values,
                                          color=colors[idx % len(colors)], linestyle=':',
                                          linewidth=1.4, label=f'{model_name}模型', alpha=0.85)

        # 标记春运月份
        if hasattr(self, 'spring_festival_info') and self.spring_festival_info:
            for key, info in self.spring_festival_info.items():
                if info['春运天数'] > 0:
                    year, month = map(int, key.split('-'))
                    try:
                        date = pd.Timestamp(year=year, month=month, day=1)
                        y = float(forecast.loc[date]) if date in forecast.index else float(forecast.iloc[0])
                        self.forecast_ax.plot(date, y, 'g*',
                                              markersize=max(8, 12*scale),
                                              label='春运' if key == list(self.spring_festival_info.keys())[0] else "")
                    except Exception:
                        pass

        self.forecast_ax.set_xlabel('日期', fontsize=label_size)
        self.forecast_ax.set_ylabel('旅客运输量', fontsize=label_size)

        model_name = {
            'ensemble': '融合模型',
            'hw': 'Holt-Winters',
            'sarima': 'SARIMA'
        }.get(self.model_var.get(), '融合模型')
        mode = str(getattr(self, "model_mode_var", tk.StringVar(value="auto")).get() or "auto")
        mode_text = "自动推荐" if mode == "auto" else "手动选择"
        title = f'旅客运输量预测 ({model_name} · {mode_text})'
        if getattr(self, "last_rec_info", None):
            title += f" · 回测推荐权重 HW {self.last_rec_info['weights'].get('hw', 0.5):.2f}/SA {self.last_rec_info['weights'].get('sarima', 0.5):.2f}"
        self.forecast_ax.set_title(title, fontsize=title_size, fontweight='bold')
        self.forecast_ax.tick_params(axis="both", labelsize=tick_size)
        self.forecast_ax.legend(loc='best', fontsize=legend_size)
        self.forecast_ax.grid(True, alpha=0.3)
        
        self.forecast_fig.tight_layout()
        self.forecast_canvas.draw()
        self.forecast_ax.grid(True, alpha=0.3)

        # 旋转x轴标签
        plt.setp(self.forecast_ax.xaxis.get_majorticklabels(), rotation=45)
        self.forecast_fig.tight_layout()
        self.forecast_canvas.draw()

    def export_forecast_data(self):
        """导出预测数据"""
        if self.forecast_data is None or len(self.forecast_data) == 0:
            messagebox.showwarning("警告", "请先进行预测再导出")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
            initialfile=f"旅客运输量预测结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        if file_path:
            try:
                # 创建DataFrame
                df = pd.DataFrame(self.forecast_data)

                # 导出到Excel
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    # 写入说明
                    df_description = pd.DataFrame({
                        '说明': [
                            '数据来源：民航旅客运输量预测系统 V1.1',
                            f'导出时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                            f'预测模型：{self.model_var.get()}',
                            f'年度增长率：{self.lunar_config["annual_growth_rate"] * 100:.2f}%',
                            f'启用节假日效应：{"是" if self.holiday_var.get() else "否"}',
                            '注：春运天数基于农历春节日期计算；精选算法集合见“算法手册”',
                        ]
                    })
                    df_description.to_excel(writer, sheet_name='说明', index=False)

                    # 写入预测数据
                    df.to_excel(writer, sheet_name='预测结果', index=False)

                    # 添加年度汇总
                    yearly_summary = df.groupby('年份').agg({
                        '旅客运输量': ['sum', 'mean', 'std', 'min', 'max']
                    }).round(0)
                    yearly_summary.columns = ['合计', '月均', '标准差', '最小值', '最大值']
                    yearly_summary.to_excel(writer, sheet_name='年度汇总')

                self.update_status(f"预测数据已导出: {os.path.basename(file_path)}")
                messagebox.showinfo("成功", f"预测数据已成功导出")

            except Exception as e:
                logging.exception("导出失败")
                messagebox.showerror("错误", f"导出失败: {str(e)}")

    def export_growth_analysis(self):
        """导出增长分析报告"""
        if not hasattr(self, 'growth_rates') or not self.growth_rates:
            messagebox.showwarning("警告", "请先运行预测以生成增长分析")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
            initialfile=f"增长分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        if file_path:
            try:
                # 准备数据
                forecast_df = pd.DataFrame(self.forecast_data)

                # 计算年度数据
                yearly_data = forecast_df.groupby('年份').agg({
                    '旅客运输量': ['sum', 'mean', 'std', 'min', 'max']
                }).round(0)
                yearly_data.columns = ['年度合计', '月均', '标准差', '最小值', '最大值']

                # 计算增长率
                growth_data = []
                years = sorted(self.growth_rates.keys())

                for i, year in enumerate(years):
                    if i == 0:
                        # 第一年，计算相对于基准的增长
                        growth_rate = self.growth_rates[year]
                        target_growth = self.lunar_config['annual_growth_rate'] * 100
                        deviation = growth_rate - target_growth
                    else:
                        # 后续年份
                        growth_rate = self.growth_rates[year]
                        target_growth = self.lunar_config['annual_growth_rate'] * 100
                        deviation = growth_rate - target_growth

                    growth_data.append({
                        '年份': year,
                        '实际增长率': f"{growth_rate:.2f}%",
                        '目标增长率': f"{target_growth:.2f}%",
                        '偏差': f"{deviation:.2f}%"
                    })

                growth_df = pd.DataFrame(growth_data)

                # 导出到Excel
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    # 写入增长分析
                    growth_df.to_excel(writer, sheet_name='增长率分析', index=False)

                    # 写入年度数据
                    yearly_data.to_excel(writer, sheet_name='年度数据')

                    # 添加春运分析
                    if hasattr(self, 'spring_festival_info') and self.spring_festival_info:
                        spring_data = []
                        for key, info in self.spring_festival_info.items():
                            year, month = map(int, key.split('-'))
                            spring_data.append({
                                '年份': year,
                                '月份': month,
                                '春节日期': info['春节日期'],
                                '春运天数': info['春运天数'],
                                '效应系数': info['效应系数'],
                                '效应强度': f"{(info['效应系数'] - 1) * 100:.1f}%"
                            })

                        spring_df = pd.DataFrame(spring_data)
                        spring_df.to_excel(writer, sheet_name='春运分析', index=False)

                    # 添加配置信息
                    config_data = {
                        '配置项': list(self.lunar_config.keys()),
                        '配置值': [f"{v * 100:.2f}%" if k == 'annual_growth_rate' else v
                                   for k, v in self.lunar_config.items()]
                    }
                    config_df = pd.DataFrame(config_data)
                    config_df.to_excel(writer, sheet_name='配置信息', index=False)

                self.update_status(f"增长分析报告已导出: {os.path.basename(file_path)}")
                messagebox.showinfo("成功", f"增长分析报告已成功导出")

            except Exception as e:
                logging.exception("导出失败")
                messagebox.showerror("错误", f"导出失败: {str(e)}")

    def export_full_report(self):
        """导出完整报告"""
        if self.data is None or self.forecast_data is None:
            messagebox.showwarning("警告", "没有足够的数据生成完整报告")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
            initialfile=f"民航旅客运输量完整报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        if file_path:
            try:
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    # 1. 封面
                    cover_df = pd.DataFrame({
                        '民航旅客运输量预测分析报告 (最终版)': [
                            '',
                            f'报告生成时间：{datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}',
                            f'历史数据量：{len(self.data)} 条',
                            f'预测期数：{len(self.forecast_data)} 个月',
                            f'预测模型：{self.model_var.get()}',
                            f'年度增长率：{self.lunar_config["annual_growth_rate"] * 100:.2f}%',
                            '',
                            '报告特点：',
                            f'1. 春运窗口：春节前{int(self.holiday_cfg.get("spring_travel_before_days", 15))}天到春节后{int(self.holiday_cfg.get("spring_travel_after_days", 24))}天',
                            f'2. 每年总旅客运输量环比增长{self.lunar_config["annual_growth_rate"] * 100:.2f}%',
                            '3. 基于农历春节日期计算春运',
                            '4. 多模型融合优化预测精度'
                        ]
                    })
                    cover_df.to_excel(writer, sheet_name='报告封面', index=False, header=False)

                    # 2. 历史数据
                    self.data.to_excel(writer, sheet_name='历史数据', index=False)

                    # 3. 预测结果
                    forecast_df = pd.DataFrame(self.forecast_data)
                    forecast_df.to_excel(writer, sheet_name='预测结果', index=False)

                    # 4. 增长分析
                    if hasattr(self, 'growth_rates'):
                        growth_data = []
                        for year, rate in self.growth_rates.items():
                            growth_data.append({
                                '年份': year,
                                '实际增长率': f"{rate:.2f}%",
                                '目标增长率': f"{self.lunar_config['annual_growth_rate'] * 100:.2f}%"
                            })
                        pd.DataFrame(growth_data).to_excel(writer, sheet_name='增长分析', index=False)

                    # 5. 年度汇总
                    combined_data = []
                    for idx, row in self.data.iterrows():
                        combined_data.append({
                            '年份': row['年份'],
                            '月份': row['月份'],
                            '旅客运输量': row['旅客运输量'],
                            '类型': '历史'
                        })

                    for item in self.forecast_data:
                        combined_data.append({
                            '年份': item['年份'],
                            '月份': item['月份'],
                            '旅客运输量': item['旅客运输量'],
                            '类型': '预测'
                        })

                    combined_df = pd.DataFrame(combined_data)
                    yearly_summary = combined_df.groupby(['年份', '类型']).agg({
                        '旅客运输量': ['sum', 'mean', 'std', 'min', 'max']
                    }).round(0)
                    yearly_summary.columns = ['合计', '月均', '标准差', '最小值', '最大值']
                    yearly_summary.to_excel(writer, sheet_name='年度汇总')

                    # 6. 月度分析
                    monthly_stats = combined_df.groupby('月份').agg({
                        '旅客运输量': ['mean', 'std', 'min', 'max', 'count']
                    }).round(0)
                    monthly_stats.columns = ['平均值', '标准差', '最小值', '最大值', '数据量']
                    monthly_stats.to_excel(writer, sheet_name='月度分析')

                self.update_status(f"完整报告已导出: {os.path.basename(file_path)}")
                messagebox.showinfo("成功", f"完整报告已成功导出")

            except Exception as e:
                logging.exception("导出失败")
                messagebox.showerror("错误", f"导出失败: {str(e)}")

    def data_preprocessing(self):
        """数据预处理"""
        if self.data is None or len(self.data) < 12:
            messagebox.showwarning("警告", "至少需要12个月的历史数据")
            return

        try:
            self.update_status("正在进行数据预处理...")

            # 创建时间序列
            ts = self.prepare_time_series()

            # 1. 平稳性检验
            from statsmodels.tsa.stattools import adfuller
            adf_result = adfuller(ts, autolag='AIC')
            is_stationary = adf_result[1] < 0.05

            # 2. 季节性分解
            from statsmodels.tsa.seasonal import seasonal_decompose
            decomposition = seasonal_decompose(ts, model='additive', period=12)

            # 3. 计算统计量
            stats = {
                'stationary': is_stationary,
                'adf_pvalue': adf_result[1],
                'mean': ts.mean(),
                'std': ts.std(),
                'trend_strength': 1 - (decomposition.resid.var() / ts.var()) if ts.var() > 0 else 0,
                'seasonal_strength': 1 - (decomposition.resid.var() / decomposition.seasonal.var())
                if decomposition.seasonal.var() > 0 else 0
            }

            # 更新分析图表
            self.update_analysis_charts(ts, decomposition, stats)

            # 显示结果
            result_text = f"数据预处理结果:\n"
            result_text += f"平稳性检验: {'平稳' if is_stationary else '非平稳'}\n"
            result_text += f"ADF检验p值: {adf_result[1]:.4f}\n"
            result_text += f"均值: {ts.mean():.0f}\n"
            result_text += f"标准差: {ts.std():.0f}\n"
            result_text += f"趋势强度: {stats['trend_strength']:.2%}\n"
            result_text += f"季节强度: {stats['seasonal_strength']:.2%}\n\n"
            result_text += f"建议: {'数据已平稳，可直接建模' if is_stationary else '建议进行差分处理'}"

            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, result_text)

            self.update_status("数据预处理完成")

        except Exception as e:
            messagebox.showerror("错误", f"数据预处理失败: {str(e)}")

    def data_diagnosis(self):
        """数据诊断"""
        if self.data is None:
            return

        try:
            ts = self.prepare_time_series()

            diagnosis = f"数据诊断报告:\n"
            diagnosis += f"数据量: {len(ts)} 个月\n"

            # 检查缺失值
            missing_months = self.check_missing_months()
            if missing_months:
                diagnosis += f"缺失月份: {len(missing_months)} 个\n"

            # 检查异常值
            outliers = self.detect_outliers(ts)
            if len(outliers) > 0:
                diagnosis += f"异常值: {len(outliers)} 个\n"

            # 季节性分析
            seasonal_pattern = self.analyze_seasonality()
            diagnosis += f"季节性模式: {seasonal_pattern}\n"

            messagebox.showinfo("数据诊断", diagnosis)

        except Exception as e:
            messagebox.showerror("错误", f"数据诊断失败: {str(e)}")

    def check_missing_months(self):
        """检查缺失月份"""
        if self.data is None:
            return []

        dates = []
        for _, row in self.data.iterrows():
            dates.append(f"{int(row['年份'])}-{int(row['月份']):02d}")

        # 假设数据应该是连续的
        missing = []
        return missing

    def detect_outliers(self, ts, n_std=3):
        """检测异常值"""
        mean = ts.mean()
        std = ts.std()

        outliers = ts[(ts < mean - n_std * std) | (ts > mean + n_std * std)]
        return outliers

    def analyze_seasonality(self):
        """分析季节性模式"""
        if self.data is None:
            return "数据不足"

        # 简单季节性分析
        monthly_avg = self.data.groupby('月份')['旅客运输量'].mean()
        peak_month = monthly_avg.idxmax()

        seasons = {
            1: "春运高峰", 2: "春运高峰",
            7: "暑假高峰", 8: "暑假高峰",
            5: "五一高峰", 10: "十一高峰"
        }

        return seasons.get(peak_month, f"季节性不显著，高峰在{peak_month}月")

    def update_analysis_charts(self, ts, decomposition, stats):
        """更新分析图表"""
        # 保存数据以供缩放时刷新
        self._last_analysis_ts = ts
        self._last_analysis_decomp = decomposition
        self._last_analysis_stats = stats

        self.ensure_analysis_canvas()
        # 清除现有图表
        for ax in self.analysis_axs.flat:
            ax.clear()

        scale = float(self.ui_scale_var.get()) if hasattr(self, "ui_scale_var") else 1.0
        label_size = max(8, int(round(9 * scale)))
        title_size = max(10, int(round(12 * scale)))
        tick_size = max(7, int(round(8 * scale)))

        # 1. 原始时间序列
        self.analysis_axs[0, 0].plot(ts.index, ts.values, color=T_COLORS["primary"], linewidth=1.8)
        self.analysis_axs[0, 0].set_title('原始时间序列', fontsize=title_size, fontweight='bold')
        self.analysis_axs[0, 0].set_xlabel('日期', fontsize=label_size)
        self.analysis_axs[0, 0].set_ylabel('旅客运输量', fontsize=label_size)
        self.analysis_axs[0, 0].tick_params(labelsize=tick_size)
        self.analysis_axs[0, 0].grid(True, alpha=0.25, color=T_COLORS["border"])

        # 2. 季节性分解
        self.analysis_axs[0, 1].plot(decomposition.trend.index, decomposition.trend.values, color=T_COLORS["success"], linewidth=1.8)
        self.analysis_axs[0, 1].set_title('趋势成分', fontsize=title_size, fontweight='bold')
        self.analysis_axs[0, 1].set_xlabel('日期', fontsize=label_size)
        self.analysis_axs[0, 1].set_ylabel('趋势', fontsize=label_size)
        self.analysis_axs[0, 1].tick_params(labelsize=tick_size)
        self.analysis_axs[0, 1].grid(True, alpha=0.25, color=T_COLORS["border"])

        # 3. 季节性成分
        self.analysis_axs[1, 0].plot(decomposition.seasonal.index, decomposition.seasonal.values, color=T_COLORS["accent"], linewidth=1.8)
        self.analysis_axs[1, 0].set_title('季节性成分', fontsize=title_size, fontweight='bold')
        self.analysis_axs[1, 0].set_xlabel('日期', fontsize=label_size)
        self.analysis_axs[1, 0].set_ylabel('季节性', fontsize=label_size)
        self.analysis_axs[1, 0].tick_params(labelsize=tick_size)
        self.analysis_axs[1, 0].grid(True, alpha=0.25, color=T_COLORS["border"])

        # 4. 残差
        self.analysis_axs[1, 1].plot(decomposition.resid.index, decomposition.resid.values, color=T_COLORS["text_sub"], linewidth=1.2)
        self.analysis_axs[1, 1].axhline(0, color=T_COLORS["border"], linewidth=0.8, linestyle='--')
        self.analysis_axs[1, 1].set_title('残差成分', fontsize=title_size, fontweight='bold')
        self.analysis_axs[1, 1].set_xlabel('日期', fontsize=label_size)
        self.analysis_axs[1, 1].set_ylabel('残差', fontsize=label_size)
        self.analysis_axs[1, 1].tick_params(labelsize=tick_size)
        self.analysis_axs[1, 1].grid(True, alpha=0.25, color=T_COLORS["border"])

        # 调整布局
        self.analysis_fig.tight_layout()
        self.analysis_canvas.draw()

    def export_original_data(self):
        """导出原始数据"""
        if self.data is None:
            messagebox.showwarning("警告", "没有数据可导出")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
            initialfile="原始数据.xlsx"
        )

        if file_path:
            try:
                self.data.to_excel(file_path, index=False)
                self.update_status(f"原始数据已导出: {os.path.basename(file_path)}")
                messagebox.showinfo("成功", f"原始数据已成功导出")
            except Exception as e:
                logging.exception("导出失败")
                messagebox.showerror("错误", f"导出失败: {str(e)}")

    def clear_data(self):
        """清空数据"""
        if messagebox.askyesno("确认", "确定要清空所有数据吗？"):
            # 清空表格
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)

            for item in self.forecast_tree.get_children():
                self.forecast_tree.delete(item)

            # 清空统计信息
            self.stats_text.delete(1.0, tk.END)

            # 清空数据
            self.data = None
            self.forecast_data = None
            self.model_results = {}

            # 清空图表
            if getattr(self, "analysis_axs", None) is not None:
                for ax in self.analysis_axs.flat:
                    ax.clear()
                self.analysis_fig.tight_layout()
                self.analysis_canvas.draw()

            if getattr(self, "forecast_ax", None) is not None:
                self.forecast_ax.clear()
                self.forecast_fig.tight_layout()
                self.forecast_canvas.draw()

            self.update_status("数据已清空")

    # ========== 管理控制台：官方数据源接入 ==========

    def open_admin_console(self):
        """管理控制台：自动接入官方渠道数据源（GDP / ASK）并纳入预测"""
        win = tk.Toplevel(self.root)
        win.title("管理控制台 - 官方数据源接入")
        win.geometry("880x640")
        win.configure(bg=T_COLORS["bg_window"])
        win.transient(self.root)

        header = card_frame(win, "数据源接入说明")
        header.pack(fill=tk.X, padx=12, pady=(12, 4))
        tk.Label(header, text="自动接入国家统计局（GDP）与民航行业（ASK 可用座公里）数据，"
                              "接入后作为外生变量参与 SARIMAX 预测计算。",
                 bg=T_COLORS["bg_card"], fg=T_COLORS["text_sub"]).pack(anchor="w", padx=8, pady=2)
        tk.Label(header, text="离线时自动降级为内置参考数据，并在此标注实际来源。",
                 bg=T_COLORS["bg_card"], fg=T_COLORS["text_sub"]).pack(anchor="w", padx=8, pady=(0, 4))

        # ---- 数据源状态表 ----
        status_card = card_frame(win, "数据源状态")
        status_card.pack(fill=tk.X, padx=12, pady=6)
        cols = ("指标", "来源", "数据量", "最新日期", "最新值", "更新时间", "状态")
        self.admin_tree = ttk.Treeview(status_card, columns=cols, show="headings", height=3, style="Modern.Treeview")
        widths = {"指标": 120, "来源": 160, "数据量": 70, "最新日期": 100, "最新值": 100, "更新时间": 150, "状态": 70}
        for c in cols:
            self.admin_tree.heading(c, text=c)
            self.admin_tree.column(c, width=widths[c], anchor=tk.CENTER)
        vsb = ttk.Scrollbar(status_card, orient=tk.VERTICAL, command=self.admin_tree.yview, style="Modern.Vertical.TScrollbar")
        self.admin_tree.configure(yscrollcommand=vsb.set)
        self.admin_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=6)
        vsb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 8), pady=6)

        def refresh_status():
            try:
                for item in self.admin_tree.get_children():
                    self.admin_tree.delete(item)
                for row in self.external_mgr.status():
                    latest = row.get("最新值")
                    latest_text = f"{latest:,.1f}" if latest is not None else "-"
                    self.admin_tree.insert("", "end", values=(
                        row["指标"], row["来源"], row["数据量"], row["最新日期"],
                        latest_text, row["更新时间"], row["状态"],
                    ))
            except Exception:
                pass

        # ---- 底部操作区 ----
        bottom = tk.Frame(win, bg=T_COLORS["bg_window"])
        bottom.pack(fill=tk.X, padx=12, pady=6)
        self.external_enabled_var = tk.BooleanVar(value=bool(self.external_enabled))
        ttk.Checkbutton(bottom, text="接入预测（GDP/ASK 参与预测计算）",
                        variable=self.external_enabled_var,
                        command=self._toggle_external).pack(side=tk.LEFT)

        update_btn = ttk.Button(bottom, text="一键更新数据", style="Modern.TButton")
        update_btn.pack(side=tk.LEFT, padx=10)
        ttk.Button(bottom, text="清理缓存", style="Danger.TButton",
                   command=self._admin_clear_cache).pack(side=tk.LEFT)
        self.admin_status_label = tk.Label(bottom, text=self.external_status_text,
                                           bg=T_COLORS["bg_window"], fg=T_COLORS["text_sub"])
        self.admin_status_label.pack(side=tk.RIGHT)

        # ---- 指标趋势预览 ----
        preview_card = card_frame(win, "指标趋势预览（近 5 年）")
        preview_card.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.6, 3.6), sharex=True)
        canvas = FigureCanvasTkAgg(fig, master=preview_card)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        def draw_preview():
            try:
                data = self.external_mgr.load()
                gdp = data["gdp"]["gdp"].iloc[-60:]
                ask = data["ask"]["ask"].iloc[-60:]
                ax1.clear(); ax2.clear()
                ax1.plot(gdp.index, gdp.values, color=T_COLORS["primary"], linewidth=1.8, label="GDP（亿元）")
                ax1.set_ylabel("GDP（亿元）", fontsize=9); ax1.legend(fontsize=8); ax1.grid(alpha=0.25)
                ax2.plot(ask.index, ask.values, color=T_COLORS["primary_light"], linewidth=1.8, label="ASK（亿座公里）")
                ax2.set_ylabel("ASK（亿座公里）", fontsize=9); ax2.legend(fontsize=8); ax2.grid(alpha=0.25)
                for ax in (ax1, ax2):
                    ax.tick_params(labelsize=8)
                fig.tight_layout()
                canvas.draw()
            except Exception:
                pass

        def do_update():
            update_btn.configure(state="disabled", text="正在更新...")

            def worker():
                try:
                    res = self.external_mgr.refresh(use_akshare=True)
                except Exception as e:
                    res = {"error": str(e)}

                def done():
                    try:
                        update_btn.configure(state="normal", text="一键更新数据")
                        refresh_status()
                        draw_preview()
                        if "error" in res:
                            self.admin_status_label.configure(text=f"更新失败: {res['error']}", fg=T_COLORS["danger"])
                        else:
                            src = f"GDP: {'在线' if res.get('gdp_ok') else '内置'} | ASK: {'在线' if res.get('ask_ok') else '内置'}"
                            self.admin_status_label.configure(text=f"更新完成 {res.get('refreshed_at', '')} | {src}", fg=T_COLORS["success"])
                            self.external_status_text = f"外部数据已更新 ({src})"
                            self.update_status(self.external_status_text)
                    except Exception:
                        pass

                try:
                    win.after(0, done)
                except Exception:
                    pass

            threading.Thread(target=worker, daemon=True).start()

        update_btn.configure(command=do_update)
        refresh_status()
        draw_preview()
        self.update_status("管理控制台已打开")

    def _toggle_external(self):
        """外部因子接入预测开关"""
        self.external_enabled = bool(self.external_enabled_var.get()) if hasattr(self, "external_enabled_var") else self.external_enabled
        self.external_status_text = "外部数据已启用" if self.external_enabled else "外部数据已停用"
        self.update_status(self.external_status_text)

    def _admin_clear_cache(self):
        if not messagebox.askyesno("确认", "确定要清空外部数据缓存吗？\n清空后将恢复为内置参考数据。"):
            return
        try:
            self.external_mgr.clear_cache()
            if hasattr(self, "admin_tree"):
                for item in self.admin_tree.get_children():
                    self.admin_tree.delete(item)
            self.update_status("外部数据缓存已清空")
            messagebox.showinfo("成功", "缓存已清空，当前使用内置参考数据")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    # ========== 算法使用手册 ==========

    def open_manual_viewer(self):
        """算法使用手册：点击查看（含已移除算法说明）"""
        win = tk.Toplevel(self.root)
        win.title("算法使用手册")
        win.geometry("980x680")
        win.configure(bg=T_COLORS["bg_window"])
        win.transient(self.root)

        main = tk.Frame(win, bg=T_COLORS["bg_window"])
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # 左侧：算法列表
        left = card_frame(main, "算法列表")
        left.pack(side=tk.LEFT, fill=tk.Y)
        list_tree = ttk.Treeview(left, columns=("name",), show="headings", height=8, style="Modern.Treeview")
        list_tree.heading("name", text="算法")
        list_tree.column("name", width=240, anchor=tk.W)
        list_tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        list_tree.tag_configure("removed", foreground=T_COLORS["danger"])

        # 右侧：手册内容
        right = card_frame(main, "手册详情")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))
        title_label = tk.Label(right, text="", font=("微软雅黑", 13, "bold"),
                               bg=T_COLORS["bg_card"], fg=T_COLORS["primary"], anchor="w")
        title_label.pack(fill=tk.X, padx=10, pady=(8, 2))
        text = scrolledtext.ScrolledText(right, wrap=tk.WORD, font=("微软雅黑", 10), padx=12, pady=8)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        text.configure(state="disabled")

        def show_manual(item):
            try:
                if not item:
                    return
                values = list_tree.item(item, "values")
                if not values:
                    return
                title_label.configure(text=str(values[0]))
                idx = int(item)
                content = MANUALS[idx]["content"] if idx < len(MANUALS) else REMOVED_NOTES[idx - len(MANUALS)]["content"]
                text.configure(state="normal")
                text.delete(1.0, tk.END)
                text.insert(1.0, content)
                text.configure(state="disabled")
            except Exception:
                pass

        for i, m in enumerate(MANUALS):
            list_tree.insert("", "end", iid=str(i), values=(m["name"],))
        for j, r in enumerate(REMOVED_NOTES):
            iid = str(len(MANUALS) + j)
            list_tree.insert("", "end", iid=iid, values=(r["name"],), tags=("removed",))
        list_tree.bind("<<TreeviewSelect>>", lambda e: show_manual(list_tree.selection()[0] if list_tree.selection() else None))
        if list_tree.get_children():
            list_tree.selection_set(list_tree.get_children()[0])
            show_manual(list_tree.get_children()[0])

    # ========== 马尔可夫状态转移分析 ==========

    def open_regime_analysis(self):
        """状态转移分析（马尔可夫情景分析辅助层）"""
        if self.data is None or len(self.data) < 12:
            messagebox.showwarning("警告", "请先加载数据")
            return
        try:
            ts = self.prepare_time_series()
            result = analyze_regimes(ts)
            if "error" in result:
                messagebox.showerror("错误", str(result["error"]))
                return

            win = tk.Toplevel(self.root)
            win.title("状态转移分析（马尔可夫情景分析）")
            win.geometry("880x600")
            win.configure(bg=T_COLORS["bg_window"])
            win.transient(self.root)

            info = card_frame(win, "分析摘要")
            info.pack(fill=tk.X, padx=12, pady=(12, 6))
            cur = result["current_state"]
            ss = result["steady_state"]
            tk.Label(info, text=f"当前状态：{cur} ｜ 状态频率：回落 {result['state_freq']['回落']:.1%} / "
                                f"平稳 {result['state_freq']['平稳']:.1%} / 增长 {result['state_freq']['增长']:.1%}",
                     bg=T_COLORS["bg_card"], fg=T_COLORS["text_main"]).pack(anchor="w", padx=8, pady=2)
            tk.Label(info, text=f"稳态分布：回落 {ss['回落']:.1%} / 平稳 {ss['平稳']:.1%} / 增长 {ss['增长']:.1%}",
                     bg=T_COLORS["bg_card"], fg=T_COLORS["text_sub"]).pack(anchor="w", padx=8, pady=(0, 4))
            tk.Label(info, text="说明：按月度环比增速划分状态（>+1% 增长，<-1% 回落）。本分析作为生产保障情景判断的辅助参考，"
                                "不直接改变预测主路径（客观评估结论，详见评估报告）。",
                     bg=T_COLORS["bg_card"], fg=T_COLORS["text_sub"]).pack(anchor="w", padx=8, pady=(0, 6))

            mid = tk.Frame(win, bg=T_COLORS["bg_window"])
            mid.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

            # 左：转移矩阵
            mat_card = card_frame(mid, "状态转移概率矩阵")
            mat_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            mat_tree = ttk.Treeview(mat_card, columns=("to", "p0", "p1", "p2"), show="headings", height=4, style="Modern.Treeview")
            for c, label in (("to", "当前\\下一"), ("p0", "回落"), ("p1", "平稳"), ("p2", "增长")):
                mat_tree.heading(c, text=label)
                mat_tree.column(c, width=90, anchor=tk.CENTER)
            mat_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
            P = result["transition_matrix"]
            names = ["回落", "平稳", "增长"]
            for i in range(3):
                mat_tree.insert("", "end", values=(names[i], f"{P[i][0]:.2f}", f"{P[i][1]:.2f}", f"{P[i][2]:.2f}"))

            # 右：未来状态概率图
            fig_card = card_frame(mid, "未来 12 个月状态概率")
            fig_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))
            fig, ax = plt.subplots(figsize=(5.2, 3.2))
            canvas = FigureCanvasTkAgg(fig, master=fig_card)
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
            dist = result["forecast_distribution"]
            months = result["month_labels"]
            x = list(range(len(months)))
            ax.stackplot(x, [d[0] for d in dist], [d[1] for d in dist], [d[2] for d in dist],
                         labels=names, colors=[T_COLORS["danger"], T_COLORS["accent"], T_COLORS["primary_light"]], alpha=0.85)
            ax.set_xlabel("未来月份", fontsize=9)
            ax.set_ylabel("概率", fontsize=9)
            ax.legend(loc="upper right", fontsize=8)
            ax.grid(alpha=0.25)
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            messagebox.showerror("错误", f"状态转移分析失败: {str(e)}")

    def update_status(self, message):
        """更新状态栏"""
        self.status_bar.config(text=f"状态: {message}")


def main():
    """主函数"""
    try:
        import faulthandler

        with open(_early_log_path(), "a", encoding="utf-8") as f:
            faulthandler.enable(file=f, all_threads=True)
    except Exception:
        pass

    log_path = None
    try:
        log_path = configure_logging()
    except Exception:
        pass

    ok, missing = check_dependencies()
    if not ok:
        if getattr(sys, "frozen", False):
            try:
                tmp = tk.Tk()
                tmp.withdraw()
                messagebox.showerror(
                    "依赖缺失",
                    "检测到缺少依赖库：\n"
                    + ", ".join(missing)
                    + "\n\n当前为已打包程序，无法在运行时自动安装依赖。\n"
                    + "请重新安装/更新安装包，或联系发布方。",
                )
                tmp.destroy()
            except Exception:
                pass
            return
        try:
            tmp = tk.Tk()
            tmp.withdraw()
            ask = messagebox.askyesno(
                "依赖缺失",
                "检测到缺少依赖库：\n"
                + ", ".join(missing)
                + "\n\n是否现在自动安装依赖？\n"
                + "（可能需要几分钟）",
            )
            tmp.destroy()
            if not ask:
                return

            win = tk.Tk()
            win.title("正在安装依赖")
            win.geometry("520x160")
            win.resizable(False, False)
            info = tk.Label(win, text="正在安装依赖，请稍候…", anchor="w", justify=tk.LEFT)
            info.pack(fill=tk.X, padx=12, pady=(14, 8))
            detail = tk.Label(
                win,
                text="将执行：python -m pip install -r requirements.txt",
                anchor="w",
                justify=tk.LEFT,
                fg="#555",
            )
            detail.pack(fill=tk.X, padx=12, pady=(0, 10))
            bar = ttk.Progressbar(win, mode="indeterminate")
            bar.pack(fill=tk.X, padx=12, pady=(0, 12))
            bar.start(12)

            def _worker():
                code = 1
                try:
                    req_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
                    p = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", req_path],
                        capture_output=True,
                        text=True,
                    )
                    code = int(p.returncode)
                    if p.stdout:
                        logging.info(p.stdout)
                    if p.stderr:
                        logging.warning(p.stderr)
                except Exception:
                    logging.exception("自动安装依赖失败")
                    code = 1

                def _done():
                    try:
                        bar.stop()
                    except Exception:
                        pass
                    if code == 0:
                        messagebox.showinfo("成功", "依赖安装完成，即将重启应用。")
                        try:
                            win.destroy()
                        except Exception:
                            pass
                        os.execv(sys.executable, [sys.executable] + sys.argv)
                    else:
                        msg = "依赖安装失败。\n\n请手动执行：python -m pip install -r requirements.txt"
                        if log_path:
                            msg += f"\n\n日志位置：{log_path}"
                        messagebox.showerror("失败", msg)
                        try:
                            win.destroy()
                        except Exception:
                            pass

                try:
                    win.after(0, _done)
                except Exception:
                    pass

            threading.Thread(target=_worker, daemon=True).start()
            win.mainloop()
        except Exception:
            pass
        return

    global pd, np, plt, FigureCanvasTkAgg
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    try:
        mpl.rcParams["font.sans-serif"] = [
            "Microsoft YaHei",
            "SimHei",
            "PingFang SC",
            "WenQuanYi Micro Hei",
            "Arial Unicode MS",
        ]
        mpl.rcParams["axes.unicode_minus"] = False
    except Exception:
        pass

    try:
        from capm.single_instance import acquire_single_instance_mutex

        if os.name == "nt":
            if not acquire_single_instance_mutex("CAPM_PASSENGER_FORECAST_SINGLE_INSTANCE"):
                if _try_activate_existing_window():
                    return
                tmp = tk.Tk()
                tmp.withdraw()
                choice = messagebox.askyesnocancel(
                    "提示",
                    "检测到应用已在运行中，但未找到可见窗口。\n\n"
                    "是：尝试激活已运行窗口\n"
                    "否：强制启动新实例\n"
                    "取消：退出",
                )
                tmp.destroy()
                if choice is True:
                    _try_activate_existing_window()
                    return
                if choice is None:
                    return
                logging.warning("用户选择强制启动新实例")
    except Exception:
        pass

    try:
        root = tk.Tk()
        app = FinalForecastApp(root)
        _bring_window_to_front(root)
        root.mainloop()
    except Exception:
        logging.exception("应用启动失败")
        try:
            tmp = tk.Tk()
            tmp.withdraw()
            msg = "应用启动失败"
            if log_path:
                msg += f"\n\n日志位置：{log_path}"
            messagebox.showerror("错误", msg)
            tmp.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    main()
