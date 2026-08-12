# CAPM 跨平台安装包工程

本目录提供 Windows / macOS / Linux 的“可重复构建”安装包工程与脚本。跨平台安装包无法在单一操作系统上完成所有平台的二进制构建：需要在目标 OS（或对应架构的 CI Runner）上分别构建产物，再打包成对应安装格式。

## 目录结构

- `packaging/app.json`：统一产品元信息（名称/版本/默认安装目录等）
- `packaging/windows/`：Windows 安装程序（Inno Setup EXE）
- `packaging/macos/`：macOS DMG/PKG 构建脚本（需在 macOS 上执行）
- `packaging/linux/`：Linux DEB/RPM 构建脚本与模板（需在 Linux 上执行）

## 构建原则

- 64 位优先：Windows x86_64、Linux x86_64、macOS Intel/Apple Silicon 分别构建
- “独立运行”：安装后不依赖开发环境路径；运行时用户数据目录在用户配置目录（Windows：`%APPDATA%\\CAPM`）
- 静默安装：Windows 安装程序支持 ` /SILENT` / ` /VERYSILENT`

