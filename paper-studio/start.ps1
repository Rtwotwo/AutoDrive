$ErrorActionPreference = 'Stop'
$configPath = Join-Path $PSScriptRoot 'desktop-install.json'
if (-not $env:PAPER_STUDIO_HOME -and (Test-Path -LiteralPath $configPath)) {
    $privateConfig = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
    $desktopExe = Join-Path $privateConfig.installation_dir 'app\PaperStudio.exe'
    if (Test-Path -LiteralPath $desktopExe) {
        Start-Process -FilePath $desktopExe -WorkingDirectory $privateConfig.installation_dir -WindowStyle Hidden
        exit 0
    }
}
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Run setup.ps1 first; see README.md.' }
$pythonw = Join-Path $PSScriptRoot '.venv\Scripts\pythonw.exe'
Start-Process -FilePath $pythonw -ArgumentList ('"'+(Join-Path $PSScriptRoot 'desktop.py')+'"') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
