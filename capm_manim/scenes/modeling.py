from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from manim import DOWN, LEFT, RIGHT, UP, Axes, FadeIn, FadeOut, Line, Scene, VGroup

from capm_manim.assets.sample_data import sample_ensemble, sample_model_components
from capm_manim.components.progress import ProgressBar
from capm_manim.components.theme import THEME, label, rt


class ModelingScene(Scene):
    def construct(self):
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
        self.play(FadeIn(axes), FadeIn(xticks), FadeIn(legend), FadeIn(bar), run_time=rt(0.8))

        self.play(FadeIn(g_lin), bar.animate_to(0.25).set_run_time(rt(0.5)))
        self.play(FadeIn(g_hw), bar.animate_to(0.50).set_run_time(rt(0.5)))
        self.play(FadeIn(g_sar), bar.animate_to(0.70).set_run_time(rt(0.5)))
        self.play(FadeIn(g_ens), bar.animate_to(1.00).set_run_time(rt(0.6)))

        formula = label("融合：ŷ = w₁·HW + w₂·SARIMA + w₃·Linear（权重归一化）", font_size=28, color=THEME.muted).to_edge(LEFT).next_to(header, DOWN, buff=0.4)
        self.play(FadeIn(formula, shift=UP * 0.12), run_time=rt(0.6))
        self.wait(rt(0.9))
        self.play(FadeOut(VGroup(header, axes, xticks, legend, bar, g_lin, g_hw, g_sar, g_ens, formula)), run_time=rt(0.6))


def _legend_item(color: str, text: str):
    line = Line(LEFT * 0.35, RIGHT * 0.35).set_stroke(color, width=6)
    t = label(text, font_size=22, color=THEME.muted)
    return VGroup(line, t).arrange(RIGHT, buff=0.2)
