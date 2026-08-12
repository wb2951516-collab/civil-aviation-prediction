from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from manim import DOWN, LEFT, RIGHT, Rectangle, VGroup

from capm_manim.components.theme import THEME, label


@dataclass(frozen=True)
class TableStyle:
    header_fill: str = "#121826"
    row_fill: str = "#0F1624"
    border: str = "#2B3A55"
    header_text: str = THEME.text
    cell_text: str = THEME.muted


class DataTable(VGroup):
    def __init__(
        self,
        headers: Sequence[str],
        rows: Sequence[Sequence[str]],
        col_widths: Sequence[float] | None = None,
        row_height: float = 0.42,
        header_height: float = 0.5,
        style: TableStyle = TableStyle(),
        header_size: float = 20,
        cell_size: float = 18,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.headers = list(headers)
        self.rows = [list(map(str, r)) for r in rows]
        self.style = style

        cols = len(self.headers)
        if col_widths is None:
            col_widths = [2.0] * cols
        col_widths = list(col_widths)
        if len(col_widths) != cols:
            col_widths = [float(col_widths[0])] * cols

        header_group = self._build_row(
            self.headers,
            col_widths=col_widths,
            height=header_height,
            fill=style.header_fill,
            stroke=style.border,
            text_color=style.header_text,
            font_size=header_size,
        )
        body_rows: List[VGroup] = []
        for r in self.rows:
            body_rows.append(
                self._build_row(
                    r,
                    col_widths=col_widths,
                    height=row_height,
                    fill=style.row_fill,
                    stroke=style.border,
                    text_color=style.cell_text,
                    font_size=cell_size,
                )
            )

        table = VGroup(header_group, *body_rows).arrange(DOWN, buff=0.02, aligned_edge=LEFT)
        self.add(table)
        self.table = table

    def _build_row(
        self,
        values: Sequence[str],
        col_widths: Sequence[float],
        height: float,
        fill: str,
        stroke: str,
        text_color: str,
        font_size: float,
    ) -> VGroup:
        cells = []
        for i, w in enumerate(col_widths):
            rect = Rectangle(width=float(w), height=float(height)).set_fill(fill, opacity=1).set_stroke(stroke, width=1.5)
            t = label(str(values[i]) if i < len(values) else "", font_size=font_size, color=text_color)
            t.scale_to_fit_width(float(w) - 0.25)
            t.move_to(rect.get_center())
            cells.append(VGroup(rect, t))
        row = VGroup(*cells).arrange(RIGHT, buff=0.02)
        return row

