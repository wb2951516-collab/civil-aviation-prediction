# CAPM 安装包使用说明

本说明面向发布后的安装包用户与部署人员。

## 系统要求

- Windows 10/11 x64
- macOS（需分别提供 Intel x86_64 与 Apple Silicon arm64 构建产物）
- Linux x86_64（Debian/Ubuntu：DEB；Fedora/RHEL：RPM）

## Windows（EXE 安装程序）

- 图形化安装：双击 `CAPM-Setup-<version>.exe`
- 默认安装路径：`C:\\Program Files\\CAPM`
- 静默安装：
  - `/SILENT`：静默但显示进度
  - `/VERYSILENT`：完全静默

示例：

```bat
CAPM-Setup-1.0.0.exe /VERYSILENT /NORESTART
```

卸载：
- 控制面板 → 程序和功能 → 卸载

升级：
- 直接运行新版本安装程序覆盖安装（保留用户数据目录 `%APPDATA%\\CAPM`）

## macOS（DMG/PKG）

- DMG：拖拽 `CAPM.app` 到 `Applications`
- PKG：双击安装，默认安装到 `/Applications`

安全与签名：
- 若用于对外发布，需要对 `.app` 进行代码签名并公证（notarization），否则可能被 Gatekeeper 拦截。

## Linux（DEB/RPM）

DEB（Debian/Ubuntu）：

```bash
sudo dpkg -i capm_<version>_amd64.deb
```

RPM（Fedora/RHEL）：

```bash
sudo dnf install ./capm-<version>-1.x86_64.rpm
```

卸载：
- DEB：`sudo dpkg -r capm`
- RPM：`sudo dnf remove capm`

## 故障排查（Windows）

如果程序无法启动（双击无反应或闪退）：

1. **检查 VC++ 运行库**
   - 确保安装了 Visual C++ Redistributable 2015-2022 x64。安装程序会自动检测并安装，但若被拦截，可尝试手动安装（位于安装目录 `vc_redist.x64.exe`）。

2. **查看日志**
   - 启动日志（最早期崩溃记录）：`%APPDATA%\CAPM\logs\early_crash.log`
   - 应用运行日志：`%APPDATA%\CAPM\logs\app.log`

3. **命令行诊断**
   - 打开 PowerShell，进入安装目录（如 `C:\Program Files\CAPM`），运行：
     ```powershell
     .\CAPM.exe
     ```
   - 若有输出报错信息，请提供给技术支持。

4. **常见原因**
   - 安全软件拦截：某些杀毒软件可能误杀未签名的 EXE。请添加信任。
   - 缺少依赖：确认安装包完整性（Standalone 模式下应包含 `CAPM.dist` 目录）。

## 用户数据

默认不删除用户数据（便于升级保留配置）。
- Windows 用户数据目录：`%APPDATA%\\CAPM`

