from __future__ import annotations

from manim import DOWN, UP, FadeIn, FadeOut, Scene, VGroup

from manim.components.pipeline import pipe_row
from manim.components.theme import THEME, label, rt


class SummaryScene(Scene):
    def construct(self):
        title = label("总结：一条可解释的预测流水线", font_size=46, color=THEME.text, weight="BOLD").to_edge(UP)
        steps = ["数据", "时间序列", "模型", "节假日", "增长率", "输出"]
        row = pipe_row(steps, width=2.2, height=0.9, title_size=26).scale(0.95).next_to(title, DOWN, buff=0.55)

        takeaway = label("教学重点：每一步都能定位到代码函数与可视化结果", font_size=28, color=THEME.muted).next_to(row, DOWN, buff=0.6)

        self.play(FadeIn(title, shift=DOWN * 0.2), FadeIn(row, shift=DOWN * 0.1), run_time=rt(0.8))
        for b in row:
            self.play(b.pulse_anim(color=THEME.accent, run_time=0.45))
        self.play(FadeIn(takeaway, shift=DOWN * 0.1), run_time=rt(0.6))
        self.wait(rt(0.8))
        self.play(FadeOut(VGroup(title, row, takeaway)), run_time=rt(0.6))
