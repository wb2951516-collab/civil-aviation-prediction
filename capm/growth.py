from typing import Any, Dict, Optional, Tuple


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

