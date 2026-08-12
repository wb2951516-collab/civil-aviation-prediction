# 民航旅客运输量预测模型 - 双版本视频生成项目

## 📋 项目概述

本项目提供了两个不同版本的科学演示视频，用于展示民航旅客运输量预测模型的核心数学原理。

---

## ✅ 版本一：Manim 动画版本（已完成）

### 🎥 视频信息
- **文件路径**: `media/videos/tutorial/1080p60/CAPMTutorial.mp4`
- **文件大小**: 3.18 MB
- **分辨率**: 1920×1080 (1080p)
- **帧率**: 60fps
- **时长**: 约 2-3 分钟

### 📁 相关文件
- **主脚本**: `capm_manim/scenes/tutorial.py`
- **配置文件**: `capm_manim/manim.cfg`
- **主题组件**: `capm_manim/components/theme.py`
- **其他场景**: `capm_manim/scenes/` 目录下的其他场景文件

### 🎬 视频内容结构
1. **开篇引入** - 项目介绍和目标
2. **工作流程** - 完整的预测流水线展示
3. **模型预测** - 三模型并行（Linear/Holt-Winters/SARIMA）
4. **加权融合** - 集成学习原理
5. **节假日效应** - 春运等特殊时期修正
6. **增长率校准** - 年度总量调整
7. **结果输出** - 表格和导出功能
8. **总结回顾** - 项目核心价值

### 🚀 如何重新渲染
```powershell
# 在项目根目录执行
.\.venv\Scripts\python.exe -m manim --config_file .\capm_manim\manim.cfg -qh .\capm_manim\scenes\tutorial.py CAPMTutorial
```

---

## 🔄 版本二：AI 视频生成版本（替代方案）

### 📌 说明
由于项目中没有找到 "seed2.0" 模型的相关信息，这里提供几种可行的替代方案：

#### 方案 A：基于现有 Manim 视频的二次创作
使用 AI 视频编辑工具（如 Runway、Pika、Sora 等）对现有的 Manim 视频进行风格转换或增强。

#### 方案 B：使用其他 Python 动画库
- **Matplotlib 动画** + FFmpeg
- **MoviePy** 进行视频合成
- **Pygame** 制作简单动画

#### 方案 C：使用 AI 视频生成 API
- OpenAI Sora API
- Runway Gen-3 API
- Pika Labs API
- Google Veo API

### 🎯 推荐实现方案

考虑到项目的完整性和可复现性，我推荐使用 **Matplotlib + MoviePy** 来创建一个独立的动画版本，不依赖 Manim。

---

## 📊 项目文件结构

```
Civil aviation passenger traffic volume prediction model/
├── capm_manim/                    # Manim 动画库
│   ├── scenes/                    # 动画场景
│   │   ├── tutorial.py            # 主教程场景
│   │   ├── intro.py
│   │   ├── architecture.py
│   │   ├── modeling.py
│   │   ├── holiday_effect.py
│   │   ├── growth_adjustment.py
│   │   └── ...
│   ├── components/                # 可复用组件
│   │   ├── theme.py              # 主题配置
│   │   ├── charts.py             # 图表组件
│   │   └── ...
│   └── manim.cfg                 # Manim 配置
├── media/                         # 渲染输出目录
│   └── videos/
│       └── tutorial/
│           └── 1080p60/
│               └── CAPMTutorial.mp4  # ✅ 已生成的视频
├── capm/                          # 核心预测模型
│   ├── models.py                 # 预测算法
│   ├── holiday.py                # 节假日处理
│   └── growth.py                 # 增长率处理
├── check_deps.py                 # 依赖检查脚本
├── check_video_info.py           # 视频信息检查
└── PROJECT_SUMMARY.md            # 本文件
```

---

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| 动画引擎 | Manim Community v0.19.1 |
| 预测模型 | Linear / Holt-Winters / SARIMA |
| 数据处理 | Pandas / NumPy |
| 统计建模 | Statsmodels |
| 可视化 | Matplotlib (内置) |

---

## 📝 核心数学原理

### 1. 线性回归模型
```
y = intercept + slope × x
```

### 2. Holt-Winters 指数平滑
- 水平（Level）、趋势（Trend）、季节性（Seasonality）三重要素

### 3. SARIMA 模型
- 季节性自回归综合移动平均模型

### 4. 加权融合
```
ŷ = w₁·HW + w₂·SARIMA + w₃·Linear
```
其中权重归一化：w₁ + w₂ + w₃ = 1

### 5. 节假日效应系数
```
系数 = 1 + (春运天数/月天数) × (spring_effect - 1)
```

---

## 🎯 下一步建议

1. **验证 Manim 视频** - 观看并确认内容完整
2. **选择版本二方案** - 根据可用资源选择实现方式
3. **质量对比** - 对比两个版本的视觉效果和内容完整性

---

## 📞 技术支持

如有问题，请检查：
1. 虚拟环境是否激活
2. 依赖是否完整安装（运行 `check_deps.py`）
3. FFmpeg 是否可用（视频渲染必需）
