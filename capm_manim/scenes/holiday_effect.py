from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import calendar as _cal
from datetime import datetime, timedelta

from manim import DOWN, LEFT, RIGHT, UP, FadeIn, FadeOut, Rectangle, Scene, VGroup

from capm_manim.components.table import DataTable
from capm_manim.components.theme import THEME, label, rt


def _spring_festival_date(year: int) -> datetime:
    defaults = {2025: datetime(2025, 1, 29), 2026: datetime(2026, 2, 17), 2027: datetime(2027, 2, 6)}
    if year in defaults:
        return defaults[year]
    base = defaults[2025]
    return base + timedelta(days=(year - 2025) * 11)


def _spring_span(year: int, before_days: int, after_days: int):
    sf = _spring_festival_date(year)
    return sf - timedelta(days=int(before_days)), sf + timedelta(days=int(after_days))


def _month_spring_days(year: int, month: int, before_days: int, after_days: int) -> int:
    start, end = _spring_span(year, before_days, after_days)
    dim = _cal.monthrange(year, month)[1]
    return sum(1 for d in range(1, dim + 1) if start <= datetime(year, month, d) <= end)


def _month_effect(year: int, month: int, before_days: int, after_days: int, spring_effect: float, months_in_scope=(1, 2, 3)) -> float:
    if month not in months_in_scope:
        return 1.0
    spring_days = _month_spring_days(year, month, before_days, after_days)
    if spring_days <= 0:
        return 1.0
    dim = _cal.monthrange(year, month)[1]
    return 1.0 + (spring_days / dim) * (float(spring_effect) - 1.0)


class HolidayEffectScene(Scene):
    def construct(self):
        header = label("节假日/春运效应：用系数修正预测", font_size=42, color=THEME.text, weight="BOLD").to_edge(UP)
        desc = label("对每个月：预测值 × 效应系数（春运按覆盖天数占比插值）", font_size=28, color=THEME.muted).next_to(header, DOWN, buff=0.25).to_edge(LEFT)

        year = 2026
        before_days, after_days = 15, 24
        spring_effect = 1.15

        rows = []
        bars = VGroup()
        for m in [1, 2, 3]:
            dim = _cal.monthrange(year, m)[1]
            spring_days = _month_spring_days(year, m, before_days, after_days)
            coef = _month_effect(year, m, before_days, after_days, spring_effect)
            rows.append([f"{year}-{m:02d}", f"{spring_days}/{dim}", f"{coef:.3f}"])

            w = 3.1
            h = 0.45
            bg = Rectangle(width=w, height=h).set_fill("#121826", opacity=1).set_stroke("#2B3A55", width=1.5)
            fill_w = max(0.0001, w * (spring_days / dim))
            fg = Rectangle(width=fill_w, height=h).set_fill(THEME.post, opacity=0.9).set_stroke(width=0)
            fg.align_to(bg, LEFT)
            title = label(f"{m:02d}月", font_size=22, color=THEME.text)
            coef_t = label(f"×{coef:.3f}", font_size=22, color=THEME.muted)
            bars.add(VGroup(title, bg, fg, coef_t).arrange(RIGHT, buff=0.25))

        bars.arrange(DOWN, buff=0.25, aligned_edge=LEFT).next_to(desc, DOWN, buff=0.5).to_edge(LEFT)
        table = DataTable(headers=["月份", "春运覆盖", "效应系数"], rows=rows, col_widths=[2.2, 2.2, 2.1]).scale(0.95).to_edge(RIGHT).shift(DOWN * 0.4)
        formula = label("系数 = 1 + (春运天数/月天数)·(spring_effect − 1)", font_size=26, color=THEME.muted).next_to(bars, DOWN, buff=0.45).to_edge(LEFT)

        self.play(FadeIn(header, shift=DOWN * 0.2), FadeIn(desc, shift=DOWN * 0.2), run_time=rt(0.7))
        self.play(FadeIn(bars), FadeIn(table), FadeIn(formula), run_time=rt(0.9))
        self.wait(rt(1.0))
        self.play(FadeOut(VGroup(header, desc, bars, table, formula)), run_time=rt(0.6))
