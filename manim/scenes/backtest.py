from __future__ import annotations

from manim import DOWN, LEFT, RIGHT, UP, FadeIn, FadeOut, Rectangle, Scene, VGroup

from manim.components.theme import THEME, label, rt


class AutoWeightBacktestScene(Scene):
    def construct(self):
        header = label("可选：自动权重（滚动回测）", font_size=42, color=THEME.text, weight="BOLD").to_edge(UP)
        desc = label("训练窗口滚动 → 预测误差对比 → 推荐融合权重", font_size=28, color=THEME.muted).next_to(header, DOWN, buff=0.25).to_edge(LEFT)

        models = ["HW", "SARIMA", "Linear"]
        errors = [6.8, 7.5, 9.2]
        bars = _error_bars(models, errors).to_edge(LEFT).shift(DOWN * 0.15)

        weights = [0.45, 0.35, 0.20]
        weight_rows = [[models[i], f"{errors[i]:.1f}%", f"{weights[i]:.2f}"] for i in range(3)]
        panel = VGroup(
            Rectangle(width=5.2, height=3.0).set_fill("#0F1624", opacity=1).set_stroke("#2B3A55", width=2),
        ).to_edge(RIGHT).shift(DOWN * 0.15)
        table = VGroup(
            label("推荐权重（示例）", font_size=26, color=THEME.text, weight="BOLD"),
            _mini_table(["模型", "回测误差", "权重"], weight_rows),
        ).arrange(DOWN, buff=0.25).move_to(panel.get_center())
        panel.add(table)

        self.play(FadeIn(header, shift=DOWN * 0.2), FadeIn(desc, shift=DOWN * 0.2), run_time=rt(0.7))
        self.play(FadeIn(bars), FadeIn(panel), run_time=rt(0.9))
        self.wait(rt(0.9))
        self.play(FadeOut(VGroup(header, desc, bars, panel)), run_time=rt(0.6))


def _error_bars(names: list[str], values: list[float]) -> VGroup:
    bars = []
    max_v = max(values) if values else 1.0
    for i, n in enumerate(names):
        w = 4.2
        h = 0.45
        bg = Rectangle(width=w, height=h).set_fill("#121826", opacity=1).set_stroke("#2B3A55", width=1.5)
        fill_w = max(0.0001, w * (values[i] / max_v))
        fg = Rectangle(width=fill_w, height=h).set_fill(THEME.model, opacity=0.9).set_stroke(width=0)
        fg.align_to(bg, LEFT)
        name = label(n, font_size=22, color=THEME.text)
        val = label(f"{values[i]:.1f}%", font_size=22, color=THEME.muted)
        bars.append(VGroup(name, bg, fg, val).arrange(RIGHT, buff=0.25))
    return VGroup(*bars).arrange(DOWN, buff=0.25, aligned_edge=LEFT)


def _mini_table(headers: list[str], rows: list[list[str]]) -> VGroup:
    from manim.components.table import DataTable

    return DataTable(headers=headers, rows=rows, col_widths=[1.4, 1.6, 1.2]).scale(0.9)
