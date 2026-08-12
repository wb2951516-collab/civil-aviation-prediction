from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from manim import DOWN, FadeIn, FadeOut, Scene, VGroup

from capm_manim.components.theme import THEME, label, rt


class IntroScene(Scene):
    def construct(self):
        title = label("民航旅客运输量预测：从数据到结果", font_size=50, color=THEME.text, weight="BOLD")
        subtitle = label("教学动画：程序原理与输出结果生成过程", font_size=28, color=THEME.muted).next_to(title, DOWN, buff=0.25)
        group = VGroup(title, subtitle).arrange(DOWN, buff=0.25)
        self.play(FadeIn(group, shift=DOWN * 0.2), run_time=rt(0.9))
        self.wait(rt(0.6))
        self.play(FadeOut(group), run_time=rt(0.6))
