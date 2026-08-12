from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from manim import DOWN, RIGHT, UP, Arrow, FadeIn, FadeOut, Scene, VGroup

from capm_manim.components.pipeline import PipelineBlock
from capm_manim.components.progress import ProgressBar
from capm_manim.components.theme import THEME, label, rt


class ArchitectureScene(Scene):
    def construct(self):
        header = label("程序工作流程（run_forecast 主链路）", font_size=42, color=THEME.text, weight="BOLD").to_edge(UP)

        steps = [
            PipelineBlock("数据进入", subtitle="Excel导入/手动录入", width=2.55),
            PipelineBlock("时间序列", subtitle="prepare_time_series", width=2.55),
            PipelineBlock("模型预测", subtitle="Linear/HW/SARIMA/融合", width=2.75),
            PipelineBlock("节假日修正", subtitle="春运/暑运/五一/国庆", width=2.75),
            PipelineBlock("增长率校准", subtitle="年度总量缩放", width=2.55),
            PipelineBlock("结果输出", subtitle="表格/图表/导出Excel", width=2.75),
        ]
        row = VGroup(*steps).arrange(RIGHT, buff=0.35).scale(0.86).next_to(header, DOWN, buff=0.55)
        arrows = VGroup(*[Arrow(steps[i].get_right(), steps[i + 1].get_left(), buff=0.15, max_tip_length_to_length_ratio=0.15, color="#2B3A55") for i in range(len(steps) - 1)])

        bar = ProgressBar(width=12.0, height=0.2, value=0.0).to_edge(DOWN).shift(UP * 0.35)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=rt(0.6))
        self.play(FadeIn(row), FadeIn(arrows), FadeIn(bar), run_time=rt(0.8))

        for i, step in enumerate(steps):
            self.play(step.activate_anim(color=THEME.accent, run_time=0.35), bar.animate_to((i + 1) / len(steps)).set_run_time(rt(0.35)))
            self.play(step.deactivate_anim(run_time=0.2))

        self.wait(rt(0.4))
        self.play(FadeOut(VGroup(header, row, arrows, bar)), run_time=rt(0.6))
