from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from manim import DOWN, LEFT, RIGHT, UP, Axes, DecimalNumber, Dot, Line, Rectangle, VGroup

from capm_manim.components.theme import THEME, label


@dataclass(frozen=True)
class ChartSpec:
    width: float = 7.0
    height: float = 3.0
    x_step: int = 1
    y_tick_count: int = 4


def _nice_max(values: Sequence[float]) -> float:
    v = max([float(x) for x in values] + [1.0])
    if v <= 0:
        return 1.0
    mag = 10 ** int(len(str(int(v))) - 1)
    top = ((v // mag) + 1) * mag
    return float(top)


class LineChart(VGroup):
    def __init__(
        self,
        values: Sequence[float],
        x_labels: Sequence[str],
        color: str = THEME.data,
        spec: ChartSpec = ChartSpec(),
        title: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.values = [float(v) for v in values]
        self.x_labels = list(x_labels)
        self.spec = spec

        y_max = _nice_max(self.values)
        self.axes = Axes(
            x_range=[0, max(1, len(self.values) - 1), 1],
            y_range=[0, y_max, y_max / max(1, spec.y_tick_count)],
            x_length=spec.width,
            y_length=spec.height,
            tips=False,
            axis_config={"include_numbers": False, "stroke_color": "#2B3A55"},
        )

        self.graph = self.axes.plot_line_graph(
            x_values=list(range(len(self.values))),
            y_values=self.values,
            line_color=color,
            add_vertex_dots=False,
            stroke_width=4,
        )

        self.dots = VGroup(*[Dot(self.axes.c2p(i, v), radius=0.045, color=color) for i, v in enumerate(self.values)])

        self.x_tick_labels = VGroup()
        step = max(1, int(spec.x_step))
        for i in range(0, len(self.x_labels), step):
            t = label(self.x_labels[i], font_size=18, color=THEME.muted)
            t.next_to(self.axes.c2p(i, 0), DOWN, buff=0.15)
            self.x_tick_labels.add(t)

        self.add(self.axes, self.graph, self.dots, self.x_tick_labels)

        if title:
            self.title = label(title, font_size=26, color=THEME.text)
            self.title.next_to(self.axes, UP, buff=0.2).align_to(self.axes, LEFT)
            self.add(self.title)
        else:
            self.title = None

    def point_marker(self, i: int, color: str = THEME.accent) -> VGroup:
        idx = max(0, min(len(self.values) - 1, int(i)))
        v = self.values[idx]
        dot = Dot(self.axes.c2p(idx, v), radius=0.07, color=color)
        num = DecimalNumber(v, num_decimal_places=0, color=THEME.text, font_size=26).next_to(dot, UP, buff=0.12)
        return VGroup(dot, num)


class YearlyBars(VGroup):
    def __init__(
        self,
        years: Sequence[int],
        values: Sequence[float],
        color: str = THEME.post,
        width: float = 7.0,
        height: float = 3.0,
        y_unit: float | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.years = [int(y) for y in years]
        self.values = [float(x) for x in values]
        self.width = float(width)
        self.height = float(height)

        max_v = _nice_max(self.values)
        n = max(1, len(self.values))
        gap = self.width * 0.06
        bar_w = (self.width - gap * (n - 1)) / n

        baseline = Line(LEFT * (self.width / 2), RIGHT * (self.width / 2)).set_stroke("#2B3A55", width=2)
        y_axis = Line(baseline.get_left(), baseline.get_left() + UP * self.height).set_stroke("#2B3A55", width=2)

        bars = VGroup()
        labels = VGroup()
        for i, v in enumerate(self.values):
            h = max(0.0001, (v / max_v) * self.height)
            rect = Rectangle(width=bar_w, height=h).set_fill(color, opacity=0.9).set_stroke("#2B3A55", width=1.2)
            rect.move_to(baseline.get_left() + RIGHT * (bar_w / 2 + i * (bar_w + gap)) + UP * (h / 2))
            bars.add(rect)

            t = label(str(self.years[i]) if i < len(self.years) else "", font_size=18, color=THEME.muted)
            t.scale_to_fit_width(bar_w)
            t.next_to(rect, DOWN, buff=0.15)
            labels.add(t)

        self.add(baseline, y_axis, bars, labels)
