from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import calendar as _cal
from datetime import datetime, timedelta

from manim import DOWN, LEFT, RIGHT, UP, Arrow, Axes, FadeIn, FadeOut, Line, Rectangle, Scene, VGroup

from capm_manim.assets.sample_data import sample_ensemble, sample_model_components
from capm_manim.components.charts import YearlyBars
from capm_manim.components.pipeline import PipelineBlock, pipe_row
from capm_manim.components.progress import ProgressBar
from capm_manim.components.table import DataTable
from capm_manim.components.theme import THEME, label, rt


class CAPMTutorial(Scene):
    def construct(self):
        self._intro()
        self._architecture()
        self._modeling()
        self._holiday_effect()
        self._growth_adjustment()
        self._output_export()
        self._summary()

    def _intro(self):
        title = label("民航旅客运输量预测：从数据到结果", font_size=50, color=THEME.text, weight="BOLD").to_edge(UP)
        subtitle = label("教学动画：程序原理与输出结果生成过程", font_size=28, color=THEME.muted).next_to(title, DOWN, buff=0.2)
        self.play(FadeIn(title, shift=DOWN * 0.2), FadeIn(subtitle, shift=DOWN * 0.2), run_time=rt(0.8))
        self.wait(rt(0.3))
        self.play(FadeOut(VGroup(title, subtitle)), run_time=rt(0.4))

    def _architecture(self):
        header = label("程序工作流程（run_forecast 主链路）", font_size=42, color=THEME.text, weight="BOLD").to_edge(UP)
        steps = [
            PipelineBlock("数据进入", subtitle="Excel/录入", width=2.45),
            PipelineBlock("时间序列", subtitle="ts(月频)", width=2.3),
            PipelineBlock("模型预测", subtitle="3模型/融合", width=2.5),
            PipelineBlock("节假日修正", subtitle="春运等", width=2.5),
            PipelineBlock("增长率校准", subtitle="年度缩放", width=2.45),
            PipelineBlock("结果输出", subtitle="表格/导出", width=2.5),
        ]
        row = VGroup(*steps).arrange(RIGHT, buff=0.35).scale(0.9).next_to(header, DOWN, buff=0.55)
        arrows = VGroup(*[Arrow(steps[i].get_right(), steps[i + 1].get_left(), buff=0.15, max_tip_length_to_length_ratio=0.15, color="#2B3A55") for i in range(len(steps) - 1)])
        bar = ProgressBar(width=12.0, height=0.2, value=0.0).to_edge(DOWN).shift(UP * 0.35)

        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=rt(0.6))
        self.play(FadeIn(row), FadeIn(arrows), FadeIn(bar), run_time=rt(0.8))
        for i, step in enumerate(steps):
            self.play(step.activate_anim(color=THEME.accent, run_time=0.28), bar.animate_to((i + 1) / len(steps)).set_run_time(rt(0.28)))
            self.play(step.deactivate_anim(run_time=0.18))
        self.wait(rt(0.3))
        self.play(FadeOut(VGroup(header, row, arrows, bar)), run_time=rt(0.5))

    def _modeling(self):
        header = label("核心预测：三模型并行 → 加权融合", font_size=42, color=THEME.text, weight="BOLD").to_edge(UP)
        months = [f"{m:02d}" for m in range(1, 13)]
        linear, hw, sarima = sample_model_components()
        ens = sample_ensemble(weights=(0.4, 0.3, 0.3))
        y_max = max(linear.values + hw.values + sarima.values + ens.values) * 1.15

        axes = Axes(
            x_range=[0, 11, 1],
            y_range=[0, y_max, y_max / 5],
            x_length=11.5,
            y_length=4.0,
            tips=False,
            axis_config={"include_numbers": False, "stroke_color": "#2B3A55"},
        ).to_edge(DOWN).shift(UP * 0.35)

        xticks = VGroup(*[label(months[i], font_size=18, color=THEME.muted).next_to(axes.c2p(i, 0), DOWN, buff=0.15) for i in range(0, 12, 2)])

        def line_for(vals, color: str, width: float):
            return axes.plot_line_graph(
                x_values=list(range(12)),
                y_values=[float(v) for v in vals],
                line_color=color,
                add_vertex_dots=False,
                stroke_width=width,
            )

        g_lin = line_for(linear.values, "#5CDBD3", 3)
        g_hw = line_for(hw.values, "#B37FEB", 3)
        g_sar = line_for(sarima.values, "#FF85C0", 3)
        g_ens = line_for(ens.values, THEME.output, 5)

        legend = VGroup(
            _legend_item("#5CDBD3", "Linear"),
            _legend_item("#B37FEB", "Holt-Winters"),
            _legend_item("#FF85C0", "SARIMA"),
            _legend_item(THEME.output, "Ensemble"),
        ).arrange(DOWN, buff=0.15, aligned_edge=LEFT).to_edge(RIGHT).shift(UP * 0.4)
        bar = ProgressBar(width=11.5, height=0.2, value=0.0).next_to(axes, UP, buff=0.25).align_to(axes, LEFT)

        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=rt(0.6))
        self.play(FadeIn(axes), FadeIn(xticks), FadeIn(legend), FadeIn(bar), run_time=rt(0.7))
        self.play(FadeIn(g_lin), bar.animate_to(0.25).set_run_time(rt(0.45)))
        self.play(FadeIn(g_hw), bar.animate_to(0.50).set_run_time(rt(0.45)))
        self.play(FadeIn(g_sar), bar.animate_to(0.70).set_run_time(rt(0.45)))
        self.play(FadeIn(g_ens), bar.animate_to(1.00).set_run_time(rt(0.55)))

        formula = label("融合：ŷ = w₁·HW + w₂·SARIMA + w₃·Linear（权重归一化）", font_size=28, color=THEME.muted).to_edge(LEFT).next_to(header, DOWN, buff=0.4)
        self.play(FadeIn(formula, shift=UP * 0.12), run_time=rt(0.5))
        self.wait(rt(0.4))
        self.play(FadeOut(VGroup(header, axes, xticks, legend, bar, g_lin, g_hw, g_sar, g_ens, formula)), run_time=rt(0.5))

    def _holiday_effect(self):
        header = label("节假日/春运效应：用系数修正预测", font_size=42, color=THEME.text, weight="BOLD").to_edge(UP)
        desc = label("逐月：预测值 × 效应系数（春运按覆盖天数占比插值）", font_size=28, color=THEME.muted).next_to(header, DOWN, buff=0.25).to_edge(LEFT)

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

        self.play(FadeIn(header, shift=DOWN * 0.2), FadeIn(desc, shift=DOWN * 0.2), run_time=rt(0.6))
        self.play(FadeIn(bars), FadeIn(table), FadeIn(formula), run_time=rt(0.8))
        self.wait(rt(0.4))
        self.play(FadeOut(VGroup(header, desc, bars, table, formula)), run_time=rt(0.5))

    def _growth_adjustment(self):
        header = label("年度增长率校准：按年总量做缩放", font_size=42, color=THEME.text, weight="BOLD").to_edge(UP)
        desc = label("目标年度总量 = 基准总量 × (1 + 增长率)^n", font_size=28, color=THEME.muted).next_to(header, DOWN, buff=0.25).to_edge(LEFT)

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
        factor_text = label(f"缩放因子（2026）= {factor:.3f}", font_size=28, color=THEME.muted).to_edge(LEFT).next_to(left, DOWN, buff=0.45)

        self.play(FadeIn(header, shift=DOWN * 0.2), FadeIn(desc, shift=DOWN * 0.2), run_time=rt(0.6))
        self.play(FadeIn(left), FadeIn(right), run_time=rt(0.8))
        self.play(FadeIn(factor_text, shift=UP * 0.1), run_time=rt(0.5))
        self.wait(rt(0.4))
        self.play(FadeOut(VGroup(header, desc, left, right, factor_text)), run_time=rt(0.5))

    def _output_export(self):
        header = label("结果生成与导出：表格、图表、Excel报告", font_size=42, color=THEME.text, weight="BOLD").to_edge(UP)
        desc = label("forecast_data → 多Sheet Excel 报告", font_size=28, color=THEME.muted).next_to(header, DOWN, buff=0.25).to_edge(LEFT)

        fc = sample_ensemble(weights=(0.4, 0.3, 0.3))
        rows = [[fc.x_labels[i], f"{fc.values[i]:.0f}", "(春运天数)", "(系数)"] for i in range(6)]
        table = DataTable(headers=["月份", "预测值", "春运天数", "节假日系数"], rows=rows, col_widths=[2.0, 1.8, 2.0, 2.0]).scale(0.95).to_edge(LEFT).shift(DOWN * 0.25)

        tabs = _tabs(["说明", "预测结果", "年度汇总", "增长分析", "春运分析", "配置信息"], active=1).to_edge(RIGHT).shift(UP * 0.35)
        file_box = Rectangle(width=5.2, height=3.2).set_fill("#0F1624", opacity=1).set_stroke("#2B3A55", width=2)
        file_title = label("导出文件：CAPM_预测报告.xlsx", font_size=24, color=THEME.text)
        file_meta = label("可用于教学展示与复盘", font_size=22, color=THEME.muted)
        export_panel = VGroup(file_box, VGroup(file_title, file_meta).arrange(DOWN, buff=0.2).move_to(file_box.get_center())).to_edge(RIGHT).shift(DOWN * 0.55)

        self.play(FadeIn(header, shift=DOWN * 0.2), FadeIn(desc, shift=DOWN * 0.2), run_time=rt(0.6))
        self.play(FadeIn(table), FadeIn(tabs), FadeIn(export_panel), run_time=rt(0.8))
        self.wait(rt(0.4))
        self.play(FadeOut(VGroup(header, desc, table, tabs, export_panel)), run_time=rt(0.5))

    def _summary(self):
        title = label("总结：一条可解释的预测流水线", font_size=46, color=THEME.text, weight="BOLD").to_edge(UP)
        row = pipe_row(["数据", "时间序列", "模型", "节假日", "增长率", "输出"], width=2.2, height=0.9, title_size=26).scale(0.95).next_to(title, DOWN, buff=0.6)
        takeaway = label("每一步都能对应到代码函数与可视化结果", font_size=28, color=THEME.muted).next_to(row, DOWN, buff=0.6)
        self.play(FadeIn(title, shift=DOWN * 0.2), FadeIn(row, shift=DOWN * 0.1), run_time=rt(0.8))
        for b in row:
            self.play(b.pulse_anim(color=THEME.accent, run_time=0.45))
        self.play(FadeIn(takeaway, shift=DOWN * 0.1), run_time=rt(0.6))
        self.wait(rt(0.8))
        self.play(FadeOut(VGroup(title, row, takeaway)), run_time=rt(0.6))


def _legend_item(color: str, text: str):
    line = Line(LEFT * 0.35, RIGHT * 0.35).set_stroke(color, width=6)
    t = label(text, font_size=22, color=THEME.muted)
    return VGroup(line, t).arrange(RIGHT, buff=0.2)


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
