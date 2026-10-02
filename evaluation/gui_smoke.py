# -*- coding: utf-8 -*-
"""GUI 冒烟测试：实例化主窗口、校验 V1.4 卡尔曼控件、截屏留档。

用法（项目根目录）: python -m evaluation.gui_smoke
说明: 通过 main() 同款延迟导入注入全局 pd/np/plt，模拟真实启动链路。
"""

from __future__ import annotations


def main():
    import sys

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

    root = tk.Tk()
    CAPM._set_window_icon(root)
    app = CAPM.FinalForecastApp(root)
    root.update_idletasks()
    root.update()

    assert hasattr(app, "kalman_weight_var"), "缺卡尔曼权重输入"
    assert hasattr(app, "kalman_auto_var"), "缺卡尔曼自动调参开关"
    assert abs(float(app.kalman_weight_var.get()) - 0.2) < 1e-9, "默认权重应为 0.2"
    assert app._active_members() == ["hw", "sarima", "kalman"], f"成员池异常: {app._active_members()}"

    from PIL import ImageGrab

    x, y = root.winfo_rootx(), root.winfo_rooty()
    img = ImageGrab.grab(bbox=(x, y, x + root.winfo_width(), y + root.winfo_height()))
    img.save("out/gui_smoke.png")

    root.destroy()
    print("GUI SMOKE OK")


if __name__ == "__main__":
    main()
