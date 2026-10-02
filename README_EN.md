# CAPM — Civil Aviation Passenger Traffic Prediction

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![Release](https://img.shields.io/badge/Release-v1.4.0-orange.svg)](https://github.com/wb2951516-collab/civil-aviation-prediction/releases)

**English** | [中文](README.md)

A desktop application for forecasting monthly civil aviation passenger traffic: curated statistical models + an intervention engine + a Kalman-filter state-space member + automatic ensemble weighting via Bayesian Model Averaging (BMA), with built-in walk-forward backtesting, scenario analysis, and a ready-to-use GUI.

https://github.com/user-attachments/assets/a080922d-25e9-4a22-8c77-83fe90cdc896

> Silent demo above. The narrated version is available as a [Release asset](https://github.com/wb2951516-collab/civil-aviation-prediction/releases/tag/v1.3.2).

### Highlights

- **Curated model set** — Holt-Winters, SARIMA/SARIMAX and a Kalman-filter UC (unobserved components) member, selected through empirical backtesting (weaker models such as linear regression were deliberately removed)
- **Intervention engine** — holidays (incl. lunar calendar) and shock events (e.g. COVID) modeled as SARIMAX exogenous variables instead of post-hoc multiplicative corrections
- **BMA ensemble** — posterior model weights computed from backtest residuals; no manual tuning required
- **Quantified validation** — rolling backtest and holdout with MAE / RMSE / MAPE / MDA / Theil U / Ljung-Box
- **Scenario layer** — Markov state-transition analysis for boom/stable/decline regimes
- **Management console** — online official macro data (GDP, ASK) via akshare as exogenous factors

### Results (2015–2025 monthly series with pandemic shocks, rolling backtest)

| Metric | Legacy pipeline | Intervention engine (default) |
|--------|-----------------|-------------------------------|
| Stable-period ensemble MAPE | 4.92% | **2.23%** |
| Shock-period (2020–2022) ensemble MAPE | 173.32% | **9.64%** |
| Holdout ensemble MAPE | 38.24% | **4.39%** |

### V1.4 Kalman-filter integration (official CAAC monthly load-factor series, Feb 2006 – Aug 2026, 247 months, walk-forward backtest)

| Metric | Two-member ensemble (V1.3) | Three-member ensemble (V1.4, +Kalman) |
|--------|---------------------------|----------------------------------------|
| Ensemble MAPE | 4.02% | **3.61% (−10.3% relative)** |
| Ensemble RMSE | 3.48 | **3.17** |
| Theil U | 1.15 | **0.99 (beats naive benchmark)** |

### Install

- **Windows**: download `CAPM-Setup-1.4.0.exe` from [Releases](https://github.com/wb2951516-collab/civil-aviation-prediction/releases)
- **From source**: `pip install -r requirements.txt && python CAPM.py` (Windows / macOS / Linux)

### License

GPL-3.0. See [LICENSE](LICENSE). The full algorithm design rationale is documented in [docs/ALGORITHM_REDESIGN.md](docs/ALGORITHM_REDESIGN.md) (Chinese); the V1.4 Kalman integration acceptance report in [docs/KALMAN_GATE_V1.4.md](docs/KALMAN_GATE_V1.4.md) (Chinese).
