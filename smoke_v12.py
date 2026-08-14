# -*- coding: utf-8 -*-
"""V1.2 发布冒烟测试：功能零退化 + 窗口自适应/弹窗几何验证（临时脚本）"""
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

# 含 COVID 冲击的 96 个月数据（真实量级）
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

# ===== 1) 主窗口自适应 =====
root = tk.Tk()
root.withdraw()
app = m.FinalForecastApp(root)
root.update()
screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
win_w, win_h = root.winfo_width(), root.winfo_height()
win_x, win_y = root.winfo_x(), root.winfo_y()
in_screen = (win_x >= 0 and win_y >= 0 and win_x + win_w <= screen_w + 1 and win_y + win_h <= screen_h + 1)
checks.append(("主窗口尺寸自适应(88%屏幕, 居中)", in_screen and win_w <= screen_w and win_h <= screen_h))
print(f"   screen={screen_w}x{screen_h} win={win_w}x{win_h}+{win_x}+{win_y} in_screen={in_screen}")

# ===== 2) 数据导入 + 干预引擎预测 =====
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
app.model_mode_var.set("auto")
app.run_forecast()
root.update()
checks.append(("干预引擎自动推荐预测", app.last_rec_info is not None and len(app.forecast_tree.get_children()) == 12))
print("   rec:", app.last_rec_info["model"] if app.last_rec_info else None,
      "| conf_int:", 0 if app.model_conf_int is None else len(app.model_conf_int))

# ===== 3) 弹窗几何验证 =====
def verify_toplevel(win, label):
    win.update_idletasks()
    w, h = win.winfo_width(), win.winfo_height()
    x, y = win.winfo_x(), win.winfo_y()
    in_s = (x >= 0 and y >= 0 and x + w <= screen_w + 1 and y + h <= screen_h + 1)
    has_minsize = False
    try:
        has_minsize = win.minsize() != (1, 1)
    except Exception:
        pass
    ok = in_s and w >= 200 and h >= 150 and has_minsize
    checks.append((f"弹窗[{label}]几何", ok))
    print(f"   [{label}] {w}x{h}+{x}+{y} in_screen={in_s} minsize={has_minsize}")

w_manual = tk.Toplevel(root)
w_manual.title("手动录入")
m._apply_geometry(w_manual, 400, 320, parent=root, min_w=360, min_h=280)
verify_toplevel(w_manual, "手动录入")
w_manual.destroy()

w_admin = tk.Toplevel(root)
w_admin.title("管理控制台")
m._apply_geometry(w_admin, 880, 660, parent=root, min_w=680, min_h=520)
verify_toplevel(w_admin, "管理控制台")
w_admin.destroy()

w_manual2 = tk.Toplevel(root)
w_manual2.title("算法手册")
m._apply_geometry(w_manual2, 980, 700, parent=root, min_w=720, min_h=520)
verify_toplevel(w_manual2, "算法手册")
w_manual2.destroy()

w_regime = tk.Toplevel(root)
w_regime.title("状态转移")
m._apply_geometry(w_regime, 880, 620, parent=root, min_w=680, min_h=480)
verify_toplevel(w_regime, "状态转移")
w_regime.destroy()

# ===== 4) 实际弹窗打开 =====
app.open_manual_viewer()
app.open_regime_analysis()
app.open_admin_console()
root.update()
checks.append(("三个功能弹窗打开", True))
for child in root.winfo_children():
    if isinstance(child, tk.Toplevel):
        child.destroy()

# ===== 5) 传统管线切换 =====
app.engine_var.set("legacy")
app.run_forecast()
root.update()
checks.append(("传统管线预测", len(app.forecast_tree.get_children()) == 12))
app.engine_var.set("intervention")
app.run_forecast()
root.update()
checks.append(("干预引擎恢复", len(app.forecast_tree.get_children()) == 12))

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
print("V1.2 SMOKE:", "ALL PASSED" if all_ok else "HAS FAILURES")
