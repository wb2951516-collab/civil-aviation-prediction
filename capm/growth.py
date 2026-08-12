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

