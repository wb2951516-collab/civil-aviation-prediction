"""马尔可夫状态转移分析模块（情景分析辅助层）。

设计定位（客观评估结论）
-----------------------
月度旅客运输量的数值预测本质上由季节性与趋势主导，离散状态链对"数值"
预测的边际增益有限；但其在"情景分析"维度有价值：将月度环比增速离散化为
增长/平稳/回落三状态，估计状态转移矩阵与稳态分布，可用于：
1. 生产保障场景下的景气情景判断（下月处于哪个状态的先验概率）；
2. 作为回测报告中模型稳定性的描述性统计；
3. 可选地以状态概率对融合权重做温和调制（默认关闭，避免过度干预）。

本模块不参与默认预测主路径，保持"评估结论决定去留"的客观原则。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# 状态定义（按月度环比增速，%）
GROWTH_THRESHOLDS = {"up": 1.0, "down": -1.0}
STATE_NAMES = ["回落", "平稳", "增长"]  # 索引: 0 回落, 1 平稳, 2 增长


def classify_growth(ts, up_threshold: float = 1.0, down_threshold: float = -1.0) -> np.ndarray:
    """将月度环比增速分类为状态序列：0=回落, 1=平稳, 2=增长（%）。"""
    pct = np.asarray(ts, dtype=float)
    pct = np.diff(pct) / np.abs(pct[:-1]) * 100.0 if len(pct) > 1 else np.array([])
    states = np.zeros(len(pct), dtype=int)
    states[pct > up_threshold] = 2
    states[(pct >= down_threshold) & (pct <= up_threshold)] = 1
    return states


def transition_matrix(states: np.ndarray, n_states: int = 3) -> np.ndarray:
    """频率法估计转移概率矩阵 P[i, j] = P(下一状态 j | 当前状态 i)。"""
    P = np.zeros((n_states, n_states), dtype=float)
    if len(states) < 2:
        return P + np.eye(n_states) / n_states
    for i in range(len(states) - 1):
        P[states[i], states[i + 1]] += 1.0
    row_sums = P.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    P = P / row_sums
    # 无观测行的兜底：均匀
    for i in range(n_states):
        if P[i].sum() == 0:
            P[i] = 1.0 / n_states
    return P


def steady_state(P: np.ndarray) -> np.ndarray:
    """马尔可夫链稳态分布（转移矩阵特征值 1 的左特征向量）。"""
    n = P.shape[0]
    try:
        eigvals, eigvecs = np.linalg.eig(P.T)
        idx = int(np.argmin(np.abs(eigvals - 1.0)))
        v = np.real(eigvecs[:, idx])
        s = v.sum()
        if s != 0 and np.all(np.isfinite(v)):
            pi = v / s
            if np.all(pi >= -1e-9):
                return np.clip(pi, 0.0, None) / np.clip(pi, 0.0, None).sum()
    except Exception:
        pass
    return np.full(n, 1.0 / n)


def forecast_state_distribution(P: np.ndarray, current_state: int, periods: int) -> np.ndarray:
    """从当前状态出发，逐期演化状态分布（K×n_states）。"""
    n = P.shape[0]
    dist = np.zeros(n)
    dist[int(current_state)] = 1.0
    out = [dist.copy()]
    for _ in range(1, int(periods)):
        dist = dist @ P
        out.append(dist)
    return np.asarray(out)


def analyze_regimes(ts, periods: int = 12, up_threshold: float = 1.0, down_threshold: float = -1.0) -> Dict[str, Any]:
    """综合状态转移分析（供报告/可视化使用）。"""
    states = classify_growth(ts, up_threshold, down_threshold)
    if len(states) == 0:
        return {"error": "数据不足"}
    P = transition_matrix(states)
    pi = steady_state(P)
    current = int(states[-1])
    dist = forecast_state_distribution(P, current, periods)
    counts = np.bincount(states, minlength=3)
    return {
        "state_counts": {STATE_NAMES[i]: int(counts[i]) for i in range(3)},
        "state_freq": {STATE_NAMES[i]: float(counts[i] / len(states)) for i in range(3)},
        "transition_matrix": P.tolist(),
        "steady_state": {STATE_NAMES[i]: float(pi[i]) for i in range(3)},
        "current_state": STATE_NAMES[current],
        "forecast_distribution": dist.tolist(),
        "month_labels": [str(i + 1) for i in range(int(periods))],
    }


def weight_modulation(weights: Dict[str, float], state_probs: np.ndarray, strength: float = 0.0) -> Dict[str, float]:
    """按状态概率温和调制融合权重（默认 strength=0 不启用）。

    strength ∈ [0, 1]：0 不调制；>0 时若"增长/回落"状态概率高，则略微
    放大/收缩 SARIMA（对趋势更敏感）的权重。该调制默认关闭，仅在显式
    评估确认有增益后启用。
    """
    w = dict(weights)
    if strength <= 0 or len(state_probs) == 0:
        return w
    up_p, down_p = float(state_probs[2]), float(state_probs[0])
    direction = up_p - down_p  # (-1, 1)
    delta = strength * direction * 0.15  # 最大 ±15% 的权重扰动
    w_sarima = float(w.get("sarima", 0.5)) + delta
    w_hw = float(w.get("hw", 0.5)) - delta
    w_hw = max(0.05, min(0.95, w_hw))
    w_sarima = max(0.05, min(0.95, w_sarima))
    total = w_hw + w_sarima
    return {"hw": w_hw / total, "sarima": w_sarima / total}
