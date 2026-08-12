$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ProjectRoot
$ProjectRoot = Split-Path -Parent $ProjectRoot
Set-Location $ProjectRoot

$MetaPath = Join-Path $ProjectRoot "packaging\app.json"
$Meta = Get-Content -Raw -Encoding UTF8 -Path $MetaPath | ConvertFrom-Json
$Version = [string]$Meta.version

if (-not (Test-Path (Join-Path $ProjectRoot "dist"))) { New-Item -ItemType Directory -Path (Join-Path $ProjectRoot "dist") | Out-Null }
if (-not (Test-Path (Join-Path $ProjectRoot "dist_installers\windows"))) {
    New-Item -ItemType Directory -Path (Join-Path $ProjectRoot "dist_installers\windows") -Force | Out-Null
}

# Step 2: Build Executable (PyInstaller)
# -----------------------------------------------------------
Write-Host "Building executable with PyInstaller..." -ForegroundColor Cyan

$ExePath = Join-Path $ProjectRoot "dist\CAPM\CAPM.exe"
if (-not (Test-Path $ExePath)) {
    pyinstaller --name=CAPM --windowed --icon="assets\plane.ico" --noconfirm --clean --add-data="assets;assets" --collect-all capm --collect-all pandas --collect-all scipy --collect-all statsmodels --collect-all numpy CAPM.py
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed: $LASTEXITCODE" }
}
if (-not (Test-Path $ExePath)) { throw "Missing packaged exe: $ExePath" }

$VCRedist = Join-Path $ProjectRoot "packaging\windows\deps\vc_redist.x64.exe"
if (-not (Test-Path $VCRedist)) {
    & (Join-Path $ProjectRoot "packaging\windows\get_vcredist.ps1")
    if ($LASTEXITCODE -ne 0) { throw "VC++ redistributable download failed: $LASTEXITCODE" }
}
if (-not (Test-Path $VCRedist)) { throw "Missing VC++ redistributable: $VCRedist" }

$IssPath = Join-Path $ProjectRoot "packaging\windows\capm.iss"
$IsccPath = $null
$IsccCmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if ($env:ISCC_PATH -and (Test-Path $env:ISCC_PATH)) {
    $IsccPath = [string]$env:ISCC_PATH
} elseif ($IsccCmd -and $IsccCmd.Source -and (Test-Path $IsccCmd.Source)) {
    $IsccPath = [string]$IsccCmd.Source
} else {
    $Preferred = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
        (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
        (Join-Path "${env:ProgramFiles(x86)}" "Inno Setup 6\ISCC.exe")
    ) | Where-Object { $_ -and (Test-Path $_) }
    $Preferred = @($Preferred)
    if ($Preferred.Count -gt 0) {
        $IsccPath = [string]$Preferred[0]
    } else {
        $Roots = @(
            (Join-Path $env:LOCALAPPDATA "Programs"),
            $env:ProgramFiles,
            "${env:ProgramFiles(x86)}"
        ) | Where-Object { $_ -and (Test-Path $_) }
        $Roots = @($Roots)
        $Found = Get-ChildItem -Path $Roots -Filter ISCC.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($Found -and $Found.FullName) { $IsccPath = [string]$Found.FullName }
    }
}

if (-not $IsccPath -or -not (Test-Path $IsccPath)) { throw "ISCC.exe not found. Please install Inno Setup (x64) and retry." }

Write-Host "Using ISCC: $IsccPath"

& "$IsccPath" "/DAppVersion=$Version" "$IssPath"
if ($LASTEXITCODE -ne 0) { throw "Inno Setup compile failed: $LASTEXITCODE" }

Get-ChildItem (Join-Path $ProjectRoot "dist_installers\windows") -Filter "*.exe" | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | Format-Table Name,Length,LastWriteTime

