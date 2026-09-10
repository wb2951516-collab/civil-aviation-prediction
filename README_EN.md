# CAPM — Civil Aviation Passenger Traffic Prediction

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![Release](https://img.shields.io/badge/Release-v1.3.2-orange.svg)](https://github.com/wb2951516-collab/civil-aviation-prediction/releases)

**English** | [中文](README.md)

A desktop application for forecasting monthly civil aviation passenger traffic: curated statistical models + an intervention engine + automatic ensemble weighting via Bayesian Model Averaging (BMA), with built-in walk-forward backtesting, scenario analysis, and a ready-to-use GUI.

https://github.com/user-attachments/assets/b8ae0fcb-2463-436f-8453-cf0a3b5714d4

> Silent demo above. The narrated version is available as a [Release asset](https://github.com/wb2951516-collab/civil-aviation-prediction/releases/tag/v1.3.2).

### Highlights

- **Curated model set** — Holt-Winters and SARIMA/SARIMAX, selected through empirical backtesting (weaker models such as linear regression were deliberately removed)
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

### Install

- **Windows**: download `CAPM-Setup-1.3.2.exe` from [Releases](https://github.com/wb2951516-collab/civil-aviation-prediction/releases)
- **From source**: `pip install -r requirements.txt && python CAPM.py` (Windows / macOS / Linux)

### License

GPL-3.0. See [LICENSE](LICENSE). The full algorithm design rationale is documented in [docs/ALGORITHM_REDESIGN.md](docs/ALGORITHM_REDESIGN.md) (Chinese).
