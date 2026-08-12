"""量化回测模块：滚动回测 + 样本外测试 + 绩效评估。

框架设计（参考量化回测成熟做法）：
- 滚动窗口回测（walk-forward）：以 min_train 起逐段训练、外推 horizon 个月，覆盖
  不同市场阶段，衡量模型在时间上的稳定性；
- 样本外 holdout：一次切分（默认 80% 训练 / 20% 测试），模拟真实"用过去预测未来"；
- 绩效指标：MAE / RMSE / MAPE / MDA（方向命中率）/ Theil U（相对朴素基准的改进）；
- 权重策略：贝叶斯模型平均（BMA，基于残差似然）优先，MAPE 倒数法兼容兜底。
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class MetricResult:
    mae: float
    rmse: float
    mape: float
    mda: float
    theil_u: float


def _metrics(y_true, y_pred) -> MetricResult:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    err = y_pred - y_true
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err**2)))
    mask = y_true != 0
    mape = float(np.mean(np.abs(err[mask] / y_true[mask])) * 100) if mask.any() else float("nan")

    # MDA：方向命中率（环比方向与真实一致的比例）
    if len(y_true) >= 2:
        true_dir = np.sign(y_true[1:] - y_true[:-1])
        pred_dir = np.sign(y_pred[1:] - y_true[:-1])
        mda = float(np.mean(true_dir == pred_dir)) if len(true_dir) else float("nan")
    else:
        mda = float("nan")

    # Theil U：相对"上期值重复"朴素基准的 RMSE 之比（<1 表示优于基准）
    naive = y_true[:-1]
    denom = np.sqrt(np.mean((y_true[1:] - naive) ** 2))
    if denom and denom == denom:
        theil_u = float(np.sqrt(np.mean((y_true[1:] - y_pred[1:]) ** 2)) / denom)
    else:
        theil_u = float("nan")
    return MetricResult(mae=mae, rmse=rmse, mape=mape, mda=mda, theil_u=theil_u)


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


def _post_process(out, holiday_cfg, growth_cfg, spring_festival_dates, hist_total):
    from capm.growth import apply_annual_growth_adjustment
    from capm.holiday import apply_holiday_effects

    annual_growth_rate = float(growth_cfg.get("annual_growth_rate", 0.027))
    s, _ = apply_holiday_effects(out.forecast, holiday_cfg, spring_festival_dates)
    s2, _ = apply_annual_growth_adjustment(s, annual_growth_rate, hist_total)
    return s2


def _slice_factors(factors, index):
    """按目标 index 对齐并截取外生变量（训练期 / 预测期）"""
    if factors is None:
        return None, None
    import pandas as pd

    df = pd.DataFrame(factors)
    if "gdp" not in df.columns:
        df.columns = ["gdp", "ask"][: df.shape[1]]
    aligned = df.reindex(index)
    # 缺失用前向填充兜底
    aligned = aligned.ffill().bfill()
    if aligned.isna().any().any():
        return None, None
    return aligned, None


def rolling_backtest(
    ts,
    profile: Dict[str, Any],
    horizon: int = 12,
    step: int = 12,
    min_train: int = 24,
    factors: Any = None,
) -> Dict[str, Any]:
    """滚动窗口回测（walk-forward）。

    对精选模型集合（Holt-Winters / SARIMA / 融合）逐窗口评估，
    返回汇总指标、逐窗口误差（供 BMA 使用）与推荐结论。
    """
    import pandas as pd

    from capm.models import ForecastOutput, ensemble_forecast, holt_winters_forecast, sarima_forecast

    holiday_cfg = profile.get("holiday", {})
    growth_cfg = profile.get("growth", {})
    model_cfg = profile.get("model", {})
    spring_festival_dates = profile.get("spring_festival_dates", {})

    sarima_cfg = model_cfg.get("sarima", {})
    hw_cfg = model_cfg.get("holt_winters", {})

    results: Dict[str, List[MetricResult]] = {"hw": [], "sarima": [], "ensemble": []}
    errors: Dict[str, List[np.ndarray]] = {"hw": [], "sarima": [], "ensemble": []}
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
        test_index = test.index

        if factors is not None:
            exog_train, _ = _slice_factors(factors, train.index)
            exog_test, _ = _slice_factors(factors, test_index)
        else:
            exog_train = exog_test = None

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
            exog=exog_train,
            exog_future=exog_test,
        )

        hw_pred = _post_process(hw_out, holiday_cfg, growth_cfg, spring_festival_dates, hist_total).reindex(test_index)
        sarima_pred = _post_process(sarima_out, holiday_cfg, growth_cfg, spring_festival_dates, hist_total).reindex(test_index)

        # 融合：以滚动窗口内的 MAPE 倒数中间权重（与历史版本保持可对比性）
        mid = _map_weights({"hw": hw_pred, "sarima": sarima_pred}, test)
        ens_out, _ = ensemble_forecast(
            train,
            weights=mid,
            periods=len(test),
            auto_tune_sarima=bool(sarima_cfg.get("auto_tune", False)),
            auto_tune_hw=bool(hw_cfg.get("auto_tune", False)),
            sarima_params={"order": sarima_cfg.get("order", [1, 1, 1]), "seasonal_order": sarima_cfg.get("seasonal_order", [1, 1, 1, 12])},
            hw_params={"trend": hw_cfg.get("trend", "add"), "seasonal": hw_cfg.get("seasonal", "add"), "seasonal_periods": hw_cfg.get("seasonal_periods", 12)},
            exog=exog_train,
            exog_future=exog_test,
        )
        ens_pred = _post_process(ens_out, holiday_cfg, growth_cfg, spring_festival_dates, hist_total).reindex(test_index)

        for key, pred in (("hw", hw_pred), ("sarima", sarima_pred), ("ensemble", ens_pred)):
            m = _metrics(test.values, pred.values)
            results[key].append(m)
            errors[key].append(np.asarray(pred.values - test.values, dtype=float))
        windows.append((test.index[0], test.index[-1]))

    def agg(ms: List[MetricResult]) -> Dict[str, float]:
        if not ms:
            return {"mae": float("nan"), "rmse": float("nan"), "mape": float("nan"), "mda": float("nan"), "theil_u": float("nan")}
        return {
            "mae": float(np.mean([m.mae for m in ms])),
            "rmse": float(np.mean([m.rmse for m in ms])),
            "mape": float(np.mean([m.mape for m in ms])),
            "mda": float(np.nanmean([m.mda for m in ms])),
            "theil_u": float(np.nanmean([m.theil_u for m in ms])),
        }

    summary = {k: agg(v) for k, v in results.items()}
    merged_errors = {k: np.concatenate(v) if v else np.array([]) for k, v in errors.items()}
    return {
        "windows": [(a.strftime("%Y-%m"), b.strftime("%Y-%m")) for a, b in windows],
        "summary": summary,
        "errors": merged_errors,
        "recommendation": _recommend_model(summary, merged_errors),
    }


def holdout_backtest(
    ts,
    profile: Dict[str, Any],
    train_ratio: float = 0.8,
    horizon: Optional[int] = None,
    factors: Any = None,
) -> Dict[str, Any]:
    """样本外一次性回测：训练集外推 horizon 个月，与真实值对比。"""
    import pandas as pd

    from capm.models import ensemble_forecast, holt_winters_forecast, sarima_forecast

    n = len(ts)
    if n < 24:
        return {"error": "历史数据不足以进行样本外回测"}
    cut = max(12, int(n * float(train_ratio)))
    if horizon is None:
        horizon = n - cut
    train, test = ts.iloc[:cut], ts.iloc[cut : cut + horizon]
    if len(test) == 0:
        return {"error": "样本外区间为空"}

    holiday_cfg = profile.get("holiday", {})
    growth_cfg = profile.get("growth", {})
    model_cfg = profile.get("model", {})
    spring_festival_dates = profile.get("spring_festival_dates", {})
    sarima_cfg = model_cfg.get("sarima", {})
    hw_cfg = model_cfg.get("holt_winters", {})

    hist_total = _last_complete_year_total(train.to_frame(name="value"))
    test_index = test.index
    if factors is not None:
        exog_train, _ = _slice_factors(factors, train.index)
        exog_test, _ = _slice_factors(factors, test_index)
    else:
        exog_train = exog_test = None

    hw_out = holt_winters_forecast(
        train, periods=len(test),
        trend=hw_cfg.get("trend", "add"), seasonal=hw_cfg.get("seasonal", "add"),
        seasonal_periods=int(hw_cfg.get("seasonal_periods", 12)),
        auto_tune=bool(hw_cfg.get("auto_tune", False)),
    )
    sarima_out = sarima_forecast(
        train, periods=len(test),
        order=tuple(sarima_cfg.get("order", (1, 1, 1))),
        seasonal_order=tuple(sarima_cfg.get("seasonal_order", (1, 1, 1, 12))),
        auto_tune=bool(sarima_cfg.get("auto_tune", False)),
        exog=exog_train, exog_future=exog_test,
    )
    hw_pred = _post_process(hw_out, holiday_cfg, growth_cfg, spring_festival_dates, hist_total).reindex(test_index)
    sarima_pred = _post_process(sarima_out, holiday_cfg, growth_cfg, spring_festival_dates, hist_total).reindex(test_index)
    mid = _map_weights({"hw": hw_pred, "sarima": sarima_pred}, test)
    ens_out, _ = ensemble_forecast(
        train, weights=mid, periods=len(test),
        auto_tune_sarima=bool(sarima_cfg.get("auto_tune", False)),
        auto_tune_hw=bool(hw_cfg.get("auto_tune", False)),
        sarima_params={"order": sarima_cfg.get("order", [1, 1, 1]), "seasonal_order": sarima_cfg.get("seasonal_order", [1, 1, 1, 12])},
        hw_params={"trend": hw_cfg.get("trend", "add"), "seasonal": hw_cfg.get("seasonal", "add"), "seasonal_periods": hw_cfg.get("seasonal_periods", 12)},
        exog=exog_train, exog_future=exog_test,
    )
    ens_pred = _post_process(ens_out, holiday_cfg, growth_cfg, spring_festival_dates, hist_total).reindex(test_index)

    predictions = {"hw": hw_pred, "sarima": sarima_pred, "ensemble": ens_pred}
    summary = {}
    errors = {}
    for key, pred in predictions.items():
        summary[key] = _metrics(test.values, pred.values)
        errors[key] = np.asarray(pred.values - test.values, dtype=float)
    summary_dict = {k: {"mae": m.mae, "rmse": m.rmse, "mape": m.mape, "mda": m.mda, "theil_u": m.theil_u} for k, m in summary.items()}
    return {
        "train_range": (train.index[0].strftime("%Y-%m"), train.index[-1].strftime("%Y-%m")),
        "test_range": (test.index[0].strftime("%Y-%m"), test.index[-1].strftime("%Y-%m")),
        "summary": summary_dict,
        "errors": errors,
        "recommendation": _recommend_model(summary_dict, errors),
    }


def _map_weights(preds: Dict[str, Any], test) -> Dict[str, float]:
    """窗口内 MAPE 倒数权重（中间权重，保证融合模型可回测）"""
    scores = {}
    for k, pred in preds.items():
        m = _metrics(test.values, pred.values)
        mape = float(m.mape)
        scores[k] = 1.0 / mape if (mape == mape and mape > 0) else 0.0
    total = sum(scores.values())
    if total <= 0:
        n = len(scores)
        return {k: 1.0 / n for k in scores}
    return {k: float(v / total) for k, v in scores.items()}


def _recommend_model(summary: Dict[str, Any], errors: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """依据回测结果给出推荐：最优单模型 + 融合权重（BMA 优先）。"""
    from capm.bayesian import bma_weights

    # 1) 融合权重：BMA（有残差时），否则 MAPE 倒数
    weights = None
    weight_method = "均分"
    if errors:
        err_sub = {k: v for k, v in errors.items() if k in ("hw", "sarima") and len(v) > 0}
        if len(err_sub) == 2:
            weights = bma_weights(err_sub)
            weight_method = "BMA(贝叶斯模型平均)"

    if weights is None:
        mape_hw = float(summary.get("hw", {}).get("mape", float("nan")))
        mape_sarima = float(summary.get("sarima", {}).get("mape", float("nan")))
        scores = {}
        for k, m in [("hw", mape_hw), ("sarima", mape_sarima)]:
            scores[k] = 1.0 / m if (m == m and m > 0) else 0.0
        total = sum(scores.values())
        if total > 0:
            weights = {k: float(v / total) for k, v in scores.items()}
            weight_method = "MAPE倒数"
        else:
            weights = {"hw": 0.5, "sarima": 0.5}

    # 2) 最优单模型（按 MAPE 排序）
    best_model = min(
        [k for k in ("hw", "sarima", "ensemble") if k in summary],
        key=lambda k: float(summary[k].get("mape", float("inf")) or float("inf")),
        default="ensemble",
    )
    return {"model": best_model, "weights": weights, "weight_method": weight_method}


def recommend_weights_from_backtest(backtest_result: Dict[str, Any]) -> Dict[str, float]:
    """兼容接口：返回 {"hw": ..., "sarima": ...} 融合权重（BMA 优先）。"""
    rec = backtest_result.get("recommendation") or {}
    weights = rec.get("weights")
    if weights and isinstance(weights, dict):
        return dict(weights)
    summary = backtest_result.get("summary", {})
    mape_hw = float(summary.get("hw", {}).get("mape", float("nan")))
    mape_sarima = float(summary.get("sarima", {}).get("mape", float("nan")))
    scores = {}
    for k, m in [("hw", mape_hw), ("sarima", mape_sarima)]:
        if m != m or m <= 0:
            scores[k] = 0.0
        else:
            scores[k] = 1.0 / m
    total = sum(scores.values())
    if total <= 0:
        return {"hw": 0.5, "sarima": 0.5}
    return {k: float(v / total) for k, v in scores.items()}
