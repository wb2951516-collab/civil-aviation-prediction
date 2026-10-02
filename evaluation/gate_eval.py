# -*- coding: utf-8 -*-
"""卡尔曼滤波融入效果评估脚本（严格门槛验收用）。

数据：
  ① 主评估序列：CAAC 真实月度客座率（akshare macro_china_passenger_load_factor，
     2006.02 起约 244 个月，含春运/暑运季节性、长期趋势与 2020 疫情结构断点）；
  ② 稳健性序列：内置 ASK 月度近似序列（2015-2025，量纲形态接近旅客运输量）。

协议（与 auto 模式完全一致）：
  rolling_backtest(horizon=12, step=12, min_train=24, engine='intervention')

用法（必须在项目根目录执行，输出写入 evaluation/results/）：
  python -m evaluation.gate_eval baseline   # 基线（HW+SARIMA 两成员）
  python -m evaluation.gate_eval gate       # 三成员（含卡尔曼）对比 + 门槛判定
  python -m evaluation.gate_eval gate --phase2  # 追加 KF 自适应融合器对比
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def _dump_json(rel_parts, payload):
    out = Path(*rel_parts)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"已保存: {out}")


def fetch_caac_load_factor():
    """CAAC 真实月度客座率（%）。网络不可用时抛异常，由调用方决定回退。

    官方月度序列存在个别缺失月（如部分年份 2 月并入发布），按连续月度索引
    重排并对缺失月线性插值。
    """
    import akshare as ak
    import pandas as pd

    df = ak.macro_china_passenger_load_factor()
    rows = []
    for _, r in df.iterrows():
        stat = str(r["统计时间"])  # 形如 '2026.8'
        year, month = stat.split(".")
        rows.append((pd.Timestamp(int(year), int(month), 1), float(r["客座率"])))
    rows.sort()
    raw = pd.Series([v for _, v in rows], index=pd.DatetimeIndex([t for t, _ in rows]))
    raw = raw[~raw.index.duplicated(keep="last")]
    full_idx = pd.date_range(raw.index[0], raw.index[-1], freq="MS")
    aligned = raw.reindex(full_idx).interpolate(method="time").ffill().bfill()
    return aligned.rename("value")


def fallback_ask_series():
    """内置 ASK 月度近似序列（离线兜底/稳健性复核）。"""
    import pandas as pd

    from capm.datasource import _builtin_ask_frame

    s = _builtin_ask_frame()["ask"].astype(float)
    s.index = pd.DatetimeIndex(s.index, freq="MS")
    return s


def load_profile():
    """优先读用户实际配置（AppPaths.config_path()），否则用默认配置。"""
    from capm.app_paths import AppPaths
    from capm.config_store import default_config

    profile = default_config().get("profiles", {}).get("default", {})
    try:
        data = json.loads(Path(AppPaths().config_path()).read_text(encoding="utf-8"))
        saved = data.get("profiles", {}).get(data.get("active_profile", "default"))
        if isinstance(saved, dict) and saved:
            profile.update(saved)
    except Exception:
        pass
    profile.setdefault("spring_festival_dates", {})
    return profile


def load_factors(ts):
    try:
        from capm.datasource import ExternalDataManager

        return ExternalDataManager().get_monthly_factors(ts.index, periods=12)
    except Exception:
        return None


def run_backtest(ts, profile, factors, members):
    """members: 'baseline2'（HW+SARIMA）或 'kalman3'（HW+SARIMA+卡尔曼）。"""
    from capm.backtest import rolling_backtest

    member_list = ["hw", "sarima"] if members == "baseline2" else ["hw", "sarima", "kalman"]
    return rolling_backtest(
        ts, profile, horizon=12, step=12, min_train=24, factors=factors, engine="intervention", members=member_list
    )


def kf_adaptive_fuse(window_records, prior_weights=None, q: float = 1e-3, r0: float = 10.0, r_alpha: float = 0.1):
    """Phase 2：卡尔曼滤波自适应融合器（Granger-Ramanathan 状态空间形式）。

    状态 w 为成员组合权重（随机游走 + 过程噪声 q，允许权重随市场阶段漂移），
    观测方程 y_t = f_t' w + v_t（f_t 为当月各成员预测，v 噪声方差 R 在线估计）。
    每个窗口的融合发生在观测其真实值之前（严格无前视泄漏）；窗口结束后以
    该窗口 12 个月的 (y_t, f_t) 做序贯卡尔曼更新，权重随市场阶段自适应。

    window_records: 逐窗口 [{"preds": {m: array}, "actual": array}]
    返回 (fused_list, final_weights)
    """
    import numpy as np

    members = list(window_records[0]["preds"].keys())
    m = len(members)
    w = np.array([prior_weights.get(k, 1.0 / m) for k in members], dtype=float)
    w = w / w.sum()
    P = np.eye(m) * 0.05
    Q = np.eye(m) * q
    R = None

    fused, weights_hist = [], []
    for rec in window_records:
        F = np.column_stack([rec["preds"][k] for k in members])  # (h, m)
        y = np.asarray(rec["actual"], dtype=float)
        P_pred = P + Q
        fused.append(F @ w)  # 观测前融合
        if R is None:
            R = r0
        for t in range(len(y)):
            f = F[t]
            S = float(f @ P_pred @ f) + R
            if S <= 0 or not np.isfinite(S):
                continue
            K = (P_pred @ f) / S
            innov = float(y[t] - f @ w)
            w = w + K * innov
            P_pred = P_pred - np.outer(K, f @ P_pred)
            R = (1.0 - r_alpha) * R + r_alpha * innov**2
        P = (P_pred + P_pred.T) / 2.0
        w = np.clip(w, 0.0, None)
        if w.sum() <= 0 or not np.isfinite(w.sum()):
            w = np.ones(m) / m
        else:
            w = w / w.sum()
        weights_hist.append({k: float(v) for k, v in zip(members, w)})
    return fused, {k: float(v) for k, v in zip(members, w)}, weights_hist


def _collect_window_records(ts, profile, factors, members_list):
    """复用 rolling_backtest 的窗口划分，收集逐窗口成员预测与真实值。"""
    import pandas as pd

    from capm.models import (
        holt_winters_forecast,
        kalman_intervention_forecast,
        sarimax_intervention_forecast,
    )

    from capm.backtest import _last_complete_year_total, _slice_factors

    holiday_cfg = profile.get("holiday", {})
    model_cfg = profile.get("model", {})
    spring_festival_dates = profile.get("spring_festival_dates", {})
    sarima_cfg = model_cfg.get("sarima", {})
    hw_cfg = model_cfg.get("holt_winters", {})

    records = []
    total_len = len(ts)
    min_train, horizon, step = 24, 12, 12
    if total_len < min_train + horizon:
        return records
    for cut in range(min_train, total_len - horizon + 1, step):
        train = ts.iloc[:cut]
        test = ts.iloc[cut : cut + horizon]
        if len(test) == 0:
            continue
        test_index = test.index
        exog_train = exog_test = exog_full = None
        if factors is not None:
            exog_train, _ = _slice_factors(factors, train.index)
            exog_test, _ = _slice_factors(factors, test_index)
            if exog_train is not None and exog_test is not None:
                try:
                    exog_full = pd.concat([exog_train, exog_test])
                except Exception:
                    exog_full = None
        preds = {}
        hw_out = holt_winters_forecast(
            train, periods=len(test),
            trend=hw_cfg.get("trend", "add"), seasonal=hw_cfg.get("seasonal", "add"),
            seasonal_periods=int(hw_cfg.get("seasonal_periods", 12)),
            auto_tune=bool(hw_cfg.get("auto_tune", False)),
        )
        preds["hw"] = hw_out.forecast.reindex(test_index).values.astype(float)
        if "sarima" in members_list:
            s_out = sarimax_intervention_forecast(
                train, periods=len(test),
                spring_festival_dates=spring_festival_dates,
                holiday_cfg=holiday_cfg, include_covid=True,
                order=tuple(sarima_cfg.get("order", (1, 1, 1))),
                seasonal_order=tuple(sarima_cfg.get("seasonal_order", (1, 1, 1, 12))),
                exog_data=exog_full,
            )
            preds["sarima"] = s_out.forecast.reindex(test_index).values.astype(float)
        if "kalman" in members_list:
            k_out = kalman_intervention_forecast(
                train, periods=len(test),
                spring_festival_dates=spring_festival_dates,
                holiday_cfg=holiday_cfg, include_covid=True,
                exog_data=exog_full,
            )
            preds["kalman"] = k_out.forecast.reindex(test_index).values.astype(float)
        records.append({"window": [test_index[0].strftime("%Y-%m"), test_index[-1].strftime("%Y-%m")], "preds": preds, "actual": test.values.astype(float)})
    return records


def _metrics_of(y, p):
    from capm.backtest import _metrics

    m = _metrics(np.asarray(y, dtype=float), np.asarray(p, dtype=float))
    return {"mae": m.mae, "rmse": m.rmse, "mape": m.mape, "mda": m.mda, "theil_u": m.theil_u}


def _load_json(rel_parts):
    return json.loads((Path(*rel_parts)).read_text(encoding="utf-8"))


def cmd_gate(phase2: bool):
    from capm.backtest import rolling_backtest

    baseline = _load_json(("evaluation", "results", "baseline.json"))
    profile = load_profile()
    factor_policy = {"caac_load_factor": True, "builtin_ask": False}
    output = {}
    for name, fetch in (("caac_load_factor", fetch_caac_load_factor), ("builtin_ask", fallback_ask_series)):
        try:
            ts = fetch()
        except Exception as e:
            print(f"[{name}] 数据获取失败: {e}")
            continue
        base_res = baseline.get(name, {}).get("result", {})
        base_ens = float(base_res.get("summary", {}).get("ensemble", {}).get("mape", float("nan")))
        print(f"[{name}] 样本: {ts.index[0]:%Y-%m} ~ {ts.index[-1]:%Y-%m}  共 {len(ts)} 个月")
        factors = load_factors(ts) if factor_policy.get(name, True) else None
        res = rolling_backtest(ts, profile, horizon=12, step=12, min_train=24, factors=factors, engine="intervention", members=["hw", "sarima", "kalman"])
        print(_fmt_summary(f"三成员(含卡尔曼) - {name}", res))

        entry = {"three_member": res, "baseline_ensemble_mape": base_ens}
        new_ens = float(res.get("summary", {}).get("ensemble", {}).get("mape", float("nan")))
        if base_ens == base_ens and new_ens == new_ens and base_ens > 0:
            rel = (base_ens - new_ens) / base_ens * 100.0
            absp = base_ens - new_ens
            entry["relative_improve_pct"] = rel
            entry["absolute_improve_pp"] = absp
            entry["gate_pass"] = bool(rel >= 3.0 or absp >= 0.3)
            print(f"  门槛: 基线集成 MAPE={base_ens:.3f}% → 三成员 {new_ens:.3f}%  "
                  f"相对改善 {rel:.2f}%  绝对改善 {absp:.3f}pp  → {'通过' if entry['gate_pass'] else '未通过'}")

        if phase2 and name == "caac_load_factor":
            try:
                records = _collect_window_records(ts, profile, factors, ["hw", "sarima", "kalman"])
                prior = (res.get("recommendation") or {}).get("weights") or {}
                fused, final_w, weights_hist = kf_adaptive_fuse(records, prior_weights=prior)
                all_y = np.concatenate([np.asarray(r["actual"]) for r in records])
                all_f = np.concatenate([np.asarray(p) for p in fused])
                kf_metrics = _metrics_of(all_y, all_f)
                entry["phase2_kf_fusion"] = {
                    "summary": kf_metrics,
                    "final_weights": final_w,
                    "weights_by_window": weights_hist,
                }
                print(_fmt_summary("Phase2 KF自适应融合 - " + name, {"summary": {"ensemble_kf": kf_metrics}}))
                if base_ens == base_ens:
                    rel2 = (base_ens - kf_metrics["mape"]) / base_ens * 100.0
                    print(f"  Phase2 对基线集成: 相对改善 {rel2:.2f}%")
            except Exception as e:
                entry["phase2_kf_fusion_error"] = str(e)
                print(f"  Phase2 KF融合失败: {e}")

        output[name] = entry
    _dump_json(("evaluation", "results", "gate.json"), output)


def _fmt_summary(title, result):
    lines = [f"== {title} =="]
    if "error" in result:
        lines.append(f"  ERROR: {result['error']}")
        return "\n".join(lines)
    for k in ("hw", "sarima", "kalman", "ensemble", "ensemble_kf"):
        if k in result.get("summary", {}):
            s = result["summary"][k]
            lines.append(
                f"  {k:>12s}: MAPE={s['mape']:6.3f}%  RMSE={s['rmse']:8.3f}  "
                f"MDA={s['mda']:6.3f}  TheilU={s['theil_u']:6.4f}"
            )
    rec = result.get("recommendation") or {}
    if rec:
        lines.append(f"  推荐: {rec.get('model')}  权重: {rec.get('weights')}  ({rec.get('weight_method')})")
    return "\n".join(lines)


def cmd_baseline():
    from capm.backtest import rolling_backtest

    profile = load_profile()
    results = {}
    # builtin_ask 目标序列与外生变量 ask 同源（同一内置公式），直接喂入会造成
    # 数据泄漏（SARIMA 借外生变量"完美预测"目标），因此该序列不使用外生因子。
    factor_policy = {"caac_load_factor": True, "builtin_ask": False}
    for name, fetch in (("caac_load_factor", fetch_caac_load_factor), ("builtin_ask", fallback_ask_series)):
        try:
            ts = fetch()
        except Exception as e:
            print(f"[{name}] 数据获取失败: {e}")
            continue
        print(f"[{name}] 样本: {ts.index[0]:%Y-%m} ~ {ts.index[-1]:%Y-%m}  共 {len(ts)} 个月")
        factors = load_factors(ts) if factor_policy.get(name, True) else None
        res = rolling_backtest(ts, profile, horizon=12, step=12, min_train=24, factors=factors, engine="intervention")
        results[name] = {"sample": [str(ts.index[0].date()), str(ts.index[-1].date()), int(len(ts))], "result": res}
        print(_fmt_summary(f"基线(两成员) - {name}", res))
    _dump_json(("evaluation", "results", "baseline.json"), results)


def main():
    parser = argparse.ArgumentParser(description="卡尔曼滤波融入效果评估")
    parser.add_argument("phase", choices=["baseline", "gate"])
    parser.add_argument("--phase2", action="store_true", help="追加 KF 自适应融合器对比")
    args = parser.parse_args()
    if args.phase == "baseline":
        cmd_baseline()
    else:
        cmd_gate(args.phase2)


if __name__ == "__main__":
    main()
