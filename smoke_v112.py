# -*- coding: utf-8 -*-
"""V1.1.2 干预引擎融入后 GUI 冒烟测试（临时脚本）"""
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

root = tk.Tk()
root.withdraw()
app = m.FinalForecastApp(root)
root.update()  # 真实启动流程

# 导入数据（模拟用户导入）
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

checks = []
# 1) 干预引擎（默认）自动推荐预测
app.model_mode_var.set("auto")
app.run_forecast()
root.update()
checks.append(("干预引擎自动推荐", app.last_rec_info is not None and len(app.forecast_tree.get_children()) == 12))
print("   rec:", app.last_rec_info["model"] if app.last_rec_info else None,
      "| weights:", app.last_rec_info["weights"] if app.last_rec_info else None)
print("   conf_int:", 0 if app.model_conf_int is None else len(app.model_conf_int),
      "| model_results:", list(app.model_results.keys()))

# 2) 手动 SARIMA（干预引擎）
app.model_mode_var.set("manual")
app.model_var.set("sarima")
app.run_forecast()
root.update()
checks.append(("干预SARIMA预测", len(app.forecast_tree.get_children()) == 12))

# 3) 切换传统管线（legacy）
app.engine_var.set("legacy")
app.model_var.set("ensemble")
app.run_forecast()
root.update()
checks.append(("传统管线预测", len(app.forecast_tree.get_children()) == 12))

# 4) 切回干预引擎
app.engine_var.set("intervention")
app.run_forecast()
root.update()
checks.append(("干预引擎恢复", len(app.forecast_tree.get_children()) == 12))

# 5) 窗口完整性
app.open_manual_viewer()
app.open_regime_analysis()
app.open_admin_console()
root.update()
checks.append(("三窗口打开", True))

root.destroy()
for name, ok in checks:
    print(("PASS " if ok else "FAIL ") + name)
print("GUI SMOKE:", "ALL PASSED" if all(ok for _, ok in checks) else "HAS FAILURES")
