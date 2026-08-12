from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class ForecastOutput:
    forecast: Any
    meta: Dict[str, Any]


@dataclass(frozen=True)
class EnsembleOutput:
    forecast: Any
    weights: Dict[str, float]
    meta: Dict[str, Any]


def _future_month_index(ts, periods: int):
    import pandas as pd

    if ts is None or len(ts) == 0:
        start = pd.Timestamp.today().to_period("M").to_timestamp()
    else:
        last = pd.Timestamp(ts.index[-1])
        start = (last.to_period("M") + 1).to_timestamp()
    return pd.date_range(start=start, periods=int(periods), freq="MS")


def simple_seasonal_forecast(ts, periods: int = 12):
    import pandas as pd

    ts = ts.dropna()
    idx = _future_month_index(ts, periods)
    df = pd.DataFrame({"value": ts.values, "month": ts.index.month})
    monthly_avg = df.groupby("month")["value"].mean()
    overall = float(df["value"].mean()) if len(df) else 0.0
    values = []
    for d in idx:
        m = int(d.month)
        if m in monthly_avg.index:
            values.append(float(monthly_avg.loc[m]))
        else:
            values.append(overall)
    return pd.Series(values, index=idx)


def linear_forecast(ts, periods: int = 12) -> ForecastOutput:
    import numpy as np
    import pandas as pd

    ts = ts.dropna()
    if len(ts) < 2:
        return ForecastOutput(simple_seasonal_forecast(ts, periods=periods), {"method": "fallback", "reason": "too_few_points"})

    x = np.arange(len(ts), dtype=float)
    y = ts.values.astype(float)
    slope, intercept = np.polyfit(x, y, deg=1)
    x_future = np.arange(len(ts), len(ts) + int(periods), dtype=float)
    y_future = intercept + slope * x_future
    y_future = np.maximum(y_future, 0.0)
    fc = pd.Series(y_future, index=_future_month_index(ts, periods))
    return ForecastOutput(fc, {"method": "linear", "slope": float(slope), "intercept": float(intercept)})


def holt_winters_forecast(
    ts,
    periods: int = 12,
    trend: Optional[str] = "add",
    seasonal: Optional[str] = "add",
    seasonal_periods: int = 12,
    auto_tune: bool = False,
) -> ForecastOutput:
    import warnings

    import pandas as pd
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    ts = ts.dropna()
    if len(ts) < max(2, int(seasonal_periods)):
        return ForecastOutput(simple_seasonal_forecast(ts, periods=periods), {"method": "fallback", "reason": "too_short"})

    candidates = [(trend, seasonal)]
    if auto_tune:
        candidates = []
        for t in [None, "add", "mul"]:
            for s in [None, "add", "mul"]:
                if s is not None and len(ts) < 2 * int(seasonal_periods):
                    continue
                candidates.append((t, s))

    best = None
    best_score = float("inf")
    best_meta: Dict[str, Any] = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for t, s in candidates:
            try:
                model = ExponentialSmoothing(
                    ts.astype(float),
                    trend=t,
                    seasonal=s,
                    seasonal_periods=int(seasonal_periods) if s is not None else None,
                    initialization_method="estimated",
                )
                res = model.fit(optimized=True)
                score = float(getattr(res, "aic", float("inf")))
                if score < best_score:
                    best_score = score
                    best = res
                    best_meta = {"method": "holt_winters", "trend": t, "seasonal": s, "aic": score}
            except Exception:
                continue

    if best is None:
        return ForecastOutput(simple_seasonal_forecast(ts, periods=periods), {"method": "fallback", "reason": "fit_failed"})

    idx = _future_month_index(ts, periods)
    pred = best.forecast(int(periods))
    pred = pd.Series(pred.values, index=idx)
    pred = pred.clip(lower=0.0)
    return ForecastOutput(pred, best_meta)


def sarima_forecast(
    ts,
    periods: int = 12,
    order: Tuple[int, int, int] = (1, 1, 1),
    seasonal_order: Tuple[int, int, int, int] = (1, 1, 1, 12),
    auto_tune: bool = False,
) -> ForecastOutput:
    import warnings

    import pandas as pd
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    ts = ts.dropna()
    if len(ts) < 8:
        return ForecastOutput(simple_seasonal_forecast(ts, periods=periods), {"method": "fallback", "reason": "too_short"})

    def _clamp(v, lo, hi):
        return max(lo, min(hi, int(v)))

    p0, d0, q0 = [int(x) for x in order]
    P0, D0, Q0, m = [int(x) for x in seasonal_order]
    m = int(m) if int(m) > 0 else 12

    candidates = [((p0, d0, q0), (P0, D0, Q0, m))]
    if auto_tune:
        candidates = []
        for p in {_clamp(p0 - 1, 0, 2), _clamp(p0, 0, 2), _clamp(p0 + 1, 0, 2)}:
            for d in {_clamp(d0, 0, 2)}:
                for q in {_clamp(q0 - 1, 0, 2), _clamp(q0, 0, 2), _clamp(q0 + 1, 0, 2)}:
                    for P in {_clamp(P0 - 1, 0, 1), _clamp(P0, 0, 1), _clamp(P0 + 1, 0, 1)}:
                        for D in {_clamp(D0, 0, 1)}:
                            for Q in {_clamp(Q0 - 1, 0, 1), _clamp(Q0, 0, 1), _clamp(Q0 + 1, 0, 1)}:
                                candidates.append(((p, d, q), (P, D, Q, m)))

    best_res = None
    best_aic = float("inf")
    best_meta: Dict[str, Any] = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for o, so in candidates:
            try:
                model = SARIMAX(
                    ts.astype(float),
                    order=o,
                    seasonal_order=so,
                    enforce_stationarity=False,
                    enforce_invertibility=False,
                )
                res = model.fit(disp=False)
                aic = float(getattr(res, "aic", float("inf")))
                if aic < best_aic:
                    best_aic = aic
                    best_res = res
                    best_meta = {"method": "sarima", "order": o, "seasonal_order": so, "aic": aic}
            except Exception:
                continue

    if best_res is None:
        return ForecastOutput(simple_seasonal_forecast(ts, periods=periods), {"method": "fallback", "reason": "fit_failed"})

    idx = _future_month_index(ts, periods)
    pred = best_res.forecast(steps=int(periods))
    pred = pd.Series(pred.values, index=idx).clip(lower=0.0)
    return ForecastOutput(pred, best_meta)


def ensemble_forecast(
    ts,
    weights: Dict[str, float],
    periods: int = 12,
    auto_tune_sarima: bool = False,
    auto_tune_hw: bool = False,
    sarima_params: Optional[Dict[str, Any]] = None,
    hw_params: Optional[Dict[str, Any]] = None,
) -> Tuple[EnsembleOutput, Dict[str, ForecastOutput]]:
    sarima_params = sarima_params or {}
    hw_params = hw_params or {}

    hw = holt_winters_forecast(
        ts,
        periods=periods,
        trend=hw_params.get("trend", "add"),
        seasonal=hw_params.get("seasonal", "add"),
        seasonal_periods=int(hw_params.get("seasonal_periods", 12)),
        auto_tune=bool(auto_tune_hw),
    )
    sarima = sarima_forecast(
        ts,
        periods=periods,
        order=tuple(sarima_params.get("order", (1, 1, 1))),
        seasonal_order=tuple(sarima_params.get("seasonal_order", (1, 1, 1, 12))),
        auto_tune=bool(auto_tune_sarima),
    )
    linear = linear_forecast(ts, periods=periods)

    w_hw = float(weights.get("hw", 0.0))
    w_s = float(weights.get("sarima", 0.0))
    w_l = float(weights.get("linear", 0.0))
    total = w_hw + w_s + w_l
    if total <= 0:
        w_hw = w_s = w_l = 1.0 / 3.0
        total = 1.0
    w_hw /= total
    w_s /= total
    w_l /= total

    idx = hw.forecast.index
    ens = (hw.forecast.reindex(idx).astype(float) * w_hw) + (sarima.forecast.reindex(idx).astype(float) * w_s) + (linear.forecast.reindex(idx).astype(float) * w_l)
    ens = ens.clip(lower=0.0)

    out = EnsembleOutput(ens, {"hw": w_hw, "sarima": w_s, "linear": w_l}, {"method": "ensemble"})
    components = {"Holt-Winters": hw, "SARIMA": sarima, "Linear": linear}
    return out, components

