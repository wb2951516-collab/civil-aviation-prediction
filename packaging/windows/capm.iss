#define AppName "CAPM"
#define AppDisplayName "民航旅客运输量预测系统"
#ifndef AppVersion
  #define AppVersion "1.4.0"
#endif
#define AppPublisher "SuperM"
#define AppExeName "CAPM.exe"
#define AppId "{{B03C64AE-9D5A-4C90-88B5-9A9A1BA5E0D2}}"

[Setup]
AppId={#AppId}
AppName={#AppDisplayName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppDisplayName}
DisableProgramGroupPage=yes
OutputDir=..\..\dist_installers\windows
OutputBaseFilename={#AppName}-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
WizardStyle=modern
SetupIconFile=..\..\assets\airCAPM.ico
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "chinesesimplified"; MessagesFile: "deps\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "purgeuserdata"; Description: "卸载时删除用户数据（%APPDATA%\CAPM）"; Flags: unchecked

[Files]
Source: "..\..\dist\CAPM\CAPM.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\dist\CAPM\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
#if FileExists("..\..\packaging\windows\deps\vc_redist.x64.exe")
Source: "..\..\packaging\windows\deps\vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
#endif

[Icons]
Name: "{group}\{#AppDisplayName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#AppDisplayName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
#if FileExists("..\..\packaging\windows\deps\vc_redist.x64.exe")
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /quiet /norestart"; Flags: waituntilterminated runhidden
#endif

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\CAPM"; Tasks: purgeuserdata

[Code]
const
  SHCNE_ASSOCCHANGED = $04000000;
  SHCNF_IDLIST = $0000;

procedure SHChangeNotify(wEventId, uFlags: Cardinal; dwItem1, dwItem2: Cardinal);
  external 'SHChangeNotify@shell32.dll stdcall';

// 升级安装后路径不变，Windows 图标缓存会继续显示旧版图标；
// 安装/卸载完成后通知 Shell 刷新，桌面/开始菜单/任务栏立即换新图标
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, 0, 0);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, 0, 0);
end;
