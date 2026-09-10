# CAPM 民航旅客运输量预测系统

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](packaging/README.md)
[![Release](https://img.shields.io/badge/Release-v1.3.2-orange.svg)](https://github.com/wb2951516-collab/civil-aviation-prediction/releases)

**[English](README_EN.md)** | 中文

面向民航运输规划场景的月度旅客运输量预测系统：精选统计模型 + 干预引擎 + 贝叶斯模型平均（BMA）自动融合，内置量化回测与情景分析，提供开箱即用的桌面 GUI。

https://github.com/user-attachments/assets/b8ae0fcb-2463-436f-8453-cf0a3b5714d4

> 上方为功能演示（静音），完整有声解说版见 [Release 附件](https://github.com/wb2951516-collab/civil-aviation-prediction/releases/tag/v1.3.2)。

---

## 一、项目简介

民航月度客流受**春运/暑运双峰季节性、法定节假日、疫情等结构冲击、宏观经济增长**多重因素叠加影响，传统单模型预测在结构突变期误差急剧放大。CAPM 以"精选算法 + 干预引擎 + 自动融合"为核心思路：

| 模块 | 作用 |
|------|------|
| 精选模型集合 | Holt-Winters、SARIMA/SARIMAX（经实证淘汰线性回归等弱势模型） |
| 干预引擎 | 节假日（含农历）与冲击事件作为 SARIMAX 外生变量建模，替代后处理修正 |
| BMA 融合 | 贝叶斯模型平均按回测似然自动分配权重，无需人工调参 |
| 增长合理性校准 | 对异常增长率分级告警而非强制覆盖，避免二次失真 |
| 量化回测 | 滚动回测 / 样本外测试，MAE、RMSE、MAPE、MDA、Theil U、Ljung-Box 残差检验 |
| 马尔可夫情景分析 | 增长/平稳/回落状态转移，输出景气情景参考（不干预主预测） |
| 管理控制台 | akshare 在线接入官方宏观/行业数据（GDP、ASK 等）作为外生因子 |
| 桌面 GUI | 置信带可视化、报告导出、内置算法手册，一线人员开箱即用 |

### 核心实证效果（含疫情冲击的 2015–2025 合成月度序列，滚动回测）

| 指标 | 传统管线 | 干预引擎（默认） |
|------|---------|----------------|
| 平稳期融合 MAPE | 4.92% | **2.23%** |
| 冲击期（2020–2022）融合 MAPE | 173.32% | **9.64%** |
| 样本外 holdout 融合 MAPE | 38.24% | **4.39%** |

> 算法决策的完整实证依据（模型淘汰理由、马尔可夫/贝叶斯方案评估、多窗口稳健性验证）见 [docs/ALGORITHM_REDESIGN.md](docs/ALGORITHM_REDESIGN.md)。

## 二、安装

### 方式一：Windows 安装包（推荐）

从 [Releases](https://github.com/wb2951516-collab/civil-aviation-prediction/releases) 下载 `CAPM-Setup-1.3.2.exe`，双击安装即可（简体中文安装向导，自带运行环境，无需配置 Python）。

### 方式二：源码运行

```bash
git clone https://github.com/wb2951516-collab/civil-aviation-prediction.git
cd civil-aviation-prediction
pip install -r requirements.txt
python CAPM.py
```

适用于 Windows / macOS / Linux（GUI 基于 tkinter）。

## 三、快速开始

1. 启动后进入主界面，导入月度旅客运输量历史数据（时间序列）；
2. 模型选择保持默认的**自动推荐**：系统自动执行滚动回测，按 BMA 权重选出最优模型/权重，一键应用；
3. 查看预测结果与置信带，关注增长率合理性告警；
4. 需要外部因子时，在管理控制台接入 GDP / ASK 数据启用 SARIMAX 外生变量；
5. 一键导出分析报告（含各模型指标对比、误差水平与权重依据）。

## 四、项目结构

```
CAPM.py                  # GUI 主程序（入口）
capm/
  ├── models.py          # 模型层：HW / SARIMA / 融合
  ├── backtest.py        # 量化回测引擎（滚动 / holdout）
  ├── bayesian.py       # BMA 权重与贝叶斯回归
  ├── markov.py         # 马尔可夫状态转移情景分析
  ├── growth.py         # 增长合理性校验与告警
  ├── holiday.py        # 节假日（含农历）效应
  ├── datasource.py     # akshare 官方数据源接入
  └── ...               # 单实例、主题、日志等工程模块
docs/                    # 算法重设计评估报告
packaging/               # Windows/macOS/Linux 安装包工程
```

## 五、算法说明（摘要）

- **为什么移除线性回归**：滚动回测 MAPE 13.40% 显著劣于 HW（11.21%）与 SARIMA（11.81%），且外推对端点敏感、无法刻画月度强季节性；
- **为什么用 BMA 而非固定权重**：BMA 利用回测残差完整分布（二阶矩）计算后验权重，对离群误差更稳健；实证中自动将冲击期表现差的 SARIMA 权重压至 0.05，无需人工干预；
- **为什么节假日进 exog 而非后处理**：乘法修正叠加是传统管线冲击期 173% 误差的主要来源；纳入 SARIMAX 外生变量后同期误差降至 9.64%；
- **模型边界（如实声明）**：任何统计模型都无法仅凭历史序列预测结构性恢复，跨恢复期场景请结合情景分析与人工判断，系统报告始终如实展示误差水平。

## 六、从源码构建安装包

详见 [packaging/README.md](packaging/README.md)。Windows 构建流程：

```powershell
pyinstaller CAPM.spec                        # PyInstaller 打包
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" /DAppVersion=1.3.2 packaging\windows\capm.iss
```

## 七、许可证

本项目基于 [GPL-3.0](LICENSE) 许可证开源。

版权所有 © 2026 SuperM
