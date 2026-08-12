"""V1.1 新旧算法方案量化回测对比验证脚本。

对比对象：
- 旧方案：Holt-Winters + SARIMA + 线性回归 三模型融合（MAPE 倒数权重）
- 新方案：Holt-Winters + SARIMA 精选融合（BMA 权重，可选 GDP/ASK 外生因子）

数据：基于真实量级合成的 2015-2025 月度旅客运输量序列
（趋势 + 年度季节性 + 春运形态 + 2020 疫情冲击 + 噪声）。

运行：python evaluate_v11.py
"""

import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

from capm.backtest import holdout_backtest, rolling_backtest
from capm.config_store import default_config
from capm.datasource import ExternalDataManager

RNG = np.random.default_rng(42)


def build_synthetic_series() -> pd.Series:
    """生成 2015-01 至 2025-12 的月度客运量（万人次量级）。"""
    n_years = 11
    base = 1200.0
    monthly_shape = [0.86, 1.08, 0.95, 0.96, 0.97, 1.00, 1.12, 1.16, 1.02, 1.05, 0.97, 0.94]
    shape = np.array(monthly_shape) / np.mean(monthly_shape)
    dates = pd.date_range("2015-01-01", periods=n_years * 12, freq="MS")
    t = np.arange(len(dates), dtype=float)
    annual_growth = 0.045
    trend = base * (1 + annual_growth) ** (t / 12.0)
    seasonal = shape[(t % 12).astype(int)]
    values = trend * seasonal
    # 春运 2 月额外提振
    feb_mask = (dates.month == 2)
    values[feb_mask] *= 1.06
    # 2020 疫情冲击（2-4 月 -55%，全年 -45%）
    covid = (dates >= "2020-02-01") & (dates <= "2020-04-30")
    values[covid] *= 0.45
    values[(dates >= "2020-05-01") & (dates <= "2020-12-31")] *= 0.82
    # 2021 恢复
    values[(dates >= "2021-01-01") & (dates <= "2021-12-31")] *= 0.92
    # 噪声
    noise = RNG.normal(1.0, 0.03, len(dates))
    return pd.Series(values * noise, index=dates, name="value")


def legacy_linear_forecast(ts, periods):
    """旧方案线性回归（评估脚本内实现，保持与历史版本可比性）。"""
    x = np.arange(len(ts), dtype=float)
    y = ts.values.astype(float)
    slope, intercept = np.polyfit(x, y, deg=1)
    x_future = np.arange(len(ts), len(ts) + int(periods), dtype=float)
    return pd.Series(np.maximum(intercept + slope * x_future, 0.0),
                     index=pd.date_range(start=(ts.index[-1].to_period("M") + 1).to_timestamp(), periods=int(periods), freq="MS"))


def legacy_metrics(y_true, y_pred):
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    err = y_pred - y_true
    mape = float(np.mean(np.abs(err[y_true != 0] / y_true[y_true != 0])) * 100)
    rmse = float(np.sqrt(np.mean(err ** 2)))
    mae = float(np.mean(np.abs(err)))
    return {"mape": mape, "rmse": rmse, "mae": mae}


def run_legacy_backtest(ts, profile, horizon=12, step=12, min_train=24):
    """旧方案回测（3 模型 MAPE 倒数融合，与旧版本同口径：无外生因子）。"""
    from capm.backtest import _post_process
    from capm.models import holt_winters_forecast, sarima_forecast

    holiday_cfg = profile.get("holiday", {})
    growth_cfg = profile.get("growth", {})
    spring_dates = profile.get("spring_festival_dates", {})

    def _last_total(train):
        if len(train) < 12:
            return None
        last_year = train.index[-1].year
        y = train[train.index.year == last_year]
        if len(y) == 12:
            return float(y.sum())
        return float(y.mean() * 12)

    results = {"hw": [], "sarima": [], "linear": [], "ensemble": []}
    for cut in range(min_train, len(ts) - horizon + 1, step):
        train, test = ts.iloc[:cut], ts.iloc[cut:cut + horizon]
        if len(test) == 0:
            continue
        hist_total = _last_total(train)
        hw = holt_winters_forecast(train, periods=len(test), trend="add", seasonal="add", seasonal_periods=12)
        sar = sarima_forecast(train, periods=len(test))
        lin = legacy_linear_forecast(train, len(test))
        preds = {
            "hw": _post_process(hw, holiday_cfg, growth_cfg, spring_dates, hist_total).reindex(test.index),
            "sarima": _post_process(sar, holiday_cfg, growth_cfg, spring_dates, hist_total).reindex(test.index),
            "linear": lin.reindex(test.index),
        }
        m = {k: legacy_metrics(test.values, p.values) for k, p in preds.items()}
        inv = {k: 1.0 / v["mape"] for k, v in m.items() if v["mape"] > 0}
        tot = sum(inv.values())
        w = {k: v / tot for k, v in inv.items()} if tot > 0 else {k: 1 / 3 for k in ("hw", "sarima", "linear")}
        ens = sum(preds[k] * w[k] for k in preds)
        for k, v in m.items():
            results[k].append(v)
        results["ensemble"].append(legacy_metrics(test.values, ens.values))
    out = {}
    for k, arr in results.items():
        out[k] = {m: float(np.nanmean([a[m] for a in arr])) for m in ("mape", "rmse", "mae")}
    return out


def main():
    print("=" * 78)
    print("V1.1 新旧算法方案量化回测对比（合成月度序列 2015-2025）")
    print("=" * 78)

    ts = build_synthetic_series()
    print(f"\n数据概况: {len(ts)} 个月 | {ts.index.min().date()} ~ {ts.index.max().date()}")
    print(f"         均值 {ts.mean():,.0f} | 标准差 {ts.std():,.0f} | 年度均值增速约 4.5%")

    cfg = default_config()
    profile = cfg["profiles"]["default"]

    # ---------- 外部因子 ----------
    factors = ExternalDataManager().get_monthly_factors(ts.index, periods=12)
    print(f"外部因子: {factors.shape[1]} 项 ({', '.join(factors.columns)})，"
          f"训练期 {ts.index.min().date()} ~ {ts.index.max().date()}")

    # ---------- 1) 滚动回测 ----------
    print("\n" + "-" * 78)
    print("1) 滚动回测（walk-forward, min_train=24, horizon=12）")
    print("-" * 78)
    legacy = run_legacy_backtest(ts, profile)
    bt_new = rolling_backtest(ts, profile, horizon=12, step=12, min_train=24, factors=factors)
    bt_new_noexog = rolling_backtest(ts, profile, horizon=12, step=12, min_train=24, factors=None)

    header = f"{'模型':<12}{'旧(MAPE%)':>12}{'新(无因子)':>14}{'新(含因子)':>14}"
    print(header)
    print("-" * len(header))
    for key, name in (("hw", "HW"), ("sarima", "SARIMA"), ("linear", "线性(旧)"), ("ensemble", "融合")):
        l = legacy.get(key, {}).get("mape", float("nan"))
        n1 = bt_new_noexog.get("summary", {}).get(key, {}).get("mape", float("nan"))
        n2 = bt_new.get("summary", {}).get(key, {}).get("mape", float("nan"))
        print(f"{name:<12}{l:>12.2f}{n1:>14.2f}{n2:>14.2f}")

    # 新方案融合（BMA 权重）在旧方案融合上的对比
    rec_new = bt_new.get("recommendation", {})
    rec_new_noexog = bt_new_noexog.get("recommendation", {})
    print(f"\n新方案推荐: {rec_new_noexog.get('model')} | 权重 {rec_new_noexog.get('weights')} ({rec_new_noexog.get('weight_method')})")
    print(f"新方案推荐(含外部因子): {rec_new.get('model')} | 权重 {rec_new.get('weights')} ({rec_new.get('weight_method')})")

    # ---------- 2) 样本外 holdout ----------
    print("\n" + "-" * 78)
    print("2) 样本外测试（holdout: 前 80% 训练 → 后 20% 预测）")
    print("-" * 78)
    cut = int(len(ts) * 0.8)
    train, test = ts.iloc[:cut], ts.iloc[cut:]
    ho = holdout_backtest(ts, profile, train_ratio=0.8, factors=factors)
    print(f"训练区间: {ho.get('train_range')} | 测试区间: {ho.get('test_range')}")
    legacy_ho = {}
    from capm.backtest import _post_process

    hw = __import__("capm.models", fromlist=["holt_winters_forecast"]).holt_winters_forecast(train, periods=len(test))
    sar = __import__("capm.models", fromlist=["sarima_forecast"]).sarima_forecast(train, periods=len(test))
    lin = legacy_linear_forecast(train, len(test))
    hist_total = float(train.iloc[-12:].sum()) if len(train) >= 12 else None
    for k, p in (("hw", hw), ("sarima", sar)):
        legacy_ho[k] = legacy_metrics(test.values, _post_process(p, profile.get("holiday", {}), profile.get("growth", {}), profile.get("spring_festival_dates", {}), hist_total).reindex(test.index).values)
    legacy_ho["linear"] = legacy_metrics(test.values, lin.reindex(test.index).values)
    print(f"{'模型':<12}{'旧MAPE%':>12}{'旧RMSE':>14}{'新MAPE%':>12}{'新RMSE':>14}{'MDA':>10}{'TheilU':>10}")
    for key, name in (("hw", "HW"), ("sarima", "SARIMA"), ("ensemble", "融合")):
        l = legacy_ho.get(key, {})
        s = ho.get("summary", {}).get(key, {})
        print(f"{name:<12}{l.get('mape', float('nan')):>12.2f}{l.get('rmse', float('nan')):>14.2f}"
              f"{s.get('mape', float('nan')):>12.2f}{s.get('rmse', float('nan')):>14.2f}"
              f"{s.get('mda', float('nan')):>10.2f}{s.get('theil_u', float('nan')):>10.2f}")
    rec_ho = ho.get("recommendation", {})
    print(f"样本外推荐: {rec_ho.get('model')} | 权重 {rec_ho.get('weights')} ({rec_ho.get('weight_method')})")

    # ---------- 3) 马尔可夫状态分析 ----------
    print("\n" + "-" * 78)
    print("3) 马尔可夫状态转移分析（情景辅助层）")
    print("-" * 78)
    from capm.markov import analyze_regimes

    rg = analyze_regimes(ts)
    if "error" not in rg:
        print(f"当前状态: {rg['current_state']}")
        print(f"状态频率: " + " | ".join(f"{k} {v:.1%}" for k, v in rg["state_freq"].items()))
        print(f"稳态分布: " + " | ".join(f"{k} {v:.1%}" for k, v in rg["steady_state"].items()))
        P = rg["transition_matrix"]
        print("转移矩阵:")
        for i, name in enumerate(["回落", "平稳", "增长"]):
            print(f"  {name} -> {P[i]}")

    # ---------- 4) BMA 与 MAPE 倒数权重对比 ----------
    print("\n" + "-" * 78)
    print("4) 权重策略对比（基于滚动回测残差）")
    print("-" * 78)
    from capm.backtest import recommend_weights_from_backtest
    from capm.bayesian import bma_weights

    errs = bt_new.get("errors", {})
    w_bma = bma_weights({k: v for k, v in errs.items() if k in ("hw", "sarima")})
    w_legacy = {"hw": 0.4, "sarima": 0.3, "linear": 0.3}
    # 归一化旧权重（去掉 linear）
    tot = w_legacy["hw"] + w_legacy["sarima"]
    w_legacy2 = {"hw": w_legacy["hw"] / tot, "sarima": w_legacy["sarima"] / tot}
    print(f"BMA 权重(新):   HW={w_bma.get('hw', 0):.3f}  SARIMA={w_bma.get('sarima', 0):.3f}")
    print(f"旧固定权重:     HW={w_legacy2['hw']:.3f}  SARIMA={w_legacy2['sarima']:.3f}")
    print(f"兼容接口权重:   {recommend_weights_from_backtest(bt_new)}")

    print("\n" + "=" * 78)
    print("对比结论：MAPE 越低越好；MDA 为方向命中率；Theil U<1 表示优于朴素基准。")
    print("=" * 78)


if __name__ == "__main__":
    main()
