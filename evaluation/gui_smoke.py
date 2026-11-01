# -*- coding: utf-8 -*-
"""GUI 冒烟 + 回归验收：实例化主窗口，交叉验证 V1.4 四个已报告缺陷。

用法（项目根目录）: python -m evaluation.gui_smoke

验收项：
  ① 导入：按列名取列，self.data 与表格同源，不再出现 Length of values 错位
  ② 模型切换：手点即手动，四模型确实产生不同结果，标题读实际模型
  ③ 增长率：负值可调；"强制校准"开关开/关结果不同，且校准后年度总量达标
  ④ 窗口自适应：弹窗几何随屏幕比例与 ui_scale 放大，管理控制台不再固定 920px

说明: 通过 main() 同款延迟导入注入全局 pd/np/plt，模拟真实启动链路。
"""

from __future__ import annotations

import os
import sys

REAL_XLSX = os.path.join("旅客运输量预测", "昆明本站预测报告", "海系昆明旅客运输总量（含8L）.xlsx")
EXPECTED_2025_TOTAL = 4093897


def _install_messagebox_stub(mod):
    """把 messagebox 换成记录器：模态弹窗会让无头运行卡死。"""
    records = []

    class _Stub:
        @staticmethod
        def showerror(title, message="", **kwargs):
            records.append(("error", title, message))

        @staticmethod
        def showwarning(title, message="", **kwargs):
            records.append(("warning", title, message))

        @staticmethod
        def showinfo(title, message="", **kwargs):
            records.append(("info", title, message))

        @staticmethod
        def askyesno(*args, **kwargs):
            return False

        @staticmethod
        def askokcancel(*args, **kwargs):
            return False

    _Stub.records = records
    mod.messagebox = _Stub
    return records


def _annual_total(app):
    return int(round(sum(float(row["旅客运输量"]) for row in app.forecast_data)))


def _check_import(app, pd):
    """① 真实 5 列文件：按列名取 旅客运输量，表格与 self.data 同源。"""
    assert os.path.exists(REAL_XLSX), f"缺少验收数据: {REAL_XLSX}"
    raw = pd.read_excel(REAL_XLSX)
    assert raw.shape[1] == 5, f"验收文件应为 5 列, 实际 {raw.shape}"

    rows, dropped = app._read_history_rows(raw)
    assert not dropped, f"不应有被跳过的行: {dropped}"
    assert len(rows) == 24, f"应解析 24 条, 实际 {len(rows)}"

    # 走真实提交路径：表格与 self.data 由同一份 rows 生成
    count, dropped = app.import_history_file(REAL_XLSX)
    assert count == 24 and not dropped, f"导入结果异常: {count}, {dropped}"
    assert list(app.data.columns) == ["年份", "月份", "旅客运输量"], f"列名异常: {list(app.data.columns)}"
    total_2025 = int(app.data[app.data["年份"] == 2025]["旅客运输量"].sum())
    assert total_2025 == EXPECTED_2025_TOTAL, f"取错列(应为旅客运输量而非 非8L): 2025 合计 {total_2025}"
    assert int(app.data[(app.data["年份"] == 2025) & (app.data["月份"] == 12)]["旅客运输量"].iloc[0]) == 191128

    items = app.history_tree.get_children()
    assert len(items) == 24, f"历史表格行数异常: {len(items)}"
    shown = app.history_tree.item(items[0], "values")
    assert int(shown[0]) == int(app.data.iloc[0]["年份"])
    assert int(str(shown[2]).replace(",", "")) == int(app.data.iloc[0]["旅客运输量"]), \
        f"表格显示与 self.data 不一致: {shown} vs {app.data.iloc[0].to_dict()}"

    ts = app.prepare_time_series()  # 旧实现在这里抛 Length of values (23)/(24)
    assert len(ts) == 24, f"时间序列长度异常: {len(ts)}"
    print(f"[OK] ① 导入: 24 行, 2025 合计 {total_2025:,}, 表格与 self.data 同源, 时间序列 {len(ts)} 个月")


def _check_model_switch(app, root):
    """② 手动模式严格生效：实际使用模型 == 单选钮，且四组结果确实不同。"""
    totals = {}
    for key in ("ensemble", "hw", "sarima", "kalman"):
        app._on_model_radio(key)
        assert app.model_mode_var.get() == "manual", "点选模型后应自动切换到手动模式"
        app.run_forecast()
        root.update_idletasks()
        assert getattr(app, "last_used_model", None) == key, \
            f"实际使用模型 {getattr(app, 'last_used_model', None)} != 所选 {key}（自动推荐仍在覆盖？）"
        totals[key] = _annual_total(app)

    assert len(set(totals.values())) >= 3, f"切换模型后结果几乎相同: {totals}"
    assert app._model_display_name("hw") == "Holt-Winters"
    print(f"[OK] ② 模型切换: {totals}")


def _check_growth_switch(app, root):
    """③ 增长率：不点“保存配置”也应实时生效；开关前后结果必须不同。"""
    app._on_model_radio("hw")
    app.config_vars["annual_growth_rate"].set(-10.0)  # 故意不写 self.growth_cfg
    app.growth_apply_var.set(False)
    app.run_forecast()
    root.update_idletasks()
    total_off = _annual_total(app)
    assert not getattr(app, "growth_calibrated", False), "关闭开关时不应校准"

    app.growth_apply_var.set(True)
    app.run_forecast()
    root.update_idletasks()
    total_on = _annual_total(app)
    target = EXPECTED_2025_TOTAL * 0.9  # -10% 单年目标
    assert getattr(app, "growth_calibrated", False), "开启开关后应执行强制校准"
    assert abs(total_on - target) <= target * 0.02, f"校准未达标: {total_on:,} vs 目标 {target:,.0f}"
    assert abs(total_on - total_off) > 1000, "增长率开关前后结果相同（仍未接入）"

    # 附带修复：干预引擎下春运天数列不再恒为 0
    feb_rows = [row for row in app.forecast_data if int(row["月份"]) == 2]
    assert feb_rows and feb_rows[0]["春运天数"] > 0, f"春运天数列仍为 0: {feb_rows[:1]}"
    print(f"[OK] ③ 增长率: 关闭 {total_off:,} → 强制 -10% {total_on:,} (目标 {target:,.0f})；"
          f"春运天数 {feb_rows[0]['春运天数']} 天")


def _check_geometry(CAPM, tk, root, app):
    """④ 弹窗几何：屏幕比例 + ui_scale 生效，管理控制台不再恒为 920px。"""
    top = tk.Toplevel(root)
    top.withdraw()
    screen_w = top.winfo_screenwidth()
    screen_h = top.winfo_screenheight()
    cap_w = max(680, int(screen_w * 0.92) - 48)
    cap_h = max(520, int(screen_h * 0.92) - 48)

    _, width, height = CAPM._scaled_dialog_geometry(
        top, 920, 720, parent=root, min_w=680, min_h=520,
        ui_scale=1.0, ratio_w=0.62, ratio_h=0.72,
    )
    expect_w = min(max(680, 920, int(screen_w * 0.62)), cap_w)
    expect_h = min(max(520, 720, int(screen_h * 0.72)), cap_h)
    assert width == expect_w, f"宽度应随屏幕比例放大: {width} != {expect_w}"
    assert height == expect_h, f"高度应随屏幕比例放大: {height} != {expect_h}"
    assert width > 920 or screen_w * 0.62 <= 920, f"大屏上仍固定在 920px: {width}"

    _, small_w, _ = CAPM._scaled_dialog_geometry(top, 400, 300, min_w=320, min_h=240, ui_scale=1.0)
    _, big_w, _ = CAPM._scaled_dialog_geometry(top, 400, 300, min_w=320, min_h=240, ui_scale=1.4)
    assert big_w > small_w, f"ui_scale 未参与尺寸计算: {small_w} -> {big_w}"
    top.destroy()

    app.open_admin_console()
    root.update_idletasks()
    root.update()
    consoles = [w for w in root.winfo_children()
                if isinstance(w, tk.Toplevel) and "管理控制台" in w.title()]
    assert consoles, "管理控制台未打开"
    actual = consoles[0].winfo_width()
    assert actual >= expect_w - 2, f"管理控制台实际宽度 {actual} < 期望 {expect_w}"
    assert getattr(app, "admin_resizer", None) is not None, "admin_tree 未挂 ColumnResizer"
    consoles[0].destroy()
    root.update_idletasks()
    print(f"[OK] ④ 几何: 屏 {screen_w}x{screen_h} → 控制台 {actual}px, ui_scale 放大 {small_w}->{big_w}")


def _check_auto_mode(app, root, pd):
    """⑥ 自动推荐：24 个月时优雅跳过并保留用户选择；36 个月时才真正推荐。"""
    # (a) 只有 24 个月（回测需 36 个月）：不得静默退回融合模型
    app._on_model_radio("hw")
    app.model_mode_var.set("auto")
    app.run_forecast()
    root.update_idletasks()
    assert app.last_rec_info is None, "24 个月数据不应产出回测推荐"
    assert app.last_used_model == "hw", f"跳过自动推荐时应保留单选模型, 实际 {app.last_used_model}"
    assert app.auto_skip_note, "跳过自动推荐时必须给出原因"
    assert "36" in app.auto_skip_note, f"原因应包含最少月份要求: {app.auto_skip_note}"
    skipped_note = app.auto_skip_note

    # (b) 补足到 36 个月：自动推荐应产出结果并回写单选钮
    hist = app.data.copy()
    base = hist[hist["年份"] == 2025]["旅客运输量"].tolist()
    extra = pd.DataFrame([
        {"年份": 2026, "月份": m + 1, "旅客运输量": int(round(base[m] * 1.03))} for m in range(12)
    ])
    app.data = pd.concat([hist, extra], ignore_index=True)
    app.model_mode_var.set("auto")
    app.run_forecast()
    root.update_idletasks()
    assert app.last_rec_info is not None, f"36 个月数据应产出推荐: {app.auto_skip_note}"
    assert app.last_used_model == app.last_rec_info["model"]
    assert app.model_var.get() == app.last_used_model, "自动推荐未把推荐模型回写到单选钮"
    assert app.model_mode_var.get() == "auto", "自动推荐不应把模式改成手动"
    print(f"[OK] ⑥ 自动推荐: 24 个月跳过（{skipped_note}）→ 36 个月推荐 {app.last_used_model} 并回写单选钮")


def _check_config_roundtrip(app):
    """⑤ 新增配置项可往返：collect_profile_from_ui → apply_profile_to_ui。"""
    app.model_mode_var.set("manual")
    app.growth_apply_var.set(True)
    app.config_vars["annual_growth_rate"].set(-5.0)

    profile = app.collect_profile_from_ui()
    assert profile["model"].get("model_mode") == "manual", profile["model"].get("model_mode")
    assert profile["growth"].get("apply_annual_growth") is True, profile["growth"]
    assert abs(profile["growth"]["annual_growth_rate"] + 0.05) < 1e-9, profile["growth"]

    app.model_mode_var.set("auto")
    app.growth_apply_var.set(False)
    app.apply_profile_to_ui(profile)
    assert app.model_mode_var.get() == "manual"
    assert app.growth_apply_var.get() is True
    assert abs(app.config_vars["annual_growth_rate"].get() + 5.0) < 1e-9
    print("[OK] ⑤ 配置往返: model_mode=manual, apply_annual_growth=True, rate=-5.0%")


def _check_config_live(app, root):
    """⑦ 配置页任一参数改动都必须改变预测结果（不改 growth_cfg、不点保存）。"""
    # 先关闭"强制校准"，否则年度总量被校准覆盖，看不出节假日系数的效果
    app.growth_apply_var.set(False)
    app._on_model_radio("ensemble")
    app.run_forecast()
    root.update_idletasks()
    base = _annual_total(app)

    cases = {}
    app.config_vars["spring_festival_effect"].set(1.60)
    app.run_forecast()
    root.update_idletasks()
    cases["春节效应 1.15→1.60"] = _annual_total(app)

    app.config_vars["spring_festival_effect"].set(1.15)
    app.spring_before_var.set(5)
    app.spring_after_var.set(5)
    app.run_forecast()
    root.update_idletasks()
    cases["春运 15/24→5/5"] = _annual_total(app)

    app.spring_before_var.set(15)
    app.spring_after_var.set(24)
    app.config_vars["summer_vacation_effect"].set(1.50)
    app.run_forecast()
    root.update_idletasks()
    cases["暑假效应 1.10→1.50"] = _annual_total(app)

    app.config_vars["summer_vacation_effect"].set(1.10)
    app.config_vars["may_day_effect"].set(1.30)
    app.run_forecast()
    root.update_idletasks()
    cases["五一效应 1.05→1.30"] = _annual_total(app)
    app.config_vars["may_day_effect"].set(1.05)

    assert all(v != base for v in cases.values()), f"配置改动未影响预测: base={base}, {cases}"
    print(f"[OK] ⑦ 配置生效: base {base:,} → {cases}")


def _check_dialog_content(app, root, tk):
    """⑧ 弹窗内容必须完整可见：管理控制台双图不被裁、算法手册列表不截断。"""
    app.open_admin_console()
    root.update_idletasks()
    root.update()
    console = [w for w in root.winfo_children()
               if isinstance(w, tk.Toplevel) and "管理控制台" in w.title()][0]
    canvases = []

    def walk(widget):
        for child in widget.winfo_children():
            if child.winfo_class() == "Canvas":
                canvases.append(child)
            walk(child)

    walk(console)
    assert canvases, "管理控制台缺少画布"
    canvas = canvases[0]
    # 画布请求尺寸曾膨胀到 4 倍并撑爆弹窗；现在由 holder 隔离子图不应被裁
    assert canvas.winfo_height() > 200, f"预览图区过矮: {canvas.winfo_height()}"
    preview_card = canvas.master.master
    assert preview_card.winfo_reqheight() < console.winfo_height(), \
        f"预览卡片请求高度 {preview_card.winfo_reqheight()} 超过窗口 {console.winfo_height()}"
    canvas_size = (canvas.winfo_width(), canvas.winfo_height())
    app.external_mgr.load()  # 确保有两张子图
    console.destroy()
    root.update_idletasks()

    app.open_manual_viewer()
    root.update_idletasks()
    root.update()
    manual = [w for w in root.winfo_children()
              if isinstance(w, tk.Toplevel) and "手册" in w.title()][0]
    trees = []

    def walk_tree(widget):
        for child in widget.winfo_children():
            if child.winfo_class() == "Treeview":
                trees.append(child)
            walk_tree(child)

    walk_tree(manual)
    assert trees, "算法手册缺少列表"
    tree = trees[0]
    x0, x1 = tree.xview()
    assert x0 <= 0.001 and x1 >= 0.999, f"算法列表被截断（需横向滚动）: xview={tree.xview()}"
    list_width = int(tree.column("name", "width"))
    manual.destroy()
    root.update_idletasks()
    print(f"[OK] ⑧ 弹窗内容: 预览画布 {canvas_size[0]}x{canvas_size[1]}，算法列表 {list_width}px 无截断")


def _check_yoy_multi_year(app, root):
    """⑨ 年度同比目标表：两行 => 24 个月预测，且逐年复利校准到目标。"""
    app.import_history_file(REAL_XLSX)  # 重置为 24 个月（末 2025）
    for item in app.yoy_tree.get_children():
        app.yoy_tree.delete(item)
    app.yoy_tree.insert("", "end", values=(2026, "-10.00"))
    app.yoy_tree.insert("", "end", values=(2027, "5.00"))
    app._on_model_radio("hw")
    app.growth_apply_var.set(True)
    app.run_forecast()
    root.update_idletasks()

    rows = app.forecast_data
    years = sorted({int(r["年份"]) for r in rows})
    assert len(rows) == 24 and years == [2026, 2027], f"多年预测异常: {len(rows)} 行 {years}"
    base = float(EXPECTED_2025_TOTAL)
    t26 = sum(r["旅客运输量"] for r in rows if int(r["年份"]) == 2026)
    t27 = sum(r["旅客运输量"] for r in rows if int(r["年份"]) == 2027)
    tgt26 = base * 0.9
    tgt27 = tgt26 * 1.05
    assert abs(t26 - tgt26) <= tgt26 * 0.001, f"2026 未达标: {t26:,.0f} vs {tgt26:,.0f}"
    assert abs(t27 - tgt27) <= tgt27 * 0.001, f"2027 未达标: {t27:,.0f} vs {tgt27:,.0f}"
    app.growth_apply_var.set(False)
    for item in app.yoy_tree.get_children():
        app.yoy_tree.delete(item)
    app.yoy_tree.insert("", "end", values=(2026, "-10.00"))
    print(f"[OK] ⑨ 多年同比: 2026 {t26:,.0f}/{tgt26:,.0f} · 2027 {t27:,.0f}/{tgt27:,.0f}")


def main():
    sys.path.insert(0, ".")

    import warnings

    warnings.filterwarnings("ignore")

    import tkinter as tk

    import CAPM

    # 模拟 main() 的全局注入（应用 after 回调 load_sample_data 依赖这些全局名）
    import matplotlib

    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    CAPM.pd = pd
    CAPM.np = np
    CAPM.plt = plt
    CAPM.FigureCanvasTkAgg = __import__(
        "matplotlib.backends.backend_tkagg", fromlist=["FigureCanvasTkAgg"]
    ).FigureCanvasTkAgg
    # 与 main() 一致：中文字体与负号，否则截图里的中文全是方块
    matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    matplotlib.rcParams["axes.unicode_minus"] = False

    messages = _install_messagebox_stub(CAPM)

    root = tk.Tk()
    CAPM._set_window_icon(root)
    app = CAPM.FinalForecastApp(root)
    root.update_idletasks()
    root.update()

    assert hasattr(app, "kalman_weight_var"), "缺卡尔曼权重输入"
    assert hasattr(app, "kalman_auto_var"), "缺卡尔曼自动调参开关"
    assert abs(float(app.kalman_weight_var.get()) - 0.2) < 1e-9, "默认权重应为 0.2"
    assert app._active_members() == ["hw", "sarima", "kalman"], f"成员池异常: {app._active_members()}"
    assert hasattr(app, "growth_apply_var"), "缺增长率强制校准开关"
    assert app.growth_apply_var.get() is False, "增长率强制校准应默认关闭"

    _check_import(app, pd)
    _check_model_switch(app, root)
    _check_growth_switch(app, root)
    _check_geometry(CAPM, tk, root, app)
    _check_config_live(app, root)
    _check_yoy_multi_year(app, root)
    _check_auto_mode(app, root, pd)
    _check_dialog_content(app, root, tk)
    _check_config_roundtrip(app)

    errors = [m for m in messages if m[0] == "error"]
    assert not errors, f"运行期出现错误弹窗: {errors}"

    try:
        from PIL import ImageGrab

        os.makedirs("out", exist_ok=True)
        x, y = root.winfo_rootx(), root.winfo_rooty()
        img = ImageGrab.grab(bbox=(x, y, x + root.winfo_width(), y + root.winfo_height()))
        img.save("out/gui_smoke.png")
    except Exception as exc:  # 截屏失败不应阻断验收
        print(f"[WARN] 截屏失败: {exc}")

    root.update_idletasks()
    # 走正式关闭路径, 顺带验证 after 回调取消后不再刷 Tk 噪声
    app._on_close()
    print("GUI SMOKE OK")


if __name__ == "__main__":
    main()
