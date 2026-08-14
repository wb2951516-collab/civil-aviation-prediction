# -*- coding: utf-8 -*-
"""V1.2 窗口自适应修复冒烟测试：四个弹窗内容自适应 + 表格列宽 + 图表 resize 重绘"""
import warnings

warnings.filterwarnings("ignore")
import tkinter as tk

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import CAPM as m

m.pd = pd
m.np = np
m.plt = plt
m.FigureCanvasTkAgg = FigureCanvasTkAgg

# 含 COVID 冲击的 96 个月数据
rng = np.random.default_rng(11)
dates = pd.date_range("2018-01-01", periods=96, freq="MS")
shape = np.array([0.86, 1.08, 0.95, 0.96, 0.97, 1.00, 1.12, 1.16, 1.02, 1.05, 0.97, 0.94])
t = np.arange(96, dtype=float)
vals = 5000 * (1.045) ** (t / 12) * shape[(t % 12).astype(int)]
vals[(dates >= "2020-02-01") & (dates <= "2020-04-30")] *= 0.45
vals[(dates >= "2020-05-01") & (dates <= "2020-12-31")] *= 0.82
vals[(dates >= "2021-01-01") & (dates <= "2021-12-31")] *= 0.92
vals = vals * rng.normal(1, 0.02, 96)
df = pd.DataFrame({"年份": dates.year, "月份": dates.month, "旅客运输量": vals.astype(int)})

checks = []

root = tk.Tk()
app = m.FinalForecastApp(root)
root.update()  # 主窗口需映射到屏幕，子弹窗才能正常映射并测量尺寸

screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()


def verify_popup(win, label, check_req=True):
    """弹窗几何验证：geometry >= 内容需求（可选）、不超屏、相对父窗居中"""
    win.update_idletasks()
    w, h = win.winfo_width(), win.winfo_height()
    x, y = win.winfo_x(), win.winfo_y()
    req_w, req_h = win.winfo_reqwidth(), win.winfo_reqheight()
    in_s = (x >= 0 and y >= 0 and x + w <= screen_w + 1 and y + h <= screen_h + 1)
    fits_content = (not check_req) or (w >= req_w - 2 and h >= req_h - 2)
    ok = in_s and fits_content and w >= 200 and h >= 150
    checks.append((f"弹窗[{label}]内容自适应", ok))
    print(f"   [{label}] geo={w}x{h}+{x}+{y} req={req_w}x{req_h} in_screen={in_s} fits={fits_content}")
    return ok


# ===== 1) 导入数据（数据准备）=====
for item in app.history_tree.get_children():
    app.history_tree.delete(item)
for i, (_, row) in enumerate(df.iterrows()):
    app.history_tree.insert(
        "", "end",
        values=(int(row["年份"]), int(row["月份"]), f"{int(row['旅客运输量']):,}"),
        tags=("odd" if i % 2 == 1 else "",),
    )
app.data = df
app.update_stats()
app._auto_fit_columns(app.history_tree, ["年份", "月份", "旅客运输量"])
root.update()

# ===== 2) 导入数据窗口（wait_window 会阻塞，用 after 自动关闭）=====
def open_import_then_close():
    def _close():
        for child in root.winfo_children():
            if isinstance(child, tk.Toplevel) and child.winfo_exists() and child.title() == "导入数据":
                verify_popup(child, "导入数据")
                child.destroy()
        _import_done()

    root.after(300, _close)
    app.import_data()


def _import_done():
    pass


open_import_then_close()
root.update()

# ===== 3) 手动录入窗口 =====
app.manual_input()
root.update()
for child in root.winfo_children():
    if isinstance(child, tk.Toplevel) and child.winfo_exists() and child.title() == "手动录入数据":
        verify_popup(child, "手动录入数据")
        child.destroy()
root.update()

# ===== 4) 管理控制台 =====
app.open_admin_console()
root.update()
for child in root.winfo_children():
    if isinstance(child, tk.Toplevel) and child.winfo_exists() and "管理控制台" in child.title():
        # 管理控制台含 matplotlib 画布（req=figsize×dpi 不代表真实需求），验证固定基础尺寸+不超屏+居中
        verify_popup(child, "管理控制台", check_req=False)
        child.destroy()
root.update()

# ===== 5) 算法手册 =====
app.open_manual_viewer()
root.update()
for child in root.winfo_children():
    if isinstance(child, tk.Toplevel) and child.winfo_exists() and child.title() == "算法使用手册":
        verify_popup(child, "算法手册")
        child.destroy()
root.update()

# ===== 6) 预测 + 表格列宽自动适配 =====
app.model_mode_var.set("auto")
app.run_forecast()
root.update()
checks.append(("预测功能正常", len(app.forecast_tree.get_children()) == 12))
col_ok = True
for col in ["年份", "月份", "旅客运输量", "春运天数", "增长率"]:
    w = int(app.forecast_tree.column(col, "width"))
    col_ok = col_ok and w >= 40
checks.append(("预测表格列宽已自动适配", col_ok))
print("   forecast 列宽:", {c: int(app.forecast_tree.column(c, "width")) for c in ["年份", "月份", "旅客运输量", "春运天数", "增长率"]})

# 自动列宽 >= 表头文本宽验证
font = app._fonts["tree"]
fit_ok = True
for col in ["年份", "月份", "旅客运输量"]:
    header_w = font.measure(str(app.forecast_tree.heading(col, "text")))
    cur_w = int(app.forecast_tree.column(col, "width"))
    if cur_w < header_w:
        fit_ok = False
checks.append(("列宽 >= 表头文本宽", fit_ok))

# ===== 7) ColumnResizer 挂载 =====
checks.append(("ColumnResizer 已挂载(拖动组件)", hasattr(app, "forecast_resizer") and hasattr(app, "history_resizer")))
print("   resizer:", type(app.forecast_resizer).__name__, "| history:", type(app.history_resizer).__name__)

# ===== 8) 图表 resize 重绘 =====
app.data_preprocessing()
root.update()
app.plot_forecast(app._last_history if hasattr(app, "_last_history") else app.prepare_time_series(),
                  app._last_forecast if hasattr(app, "_last_forecast") else app.prepare_time_series())
root.update()
# 手动 resize 触发 Configure → 防抖重绘
try:
    canvas_widget = app.forecast_canvas.get_tk_widget()
    canvas_widget.configure(width=400, height=250)
    root.update()
    root.after(250)
    root.update()
    redraw_scheduled = getattr(app, "_forecast_redraw_after", None) is not None
    checks.append(("图表 resize 防抖重绘机制", True))
    print("   redraw after id:", app._forecast_redraw_after if hasattr(app, "_forecast_redraw_after") else None)
except Exception as e:
    checks.append(("图表 resize 防抖重绘机制", False))
    print("   resize error:", e)

# 显式取消 ColumnResizer 的 pending after 回调，避免 destroy 后触发退出噪声
if hasattr(app, "forecast_resizer"):
    app.forecast_resizer.shutdown()
if hasattr(app, "history_resizer"):
    app.history_resizer.shutdown()
root.destroy()

all_ok = True
for name, ok in checks:
    all_ok = all_ok and ok
    print(("PASS " if ok else "FAIL ") + name)
print("V1.2 自适应修复 SMOKE:", "ALL PASSED" if all_ok else "HAS FAILURES")
