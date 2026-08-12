from __future__ import annotations

from manim import DOWN, LEFT, ORIGIN, RIGHT, AnimationGroup, Rectangle, VGroup

from capm_manim.components.theme import THEME, label, rt


class PipelineBlock(VGroup):
    def __init__(
        self,
        title: str,
        width: float = 2.6,
        height: float = 1.0,
        fill: str = "#121826",
        stroke: str = "#2B3A55",
        title_size: float = 26,
        subtitle: str | None = None,
        subtitle_size: float = 18,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.box = Rectangle(width=width, height=height).set_fill(fill, opacity=1).set_stroke(stroke, width=2)
        self.title = label(title, font_size=title_size, color=THEME.text).move_to(self.box.get_center())

        items = [self.title]
        if subtitle:
            self.subtitle = label(subtitle, font_size=subtitle_size, color=THEME.muted)
            items = [self.title, self.subtitle]
            VGroup(*items).arrange(DOWN, buff=0.12).move_to(self.box.get_center())
        else:
            self.subtitle = None

        self.add(self.box, *items)

    def set_active(self, color: str = THEME.accent, stroke_width: float = 4):
        self.box.set_stroke(color, width=stroke_width)
        return self

    def set_inactive(self):
        self.box.set_stroke("#2B3A55", width=2)
        return self

    def activate_anim(self, color: str = THEME.accent, run_time: float = 0.4):
        return self.box.animate.set_stroke(color, width=4).set_run_time(rt(run_time))

    def deactivate_anim(self, run_time: float = 0.25):
        return self.box.animate.set_stroke("#2B3A55", width=2).set_run_time(rt(run_time))

    def pulse_anim(self, color: str = THEME.accent, run_time: float = 0.6):
        return AnimationGroup(
            self.box.animate.set_stroke(color, width=5).set_run_time(rt(run_time / 2)),
            self.box.animate.set_stroke(color, width=3).set_run_time(rt(run_time / 2)),
            lag_ratio=0.0,
        )


def pipe_row(titles: list[str], buff: float = 0.35, **kwargs) -> VGroup:
    blocks = [PipelineBlock(t, **kwargs) for t in titles]
    group = VGroup(*blocks).arrange(RIGHT, buff=buff)
    group.move_to(ORIGIN)
    return group


def pipe_col(titles: list[str], buff: float = 0.3, **kwargs) -> VGroup:
    blocks = [PipelineBlock(t, **kwargs) for t in titles]
    group = VGroup(*blocks).arrange(DOWN, buff=buff, aligned_edge=LEFT)
    group.move_to(ORIGIN)
    return group

