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

## CI 自动构建（GitHub Actions）

[.github/workflows/release.yml](../.github/workflows/release.yml) 在**推送 `v*` 标签**时自动构建三平台安装包并创建 GitHub Release；也可在 Actions 页面手动触发（可传已存在的 tag 名发布）。

| 产物 | 构建链路 | Runner |
|------|---------|--------|
| `CAPM-Setup-<ver>.exe` | PyInstaller（`CAPM.spec`）+ Inno Setup | `windows-latest` |
| `CAPM-<ver>-macos-<arch>.dmg` | `macos/build_app_pyinstaller.sh`（PyInstaller + hdiutil） | `macos-13`(Intel) / `macos-14`(Apple Silicon) |
| `capm_<ver>_amd64.deb` / `capm-<ver>-*.rpm` | `linux/build_binary_pyinstaller.sh` + `build_deb.sh` / `build_rpm.sh`（`REUSE_BINARY=1` 复用二进制） | `ubuntu-22.04` |

说明：

- CI 统一走 **PyInstaller** 路线（速度快、无交叉编译）；各平台原 Nuitka 脚本（`macos/build_app.sh`、`linux/build_binary.sh`）保留，可在对应系统手动使用
- `linux/build_deb.sh` / `build_rpm.sh` 支持 `REUSE_BINARY=1`：复用已存在的 `dist_linux/capm`，避免 deb/rpm 各自重复构建
- macOS 产物未签名公证，正式分发需自行处理（`macos/sign_and_notarize.sh`）；终端用户首次打开：右键 → 打开，或 `xattr -cr /Applications/CAPM.app`
- exe 内嵌版本资源（`windows/version_info.py`，右键属性可见）；发布新版本时需同步 `app.json`、`version_info.py` 等处的版本号

