# 动画制作说明（CAPM → Manim）

## 场景与代码对应关系

- **IntroScene**：教学片头与主题引入  
  - 文件：`capm_manim/scenes/intro.py`
- **ArchitectureScene**：程序主链路（run_forecast 流水线）  
  - 文件：`capm_manim/scenes/architecture.py`  
  - 对应代码：主流程 [run_forecast](file:///d:/AI-coding/Prpject/Civil%20aviation%20passenger%20traffic%20volume%20prediction%20model/CAPM.py#L1557-L1616)
- **DataIngestScene**：Excel/录入 → 历史序列  
  - 文件：`capm_manim/scenes/data_ingest.py`  
  - 对应代码：[import_data](file:///d:/AI-coding/Prpject/Civil%20aviation%20passenger%20traffic%20volume%20prediction%20model/CAPM.py#L1041-L1089)、[manual_input](file:///d:/AI-coding/Prpject/Civil%20aviation%20passenger%20traffic%20volume%20prediction%20model/CAPM.py#L1090-L1146)、[prepare_time_series](file:///d:/AI-coding/Prpject/Civil%20aviation%20passenger%20traffic%20volume%20prediction%20model/CAPM.py#L1529-L1555)
- **ModelingScene**：三模型并行 → 加权融合  
  - 文件：`capm_manim/scenes/modeling.py`  
  - 对应算法：[capm/models.py](file:///d:/AI-coding/Prpject/Civil%20aviation%20passenger%20traffic%20volume%20prediction%20model/capm/models.py)
- **HolidayEffectScene**：节假日/春运效应修正  
  - 文件：`capm_manim/scenes/holiday_effect.py`  
  - 对应算法：[apply_holiday_effects](file:///d:/AI-coding/Prpject/Civil%20aviation%20passenger%20traffic%20volume%20prediction%20model/capm/holiday.py#L128-L167)
- **GrowthAdjustmentScene**：年度增长率校准  
  - 文件：`capm_manim/scenes/growth_adjustment.py`  
  - 对应算法：[apply_annual_growth_adjustment](file:///d:/AI-coding/Prpject/Civil%20aviation%20passenger%20traffic%20volume%20prediction%20model/capm/growth.py#L4-L39)
- **OutputAndExportScene**：结果表格与导出结构  
  - 文件：`capm_manim/scenes/output_export.py`  
  - 对应代码：[generate_forecast_table](file:///d:/AI-coding/Prpject/Civil%20aviation%20passenger%20traffic%20volume%20prediction%20model/CAPM.py#L1721-L1759)、[export_forecast_data](file:///d:/AI-coding/Prpject/Civil%20aviation%20passenger%20traffic%20volume%20prediction%20model/CAPM.py#L1856-L1903)
- **SummaryScene**：回顾与收束  
  - 文件：`capm_manim/scenes/summary.py`

额外场景：
- **AutoWeightBacktestScene（可选）**：滚动回测 → 推荐权重（示意）  
  - 文件：`capm_manim/scenes/backtest.py`

## 一键渲染入口

- **整片（推荐）**：`capm_manim/scenes/tutorial.py` 中的 `CAPMTutorial`

```powershell
manim --config_file .\\capm_manim\\manim.cfg -pqh .\\capm_manim\\scenes\\tutorial.py CAPMTutorial
```

- **单场景（示例）**

```powershell
manim --config_file .\\capm_manim\\manim.cfg -pqh .\\capm_manim\\scenes\\architecture.py ArchitectureScene
```

## 输出文件位置

Manim 默认输出到仓库根目录下的 `media/`：
- `media/videos/<脚本名>/<分辨率>/<Scene>.mp4`

示例：
- `media/videos/tutorial/480p15/CAPMTutorial.mp4`

## 速度/字体/配色调整

- 速度：`capm_manim/components/theme.py` 的 `SPEED`（越大越快）
- 字体：`capm_manim/components/theme.py` 的 `FONT_FAMILY`
- 配色：`capm_manim/components/theme.py` 的 `THEME`

## 依赖说明

- 本工程避免使用 `MathTex/LaTeX`，以降低对 LaTeX 环境的要求。
