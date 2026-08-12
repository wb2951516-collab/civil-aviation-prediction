"""贝叶斯方法模块：贝叶斯模型平均（BMA）与贝叶斯岭回归。

BMA 原理
--------
设滚动回测产生模型 m 的合并残差序列 e_m。在残差服从零均值高斯分布
（方差 σ_m² 未知）的假设下，模型 m 的边际似然（积分掉 σ²）近似为
    log L_m ≈ -n_m/2 * log(2π σ̂_m²) - n_m/2
其中 σ̂_m 为残差标准差（ML 估计），n_m 为样本量。
后验权重
    w_m ∝ π_m * exp(temperature * log L_m)
π_m 为先验（默认均匀），temperature 控制权重差异强度（=1 为标准贝叶斯）。

相比 MAPE 倒数法（仅利用平均绝对百分比误差的一阶矩），BMA 使用完整残差
分布（二阶矩），小样本下更稳健，并可通过先验/下限防止权重退化。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)


def _as_array(values) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return arr[np.isfinite(arr)]


def gaussian_log_likelihood(errors: np.ndarray) -> float:
    """零均值高斯 ML 对数似然（省略与模型无关的常数项）。"""
    e = _as_array(errors)
    n = len(e)
    if n == 0:
        return float("-inf")
    var = float(np.mean(e**2))
    if var <= 0 or var != var:
        return float("-inf")
    return -0.5 * n * (np.log(2.0 * np.pi * var) + 1.0)


def bma_weights(
    error_dict: Dict[str, Any],
    prior: Optional[Dict[str, float]] = None,
    floor: float = 0.05,
    temperature: float = 1.0,
) -> Dict[str, float]:
    """贝叶斯模型平均权重。

    参数
    ----
    error_dict : {"model": 残差序列（array-like）}
    prior      : 可选先验权重字典（默认均匀）
    floor      : 每个模型权重下限（防退化）
    temperature: 权重差异强度（1.0 为标准后验；<1 更保守，>1 更自信）

    返回
    ----
    {"model": 权重}，归一化且每项 >= floor。
    """
    if not error_dict:
        return {}
    names = list(error_dict.keys())
    log_likes = []
    priors = []
    for m in names:
        err = error_dict.get(m)
        if err is None or len(_as_array(err)) == 0:
            log_likes.append(float("-inf"))
        else:
            log_likes.append(gaussian_log_likelihood(err))
        priors.append(float(prior.get(m, 1.0)) if prior else 1.0)

    priors = np.asarray(priors, dtype=float)
    log_likes = np.asarray(log_likes, dtype=float)

    # 归一化先验
    if priors.sum() <= 0:
        priors = np.ones_like(priors)
    priors = priors / priors.sum()

    # 数值稳定 softmax（减去最大值）
    scaled = temperature * log_likes + np.log(priors + 1e-12)
    scaled = scaled - np.max(scaled)
    weights = np.exp(scaled)
    total = weights.sum()
    if total <= 0 or not np.isfinite(total):
        weights = priors.copy()
        total = weights.sum()

    # 下限保护：低于 floor 的模型权重被抬升并重新归一化
    weights = np.maximum(weights / total, floor)
    weights = weights / weights.sum()
    return {m: float(w) for m, w in zip(names, weights)}


def bayesian_ridge_coefs(X, y, alpha: float = 1.0):
    """贝叶斯岭回归（高斯先验 N(0, 1/alpha)），返回 (系数, 截距)。

    闭式解：β = (X'X + λI)^{-1} X'y（λ=alpha），对共线/小样本外生变量
    （GDP、ASK）的系数估计提供正则化。
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float).ravel()
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    n = len(y)
    if n < 2 or len(X) != n:
        raise ValueError("X 与 y 长度不一致或样本不足")
    X1 = np.column_stack([np.ones(n), X])
    k = X1.shape[1]
    ridge = np.eye(k)
    ridge[0, 0] = 0.0  # 截距不惩罚
    try:
        coef_all = np.linalg.solve(X1.T @ X1 + alpha * ridge, X1.T @ y)
    except np.linalg.LinAlgError:
        coef_all = np.linalg.lstsq(X1.T @ X1 + alpha * ridge, X1.T @ y, rcond=None)[0]
    intercept = float(coef_all[0])
    coefs = np.asarray(coef_all[1:], dtype=float)
    return coefs, intercept


def factor_adjusted_forecast(
    base_forecast,
    factor_data,
    coefs,
    intercept: float = 0.0,
    scale: float = 1.0,
):
    """按外生因子对基础预测做乘性修正。

    forecast_i * (1 + intercept + Σ coef_j * (factor_ij - 历史均值_j)) / scale
    其中 factor 采用去均值处理，保证修正项围绕 1 波动。
    """
    import pandas as pd

    base = pd.Series(base_forecast).astype(float)
    if factor_data is None or len(factor_data) == 0:
        return base
    factor_df = pd.DataFrame(factor_data)
    means = factor_df.mean()
    adj = np.ones(len(base))
    for j, name in enumerate(factor_df.columns):
        if j >= len(coefs):
            break
        centered = factor_df[name].values - float(means[name])
        adj = adj * (1.0 + float(coefs[j]) * centered)
    result = base * adj
    return result.clip(lower=0.0)
