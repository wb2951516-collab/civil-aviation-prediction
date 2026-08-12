from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class MetricResult:
    mae: float
    rmse: float
    mape: float


def _metrics(y_true, y_pred) -> MetricResult:
    import numpy as np

    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    err = y_pred - y_true
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err**2)))
    mask = y_true != 0
    mape = float(np.mean(np.abs(err[mask] / y_true[mask])) * 100) if mask.any() else float("nan")
    return MetricResult(mae=mae, rmse=rmse, mape=mape)


def _last_complete_year_total(train_df) -> Optional[float]:
    import pandas as pd

    if train_df is None or len(train_df) == 0:
        return None
    df = train_df.copy()
    if "year" not in df.columns:
        df["year"] = df.index.year
    if "month" not in df.columns:
        df["month"] = df.index.month
    counts = df.groupby("year")["month"].nunique()
    complete_years = [int(y) for y, c in counts.items() if int(c) == 12]
    if not complete_years:
        return None
    last_year = max(complete_years)
    total = df[df["year"] == last_year]["value"].sum()
    return float(total)


def rolling_backtest(
    ts,
    profile: Dict[str, Any],
    horizon: int = 12,
    step: int = 12,
    min_train: int = 24,
) -> Dict[str, Any]:
    import numpy as np
    import pandas as pd

    from capm.growth import apply_annual_growth_adjustment
    from capm.holiday import apply_holiday_effects
    from capm.models import ForecastOutput, holt_winters_forecast, linear_forecast, sarima_forecast

    holiday_cfg = profile.get("holiday", {})
    growth_cfg = profile.get("growth", {})
    model_cfg = profile.get("model", {})
    spring_festival_dates = profile.get("spring_festival_dates", {})

    annual_growth_rate = float(growth_cfg.get("annual_growth_rate", 0.027))
    sarima_cfg = model_cfg.get("sarima", {})
    hw_cfg = model_cfg.get("holt_winters", {})

    results: Dict[str, List[MetricResult]] = {"hw": [], "sarima": [], "linear": []}
    windows: List[Tuple[pd.Timestamp, pd.Timestamp]] = []

    total_len = len(ts)
    if total_len < min_train + horizon:
        return {"error": "历史数据不足以回测", "min_required": int(min_train + horizon)}

    start_idx = min_train
    for cut in range(start_idx, total_len - horizon + 1, step):
        train = ts.iloc[:cut]
        test = ts.iloc[cut : cut + horizon]
        if len(test) == 0:
            continue

        hist_total = _last_complete_year_total(train.to_frame(name="value"))

        hw_out = holt_winters_forecast(
            train,
            periods=len(test),
            trend=hw_cfg.get("trend", "add"),
            seasonal=hw_cfg.get("seasonal", "add"),
            seasonal_periods=int(hw_cfg.get("seasonal_periods", 12)),
            auto_tune=bool(hw_cfg.get("auto_tune", False)),
        )
        sarima_out = sarima_forecast(
            train,
            periods=len(test),
            order=tuple(sarima_cfg.get("order", (1, 1, 1))),
            seasonal_order=tuple(sarima_cfg.get("seasonal_order", (1, 1, 1, 12))),
            auto_tune=bool(sarima_cfg.get("auto_tune", False)),
        )
        lin_out = linear_forecast(train, periods=len(test))

        def post_process(out: ForecastOutput):
            s, spring_info = apply_holiday_effects(out.forecast, holiday_cfg, spring_festival_dates)
            s2, _ = apply_annual_growth_adjustment(s, annual_growth_rate, hist_total)
            return s2

        hw_pred = post_process(hw_out).reindex(test.index)
        sarima_pred = post_process(sarima_out).reindex(test.index)
        lin_pred = post_process(lin_out).reindex(test.index)

        results["hw"].append(_metrics(test.values, hw_pred.values))
        results["sarima"].append(_metrics(test.values, sarima_pred.values))
        results["linear"].append(_metrics(test.values, lin_pred.values))
        windows.append((test.index[0], test.index[-1]))

    def agg(ms: List[MetricResult]) -> Dict[str, float]:
        if not ms:
            return {"mae": float("nan"), "rmse": float("nan"), "mape": float("nan")}
        return {
            "mae": float(np.mean([m.mae for m in ms])),
            "rmse": float(np.mean([m.rmse for m in ms])),
            "mape": float(np.mean([m.mape for m in ms])),
        }

    summary = {k: agg(v) for k, v in results.items()}
    return {"windows": [(a.strftime("%Y-%m"), b.strftime("%Y-%m")) for a, b in windows], "summary": summary}


def recommend_weights_from_backtest(backtest_result: Dict[str, Any]) -> Dict[str, float]:
    summary = backtest_result.get("summary", {})
    mape_hw = float(summary.get("hw", {}).get("mape", float("nan")))
    mape_sarima = float(summary.get("sarima", {}).get("mape", float("nan")))
    mape_linear = float(summary.get("linear", {}).get("mape", float("nan")))

    scores = {}
    for k, m in [("hw", mape_hw), ("sarima", mape_sarima), ("linear", mape_linear)]:
        if m != m or m <= 0:
            scores[k] = 0.0
        else:
            scores[k] = 1.0 / m

    total = sum(scores.values())
    if total <= 0:
        return {"hw": 1 / 3, "sarima": 1 / 3, "linear": 1 / 3}
    return {k: float(v / total) for k, v in scores.items()}

