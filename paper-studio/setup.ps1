param([switch]$WithFormatter)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
        & py -3.11 -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 is required. Install it from python.org, or create .venv manually using your supported Python.' }
    }
    & '.\.venv\Scripts\python.exe' -m pip install -r requirements-desktop.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    if ($WithFormatter) { & (Join-Path $PSScriptRoot 'setup-formatter.ps1') }
    Write-Output 'Ready. Run .\start.ps1. Private data defaults to LOCALAPPDATA\PaperStudio, outside this checkout.'
} finally { Pop-Location }
