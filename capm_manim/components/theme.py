from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from manim import BLACK, DOWN, LEFT, RIGHT, UP, WHITE, VGroup, Text


SPEED = 1.0
FONT_FAMILY = "Microsoft YaHei"


def rt(seconds: float) -> float:
    s = float(seconds)
    speed = float(SPEED) if float(SPEED) > 0 else 1.0
    return s / speed


@dataclass(frozen=True)
class Theme:
    bg: str = "#0B0F1A"
    text: str = "#EAECEF"
    muted: str = "#9AA4B2"
    data: str = "#4C9AFF"
    model: str = "#B37FEB"
    post: str = "#FFA940"
    output: str = "#73D13D"
    config: str = "#8C8C8C"
    accent: str = "#40A9FF"
    danger: str = "#FF4D4F"


THEME = Theme()


def label(
    text: str,
    font_size: float = 32,
    color: str = THEME.text,
    font: str = FONT_FAMILY,
    weight: Optional[str] = None,
):
    if weight is None:
        return Text(text, font=font, font_size=font_size, color=color)
    return Text(text, font=font, font_size=font_size, color=color, weight=weight)


def stack_vert(items: Iterable, buff: float = 0.2) -> VGroup:
    group = VGroup(*items)
    group.arrange(direction=DOWN, aligned_edge=LEFT, buff=buff)
    return group


def stack_horiz(items: Iterable, buff: float = 0.2) -> VGroup:
    group = VGroup(*items)
    group.arrange(direction=RIGHT, aligned_edge=UP, buff=buff)
    return group


def default_text_colors():
    return {"text": THEME.text, "muted": THEME.muted, "white": WHITE, "black": BLACK}
