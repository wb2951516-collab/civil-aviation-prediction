import sys

try:
    import pandas as pd
except ModuleNotFoundError as e:
    print(f"self_check failed: missing dependency: {e.name}")
    print("请先执行: pip install -r requirements.txt")
    sys.exit(2)

from capm.backtest import rolling_backtest
from capm.config_store import default_config
from capm.growth import apply_annual_growth_adjustment
from capm.holiday import apply_holiday_effects, compute_month_spring_travel_days, compute_spring_travel_span
from capm.models import ensemble_forecast, holt_winters_forecast, linear_forecast, sarima_forecast


def _sample_ts() -> pd.Series:
    sample_data = [
        (2024, 10, 243533),
        (2024, 11, 178537),
        (2024, 12, 187840),
        (2025, 1, 240783),
        (2025, 2, 251444),
        (2025, 3, 234029),
        (2025, 4, 236668),
        (2025, 5, 241408),
        (2025, 6, 215072),
        (2025, 7, 293708),
        (2025, 8, 309236),
        (2025, 9, 228916),
    ]
    dates = [pd.Timestamp(year=y, month=m, day=1) for y, m, _ in sample_data]
    values = [v for _, _, v in sample_data]
    return pd.Series(values, index=pd.DatetimeIndex(dates)).sort_index()


def main() -> int:
    ts = _sample_ts()
    cfg = default_config()
    profile = cfg["profiles"]["default"]
    holiday_cfg = profile["holiday"]
    growth_cfg = profile["growth"]
    spring_dates = profile["spring_festival_dates"]

    year = 2026
    before_days = int(holiday_cfg["spring_travel_before_days"])
    after_days = int(holiday_cfg["spring_travel_after_days"])
    start, end, sf = compute_spring_travel_span(year, spring_dates, before_days, after_days)
    _ = compute_month_spring_travel_days(year, 2, spring_dates, before_days, after_days)

    hw = holt_winters_forecast(ts, periods=12, auto_tune=True).forecast
    sarima = sarima_forecast(ts, periods=12, auto_tune=True).forecast
    linear = linear_forecast(ts, periods=12).forecast
    ensemble, _ = ensemble_forecast(ts, weights={"hw": 0.4, "sarima": 0.3, "linear": 0.3}, auto_tune_sarima=True, auto_tune_hw=True)

    for name, fc in [("hw", hw), ("sarima", sarima), ("linear", linear), ("ensemble", ensemble.forecast)]:
        if len(fc) != 12:
            raise RuntimeError(f"{name} forecast length != 12")
        if fc.isna().any():
            raise RuntimeError(f"{name} forecast contains NaN")

    adjusted, spring_info = apply_holiday_effects(ensemble.forecast, holiday_cfg, spring_dates)
    final, growth_rates = apply_annual_growth_adjustment(adjusted, float(growth_cfg["annual_growth_rate"]), None)
    if len(final) != 12:
        raise RuntimeError("post-processed forecast length != 12")

    bt = rolling_backtest(ts, profile, horizon=3, step=3, min_train=6)
    if "error" in bt:
        raise RuntimeError("backtest returned error")

    print("self_check ok")
    print(f"spring_festival_source={sf.source} span={start.date()}..{end.date()} profiles=default")
    print(f"spring_info_months={len(spring_info)} growth_years={len(growth_rates)}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"self_check failed: {e}")
        sys.exit(1)

