# Install Inno Setup and build installer
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

Write-Host "Step 1: Building exe..."
& .\build_exe.ps1
if (-not $?) { throw "Build exe failed" }

Write-Host ""
Write-Host "Step 2: Checking for Inno Setup..."
$innoSetup = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if (-not (Test-Path -LiteralPath $innoSetup)) {
    Write-Host "Inno Setup not found. Downloading..."
    
    $installerUrl = "https://jrsoftware.org/download.php/is.exe"
    $installerPath = "$env:TEMP\innosetup.exe"
    
    try {
        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
        Write-Host "Installing Inno Setup (requires admin)..."
        Start-Process -FilePath $installerPath -ArgumentList "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART" -Wait
        Remove-Item $installerPath -Force
        
        if (-not (Test-Path -LiteralPath $innoSetup)) {
            throw "Inno Setup installation failed"
        }
        Write-Host "Inno Setup installed successfully!"
    }
    catch {
        Write-Host "Failed to install Inno Setup automatically."
        Write-Host "Please download and install manually from: https://jrsoftware.org/isdl.php"
        Write-Host "After installation, run this script again."
        exit 1
    }
}

Write-Host ""
Write-Host "Step 3: Creating installer..."
& $innoSetup installer.iss
if (-not $?) { throw "Inno Setup failed" }

$installer = Join-Path $PSScriptRoot "installer_output\CorporateDroneAIM_Setup.exe"
if (-not (Test-Path -LiteralPath $installer)) { throw "Installer not found: $installer" }

$sizeMb = [math]::Round((Get-Item -LiteralPath $installer).Length / 1MB, 1)
Write-Host ""
Write-Host "OK: $installer ($sizeMb MB)"
Write-Host "Installer ready for distribution!"
