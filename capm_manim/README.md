# CAPM 教学动画（Manim）

## 渲染（推荐）

在仓库根目录执行：

```powershell
manim --config_file .\capm_manim\manim.cfg -pqh .\capm_manim\scenes\tutorial.py CAPMTutorial
```

渲染单独场景（示例）：

```powershell
manim --config_file .\capm_manim\manim.cfg -pqh .\capm_manim\scenes\architecture.py ArchitectureScene
```

## 目录结构

 - `capm_manim/scenes/`：动画场景
 - `capm_manim/components/`：可复用组件（流程块/图表/表格/进度条/主题）
 - `capm_manim/assets/`：示例数据
 
 ## 可调参数
 
 - 速度：`capm_manim/components/theme.py` 的 `SPEED`
 - 字体：`capm_manim/components/theme.py` 的 `FONT_FAMILY`
 - 配色：`capm_manim/components/theme.py` 的 `THEME`
