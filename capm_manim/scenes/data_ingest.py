from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from manim import DOWN, LEFT, RIGHT, UP, FadeIn, FadeOut, Scene, VGroup

from capm_manim.assets.sample_data import sample_history
from capm_manim.components.charts import ChartSpec, LineChart
from capm_manim.components.table import DataTable
from capm_manim.components.theme import THEME, label, rt


class DataIngestScene(Scene):
    def construct(self):
        header = label("数据进入：Excel导入/手动录入 → 历史月度序列", font_size=42, color=THEME.text, weight="BOLD").to_edge(UP)
        desc = label("统一三列：年份 / 月份 / 旅客运输量", font_size=28, color=THEME.muted).next_to(header, DOWN, buff=0.25).to_edge(LEFT)

        hist = sample_history()
        rows = []
        for i in range(6):
            y, m = hist.x_labels[i].split("-")
            rows.append([y, m, f"{hist.values[i]:.0f}"])

        table = DataTable(headers=["年份", "月份", "旅客运输量"], rows=rows, col_widths=[1.5, 1.2, 2.2]).scale(1.05)
        table.to_edge(LEFT).shift(DOWN * 0.25)

        chart = LineChart(hist.values, hist.x_labels, color=THEME.data, spec=ChartSpec(width=7.2, height=3.2, x_step=6), title="历史数据 → 时间序列")
        chart.to_edge(RIGHT).shift(DOWN * 0.15)

        self.play(FadeIn(header, shift=DOWN * 0.2), FadeIn(desc, shift=DOWN * 0.2), run_time=rt(0.7))
        self.play(FadeIn(table), FadeIn(chart), run_time=rt(0.9))
        self.wait(rt(0.9))
        self.play(FadeOut(VGroup(header, desc, table, chart)), run_time=rt(0.6))
