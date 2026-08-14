#define AppName "CAPM"
#define AppDisplayName "民航旅客运输量预测系统"
#ifndef AppVersion
  #define AppVersion "1.3.0"
#endif
#define AppPublisher "CAPM Project"
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
SetupIconFile=..\..\assets\plane.ico
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
