from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from manim import DOWN, LEFT, RIGHT, UP, FadeIn, FadeOut, Scene, VGroup

from capm_manim.components.charts import YearlyBars
from capm_manim.components.theme import THEME, label, rt


class GrowthAdjustmentScene(Scene):
    def construct(self):
        header = label("年度增长率校准：按年总量做缩放", font_size=42, color=THEME.text, weight="BOLD").to_edge(UP)
        desc = label("目标年度总量 = 基准总量 × (1 + 增长率)^n；当年各月同比例缩放", font_size=28, color=THEME.muted).next_to(header, DOWN, buff=0.25).to_edge(LEFT)

        years = [2026, 2027]
        original_totals = [8600, 9050]
        growth_rate = 0.027
        base_total = 8200
        target_totals = [base_total * ((1 + growth_rate) ** (i + 1)) for i in range(len(years))]

        left_title = label("模型输出（原始年度总量）", font_size=26, color=THEME.muted)
        right_title = label("增长率目标（年度总量）", font_size=26, color=THEME.muted)

        left = VGroup(left_title, YearlyBars(years, original_totals, color=THEME.model, width=6.0, height=3.2)).arrange(DOWN, buff=0.25).to_edge(LEFT).shift(DOWN * 0.2)
        right = VGroup(right_title, YearlyBars(years, target_totals, color=THEME.post, width=6.0, height=3.2)).arrange(DOWN, buff=0.25).to_edge(RIGHT).shift(DOWN * 0.2)

        factor = target_totals[0] / original_totals[0]
        factor_text = label(f"缩放因子（2026）= 目标/原始 = {factor:.3f}", font_size=28, color=THEME.muted).to_edge(LEFT).next_to(left, DOWN, buff=0.45)

        self.play(FadeIn(header, shift=DOWN * 0.2), FadeIn(desc, shift=DOWN * 0.2), run_time=rt(0.7))
        self.play(FadeIn(left), FadeIn(right), run_time=rt(0.9))
        self.play(FadeIn(factor_text, shift=UP * 0.1), run_time=rt(0.6))
        self.wait(rt(1.0))
        self.play(FadeOut(VGroup(header, desc, left, right, factor_text)), run_time=rt(0.6))
