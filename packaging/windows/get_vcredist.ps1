$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ProjectRoot
$ProjectRoot = Split-Path -Parent $ProjectRoot

$OutDir = Join-Path $ProjectRoot "packaging\windows\deps"
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }

$OutFile = Join-Path $OutDir "vc_redist.x64.exe"
$Url = "https://aka.ms/vs/17/release/vc_redist.x64.exe"

Write-Host "Downloading: $Url"
Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing

$Size = (Get-Item $OutFile).Length
if ($Size -lt 1000000) { throw "Downloaded file seems too small: $OutFile ($Size bytes)" }

Write-Host "Saved: $OutFile ($Size bytes)" -ForegroundColor Green

