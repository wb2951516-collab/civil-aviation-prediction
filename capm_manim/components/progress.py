from __future__ import annotations

from manim import LEFT, Rectangle, VGroup

from capm_manim.components.theme import THEME


class ProgressBar(VGroup):
    def __init__(
        self,
        width: float = 10.5,
        height: float = 0.18,
        bg_color: str = "#1F2A3A",
        fill_color: str = THEME.accent,
        value: float = 0.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.width = float(width)
        self.height = float(height)
        self.bg = Rectangle(width=self.width, height=self.height).set_fill(bg_color, opacity=1).set_stroke(width=0)
        self.fill = Rectangle(width=0.0001, height=self.height).set_fill(fill_color, opacity=1).set_stroke(width=0)
        self.fill.align_to(self.bg, LEFT)
        self.add(self.bg, self.fill)
        self.set_value(value)

    def set_value(self, value: float):
        v = max(0.0, min(1.0, float(value)))
        new_w = max(0.0001, self.width * v)
        self.fill.become(Rectangle(width=new_w, height=self.height).set_fill(self.fill.get_fill_color(), opacity=1).set_stroke(width=0))
        self.fill.align_to(self.bg, LEFT)
        return self

    def animate_to(self, value: float):
        v = max(0.0, min(1.0, float(value)))
        new_w = max(0.0001, self.width * v)
        rect = Rectangle(width=new_w, height=self.height).set_fill(self.fill.get_fill_color(), opacity=1).set_stroke(width=0)
        rect.align_to(self.bg, LEFT)
        return self.fill.animate.become(rect)

