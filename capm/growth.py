from typing import Any, Dict, Optional, Tuple


def normalize_yoy_targets(targets) -> Dict[int, float]:
    """把多种形态的同比目标归一化为 {年份: 增长率(小数)}。

    支持: {"2026": -0.1} / [{year: 2026, rate: -0.1}] / {2026: -0.1}
    """
    out: Dict[int, float] = {}
    if not targets:
        return out
    if isinstance(targets, dict):
        items = targets.items()
    else:
        try:
            items = [(t.get("year"), t.get("rate")) for t in targets if isinstance(t, dict)]
        except Exception:
            return out
    for year, rate in items:
        try:
            y = int(year)
            r = float(rate)
        except (TypeError, ValueError):
            continue
        if -0.95 < r < 5.0:
            out[y] = r
    return out


def _effective_rates(years, targets: Dict[int, float]) -> Dict[int, float]:
    """确定每个预测年份实际采用的同比率。

    优先按年份精确匹配；若目标表的年份与预测年份错位（例如用户先建了 2027 行，
    之后才导入到 2025 的数据，实际预测年份是 2026），则按行序对齐兜底，
    保证配置的同比目标一定生效，而不是静默按 0% 处理。
    """
    ordered_rates = [float(targets[y]) for y in sorted(targets)]
    rates: Dict[int, float] = {}
    for idx, year in enumerate(sorted(int(y) for y in years)):
        rate = targets.get(year)
        if rate is None:
            rate = ordered_rates[idx] if idx < len(ordered_rates) else 0.0
        rates[year] = float(rate)
    return rates


def _target_totals(years, targets: Dict[int, float], base_total: float) -> Dict[int, float]:
    """逐年复利: 当年目标总量 = 上一年目标总量 × (1 + 当年同比)。"""
    rates = _effective_rates(years, targets)
    result: Dict[int, float] = {}
    current = float(base_total)
    for year in sorted(rates):
        current = current * (1.0 + rates[year])
        result[year] = current
    return result


def apply_yoy_targets(forecast, targets, historical_yearly_total: Optional[float]):
    """按年度同比目标表校准预测（支持多年跨度）。

    Returns: (调整后序列, {年份: {target_total, model_total, adjust_pct}})
    """
    if forecast is None or len(forecast) < 12:
        return forecast, {}
    targets = normalize_yoy_targets(targets)
    if not targets:
        return forecast, {}

    forecast_df = forecast.to_frame(name="value")
    forecast_df["year"] = forecast_df.index.year
    yearly_totals = forecast_df.groupby("year")["value"].sum()
    years = sorted(int(y) for y in yearly_totals.index)

    base_total = float(historical_yearly_total) if historical_yearly_total is not None else float(yearly_totals[years[0]])
    target_map = _target_totals(years, targets, base_total)
    rate_map = _effective_rates(years, targets)

    adjusted_values = []
    info: Dict[int, Dict[str, float]] = {}
    for idx, row in forecast_df.iterrows():
        year = int(row["year"])
        original_total = float(yearly_totals[year])
        target_total = float(target_map.get(year, original_total))
        factor = target_total / original_total if original_total else 1.0
        adjusted_values.append(float(row["value"]) * factor)
        if year not in info:
            info[year] = {
                "target_total": target_total,
                "model_total": original_total,
                "adjust_pct": (target_total - original_total) / original_total * 100 if original_total else 0.0,
                "target_rate": float(rate_map.get(year, 0.0)),
            }

    adjusted_forecast = forecast.__class__(adjusted_values, index=forecast.index)
    return adjusted_forecast, info


def growth_sanity_check_targets(forecast, targets, historical_yearly_total: Optional[float]):
    """按年度同比目标表计算偏离告警（不修改预测值）。"""
    if forecast is None or len(forecast) < 12 or historical_yearly_total is None:
        return forecast, {}
    targets = normalize_yoy_targets(targets)
    if not targets:
        return forecast, {}

    forecast_df = forecast.to_frame(name="value")
    forecast_df["year"] = forecast_df.index.year
    yearly_totals = forecast_df.groupby("year")["value"].sum()
    years = sorted(int(y) for y in yearly_totals.index)
    target_map = _target_totals(years, targets, float(historical_yearly_total))
    rate_map = _effective_rates(years, targets)

    warnings_info: Dict[int, Dict[str, float]] = {}
    for year in years:
        target = float(target_map[year])
        if target <= 0:
            continue
        model_total = float(yearly_totals[year])
        dev = (model_total - target) / target * 100.0
        abs_dev = abs(dev)
        level = "ok" if abs_dev < 20.0 else ("watch" if abs_dev < 50.0 else "alert")
        warnings_info[year] = {
            "model_total": model_total,
            "target_total": target,
            "deviation_pct": dev,
            "level": level,
            "target_rate": float(rate_map.get(year, 0.0)),
        }
    return forecast, warnings_info


def apply_annual_growth_adjustment(forecast, annual_growth_rate: float, historical_yearly_total: Optional[float]) -> Tuple[Any, Dict[int, float]]:
    if len(forecast) < 12:
        return forecast, {}

    forecast_df = forecast.to_frame(name="value")
    forecast_df["year"] = forecast_df.index.year

    yearly_totals = forecast_df.groupby("year")["value"].sum()
    years = sorted(yearly_totals.index)

    target_totals: Dict[int, float] = {}
    if historical_yearly_total is not None:
        base_total = float(historical_yearly_total)
    else:
        base_total = float(yearly_totals[years[0]])

    for i, y in enumerate(years):
        target_totals[int(y)] = base_total * ((1.0 + float(annual_growth_rate)) ** (i + 1))

    adjusted_values = []
    growth_rates: Dict[int, float] = {}

    for idx, row in forecast_df.iterrows():
        year = int(row["year"])
        original_value = float(row["value"])
        original_yearly_total = float(yearly_totals[year])
        target_yearly_total = float(target_totals[year])
        yearly_adjustment = target_yearly_total / original_yearly_total if original_yearly_total != 0 else 1.0
        adjusted_value = original_value * yearly_adjustment
        adjusted_values.append(adjusted_value)

        if year not in growth_rates:
            growth_rates[year] = (target_yearly_total - original_yearly_total) / original_yearly_total * 100 if original_yearly_total != 0 else 0.0

    adjusted_forecast = forecast.__class__(adjusted_values, index=forecast.index)
    return adjusted_forecast, growth_rates


def growth_sanity_check(forecast, annual_growth_rate: float, historical_yearly_total: Optional[float]) -> Tuple[Any, Dict[int, Dict[str, float]]]:
    """增长率合理性告警: 计算预测年总量相对几何增长假设的偏离, 不修改预测值。

    依据: V1.1.1 分支实证——强制增长率覆盖在后疫情恢复期反效果
    (MAPE 28.55%→30.58%), 故干预引擎改为仅告警不修改, 信任模型趋势项。

    Returns:
        (原预测不变, 告警信息dict {year: {model_total, target_total, deviation_pct, level}})
        level: "ok"(偏离<20%) | "watch"(20-50%) | "alert"(>50%)
    """
    if len(forecast) < 12 or historical_yearly_total is None:
        return forecast, {}

    forecast_df = forecast.to_frame(name="value")
    forecast_df["year"] = forecast_df.index.year
    yearly_totals = forecast_df.groupby("year")["value"].sum()
    years = sorted(yearly_totals.index)

    base_total = float(historical_yearly_total)
    warnings_info: Dict[int, Dict[str, float]] = {}

    for i, y in enumerate(years):
        model_total = float(yearly_totals[y])
        target = base_total * ((1.0 + float(annual_growth_rate)) ** (i + 1))
        if target <= 0:
            continue
        dev = (model_total - target) / target * 100.0
        abs_dev = abs(dev)
        level = "ok" if abs_dev < 20.0 else ("watch" if abs_dev < 50.0 else "alert")
        warnings_info[int(y)] = {
            "model_total": model_total,
            "target_total": target,
            "deviation_pct": dev,
            "level": level,
        }

    return forecast, warnings_info

