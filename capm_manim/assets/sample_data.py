from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class SeriesData:
    x_labels: List[str]
    values: List[float]


def sample_history() -> SeriesData:
    months = [f"2024-{m:02d}" for m in range(1, 13)] + [f"2025-{m:02d}" for m in range(1, 13)]
    values = [
        520,
        540,
        610,
        580,
        600,
        640,
        720,
        710,
        690,
        750,
        780,
        820,
        560,
        590,
        650,
        620,
        640,
        690,
        780,
        770,
        740,
        810,
        850,
        900,
    ]
    return SeriesData(months, values)


def sample_model_components() -> Tuple[SeriesData, SeriesData, SeriesData]:
    months = [f"2026-{m:02d}" for m in range(1, 13)]
    linear = [610, 635, 660, 685, 710, 735, 760, 785, 810, 835, 860, 885]
    hw = [600, 650, 720, 690, 700, 730, 840, 830, 790, 880, 910, 950]
    sarima = [630, 670, 690, 675, 685, 715, 810, 805, 775, 855, 895, 935]
    return SeriesData(months, linear), SeriesData(months, hw), SeriesData(months, sarima)


def sample_ensemble(weights=(0.4, 0.3, 0.3)) -> SeriesData:
    months = [f"2026-{m:02d}" for m in range(1, 13)]
    lin, hw, sar = sample_model_components()
    w_hw, w_sar, w_lin = float(weights[0]), float(weights[1]), float(weights[2])
    total = w_hw + w_sar + w_lin
    if total <= 0:
        w_hw = w_sar = w_lin = 1 / 3
        total = 1
    w_hw, w_sar, w_lin = w_hw / total, w_sar / total, w_lin / total
    values = [hw.values[i] * w_hw + sar.values[i] * w_sar + lin.values[i] * w_lin for i in range(12)]
    return SeriesData(months, values)

