from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from manim import DOWN, LEFT, RIGHT, UP, FadeIn, FadeOut, Rectangle, Scene, VGroup

from capm_manim.assets.sample_data import sample_ensemble
from capm_manim.components.table import DataTable
from capm_manim.components.theme import THEME, label, rt


class OutputAndExportScene(Scene):
    def construct(self):
        header = label("结果生成与导出：表格、图表、Excel报告", font_size=42, color=THEME.text, weight="BOLD").to_edge(UP)
        desc = label("生成 forecast_data → 导出预测结果/增长分析/完整报告", font_size=28, color=THEME.muted).next_to(header, DOWN, buff=0.25).to_edge(LEFT)

        fc = sample_ensemble(weights=(0.4, 0.3, 0.3))
        rows = [[fc.x_labels[i], f"{fc.values[i]:.0f}", "(春运天数)", "(效应系数)"] for i in range(6)]

        table = DataTable(headers=["月份", "预测值", "春运天数", "节假日系数"], rows=rows, col_widths=[2.0, 1.8, 2.0, 2.0]).scale(0.95)
        table.to_edge(LEFT).shift(DOWN * 0.25)

        tabs = _tabs(["说明", "预测结果", "年度汇总", "增长分析", "春运分析", "配置信息"], active=1).to_edge(RIGHT).shift(UP * 0.35)

        file_box = Rectangle(width=5.2, height=3.2).set_fill("#0F1624", opacity=1).set_stroke("#2B3A55", width=2)
        file_title = label("导出文件：CAPM_预测报告.xlsx", font_size=24, color=THEME.text)
        file_meta = label("多Sheet结构，便于教学与复盘", font_size=22, color=THEME.muted)
        export_panel = VGroup(file_box, VGroup(file_title, file_meta).arrange(DOWN, buff=0.2).move_to(file_box.get_center())).to_edge(RIGHT).shift(DOWN * 0.55)

        self.play(FadeIn(header, shift=DOWN * 0.2), FadeIn(desc, shift=DOWN * 0.2), run_time=rt(0.7))
        self.play(FadeIn(table), FadeIn(tabs), FadeIn(export_panel), run_time=rt(0.9))
        self.wait(rt(1.0))
        self.play(FadeOut(VGroup(header, desc, table, tabs, export_panel)), run_time=rt(0.6))


def _tabs(names: list[str], active: int = 0) -> VGroup:
    tabs = []
    for i, n in enumerate(names):
        w = 1.7 if len(n) <= 3 else 2.1
        h = 0.5
        fill = "#121826" if i == active else "#0F1624"
        stroke = THEME.accent if i == active else "#2B3A55"
        rect = Rectangle(width=w, height=h).set_fill(fill, opacity=1).set_stroke(stroke, width=2)
        t = label(n, font_size=20, color=THEME.text if i == active else THEME.muted)
        t.scale_to_fit_width(w - 0.25)
        t.move_to(rect.get_center())
        tabs.append(VGroup(rect, t))
    return VGroup(*tabs).arrange(DOWN, buff=0.12)
