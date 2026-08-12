"""统一现代化主题系统（原生 ttk 实现，无第三方依赖）。

设计语言：
- 主色：航空蓝（深蓝 #1B4F8A → 亮蓝 #2F7DD1 渐变语义），传达专业与可靠
- 底色：浅灰 #F3F5F9（窗口）/ 白 #FFFFFF（卡片与表格）
- 强调：成功绿 #1A7F37、警示橙 #B7791F、风险红 #C0392B
- 字体：微软雅黑（统一字号规范，支持 DPI 缩放）
- 覆盖控件：Button / Notebook / Treeview / LabelFrame / Combobox /
  Checkbutton / Radiobutton / Scale / Scrollbar / Progressbar / Entry
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# ---- 调色板 ----
COLORS = {
    "primary": "#1B4F8A",        # 主色（航空蓝-深）
    "primary_light": "#2F7DD1",  # 主色（航空蓝-亮）
    "primary_hover": "#2563A9",
    "accent": "#E8B23A",         # 强调金
    "bg_window": "#F3F5F9",      # 窗口背景
    "bg_card": "#FFFFFF",        # 卡片/内容背景
    "bg_hover": "#EAF1FA",       # 悬停底色
    "border": "#D8DEE8",         # 边框
    "text_main": "#1F2937",      # 主文本
    "text_sub": "#6B7280",       # 次级文本
    "text_on_primary": "#FFFFFF",
    "success": "#1A7F37",
    "warning": "#B7791F",
    "danger": "#C0392B",
    "row_alt": "#F7FAFD",        # 表格斑马纹
    "row_spring": "#FEF3E2",     # 春运高亮
    "selected": "#DCE9F8",       # 表格选中
}

FONT_FAMILY = "微软雅黑"
FONT_SIZES = {"small": 9, "normal": 10, "large": 12, "title": 16}


def apply_theme(root: tk.Tk) -> ttk.Style:
    """应用现代化主题到 Tk 根窗口，返回配置好的 Style。"""
    style = ttk.Style(root)

    try:
        style.theme_use("clam")  # clam 主题对颜色/内边距控制最好
    except Exception:
        pass

    c = COLORS
    # ---------- 按钮 ----------
    style.configure(
        "Modern.TButton",
        font=(FONT_FAMILY, FONT_SIZES["normal"]),
        background=c["primary"],
        foreground=c["text_on_primary"],
        borderwidth=0,
        padding=(14, 7),
        relief="flat",
        focusthickness=0,
    )
    style.map(
        "Modern.TButton",
        background=[("active", c["primary_hover"]), ("disabled", "#A9BFD9"), ("pressed", c["primary"])],
        foreground=[("disabled", "#E6EDF5")],
    )

    style.configure(
        "Secondary.TButton",
        font=(FONT_FAMILY, FONT_SIZES["normal"]),
        background=c["bg_card"],
        foreground=c["primary"],
        borderwidth=1,
        padding=(14, 6),
        relief="flat",
        focusthickness=0,
    )
    style.map(
        "Secondary.TButton",
        background=[("active", c["bg_hover"]), ("pressed", c["border"])],
        bordercolor=[("active", c["primary_light"]), ("!active", c["border"])],
    )

    style.configure(
        "Danger.TButton",
        font=(FONT_FAMILY, FONT_SIZES["normal"]),
        background=c["bg_card"],
        foreground=c["danger"],
        borderwidth=1,
        padding=(14, 6),
        relief="flat",
        focusthickness=0,
    )
    style.map("Danger.TButton", background=[("active", "#FBE9E9")], bordercolor=[("!active", c["border"]), ("active", c["danger"])])

    style.configure(
        "Toolbar.TButton",
        font=(FONT_FAMILY, FONT_SIZES["small"]),
        background=c["bg_window"],
        foreground=c["text_main"],
        borderwidth=1,
        padding=(10, 5),
        relief="flat",
        focusthickness=0,
    )
    style.map("Toolbar.TButton", background=[("active", c["bg_hover"])], bordercolor=[("!active", c["border"]), ("active", c["primary_light"])])

    # ---------- Notebook ----------
    style.configure(
        "TNotebook",
        background=c["bg_window"],
        borderwidth=0,
        tabmargins=(6, 6, 6, 0),
    )
    style.configure(
        "TNotebook.Tab",
        font=(FONT_FAMILY, FONT_SIZES["normal"]),
        background="#E3E8F0",
        foreground=c["text_sub"],
        padding=(18, 8),
        borderwidth=0,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", c["bg_card"])],
        foreground=[("selected", c["primary"])],
    )

    # ---------- 卡片式 LabelFrame ----------
    style.configure(
        "Card.TLabelframe",
        background=c["bg_card"],
        bordercolor=c["border"],
        borderwidth=1,
        relief="solid",
        padding=10,
    )
    style.configure(
        "Card.TLabelframe.Label",
        background=c["bg_card"],
        foreground=c["primary"],
        font=(FONT_FAMILY, FONT_SIZES["large"], "bold"),
    )

    # ---------- Treeview ----------
    style.configure(
        "Modern.Treeview",
        font=(FONT_FAMILY, FONT_SIZES["normal"]),
        background=c["bg_card"],
        fieldbackground=c["bg_card"],
        foreground=c["text_main"],
        borderwidth=0,
        rowheight=32,
    )
    style.map(
        "Modern.Treeview",
        background=[("selected", c["selected"])],
        foreground=[("selected", c["text_main"])],
    )
    style.configure(
        "Modern.Treeview.Heading",
        font=(FONT_FAMILY, FONT_SIZES["normal"], "bold"),
        background="#E8EDF5",
        foreground=c["text_main"],
        borderwidth=0,
        padding=(8, 7),
        relief="flat",
    )
    style.map("Modern.Treeview.Heading", background=[("active", "#DDE6F2")])

    # ---------- Combobox / Spinbox / Entry ----------
    for widget in ("TCombobox", "TSpinbox", "TEntry"):
        style.configure(
            widget,
            font=(FONT_FAMILY, FONT_SIZES["normal"]),
            fieldbackground=c["bg_card"],
            background=c["bg_card"],
            foreground=c["text_main"],
            bordercolor=c["border"],
            arrowsize=14,
            padding=4,
        )
        style.map(widget, bordercolor=[("focus", c["primary_light"])], fieldbackground=[("readonly", c["bg_card"])])

    # ---------- Checkbutton / Radiobutton ----------
    for widget in ("TCheckbutton", "TRadiobutton"):
        style.configure(
            widget,
            font=(FONT_FAMILY, FONT_SIZES["normal"]),
            background=c["bg_window"],
            foreground=c["text_main"],
            indicatorcolor=c["bg_card"],
            bordercolor=c["border"],
            focuscolor=c["primary"],
        )
        style.map(widget, indicatorcolor=[("selected", c["primary_light"]), ("pressed", c["primary_light"])], background=[("active", c["bg_window"])])

    # ---------- Scale / Scrollbar / Progressbar ----------
    style.configure(
        "Modern.Horizontal.TScale",
        background=c["bg_window"],
        troughcolor="#D8DEE8",
        bordercolor=c["border"],
        lightcolor=c["primary_light"],
        darkcolor=c["primary"],
        gripcount=0,
    )
    style.configure(
        "Modern.Vertical.TScrollbar",
        background="#C6CEDC",
        troughcolor=c["bg_window"],
        bordercolor=c["bg_window"],
        arrowsize=0,
        relief="flat",
    )
    style.configure(
        "Modern.Horizontal.TScrollbar",
        background="#C6CEDC",
        troughcolor=c["bg_window"],
        bordercolor=c["bg_window"],
        arrowsize=0,
        relief="flat",
    )
    style.map("Modern.Vertical.TScrollbar", background=[("active", "#A8B4C8")])
    style.map("Modern.Horizontal.TScrollbar", background=[("active", "#A8B4C8")])
    style.configure(
        "Modern.Horizontal.TProgressbar",
        background=c["primary_light"],
        troughcolor="#D8DEE8",
        bordercolor=c["bg_window"],
        lightcolor=c["primary_light"],
        darkcolor=c["primary"],
    )

    # ---------- 窗口级字体与背景 ----------
    root.option_add("*Font", (FONT_FAMILY, FONT_SIZES["normal"]))
    root.configure(bg=c["bg_window"])
    return style


def card_frame(parent, title: str = "") -> ttk.LabelFrame:
    """便捷创建卡片式分组容器。"""
    if title:
        frame = ttk.LabelFrame(parent, text=title, style="Card.TLabelframe")
    else:
        frame = ttk.LabelFrame(parent, style="Card.TLabelframe")
    return frame
