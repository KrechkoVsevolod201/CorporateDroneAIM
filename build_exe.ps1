# Build standalone CorporateDroneAIM.exe
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

Write-Host "Installing build dependencies..."
python -m pip install -r requirements.txt pyinstaller --quiet
if (-not $?) { throw "pip install failed" }

Write-Host "Cleaning previous build..."
if (Test-Path -LiteralPath "build") { Remove-Item -LiteralPath "build" -Recurse -Force }
if (Test-Path -LiteralPath "dist\CorporateDroneAIM.exe") {
    Remove-Item -LiteralPath "dist\CorporateDroneAIM.exe" -Force
}

Write-Host "Running PyInstaller..."
python -m PyInstaller --noconfirm --clean CorporateDroneAIM.spec
if (-not $?) { throw "PyInstaller failed" }

$exe = Join-Path $PSScriptRoot "dist\CorporateDroneAIM.exe"
if (-not (Test-Path -LiteralPath $exe)) { throw "EXE not found: $exe" }

$sizeMb = [math]::Round((Get-Item -LiteralPath $exe).Length / 1MB, 1)
Write-Host ""
Write-Host "OK: $exe ($sizeMb MB)"
Write-Host "Copy this file to another PC. On first run it creates config.json, sounds/, assets/ next to the exe."
