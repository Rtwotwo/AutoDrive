param([string]$OutputDirectory = (Join-Path $PSScriptRoot 'dist'), [string]$PythonPath = (Join-Path $PSScriptRoot '.venv\Scripts\python.exe'))
$ErrorActionPreference = 'Stop'
$python = $PythonPath
if (-not (Test-Path -LiteralPath $python)) { throw 'Run setup.ps1 first.' }
Push-Location $PSScriptRoot
try {
    & $python -m pip install -r requirements-dev.txt
    if ($LASTEXITCODE -ne 0) { throw 'Build dependency installation failed.' }
    & $python -m PyInstaller --noconfirm --windowed --onedir --name PaperStudio --icon 'static\paper-studio.ico' --distpath $OutputDirectory --workpath '.build' --add-data 'static;static' --add-data 'skills;skills' --add-data 'LICENSE;.' --add-data 'THIRD_PARTY_NOTICES.md;.' --collect-data pypdfium2_raw --hidden-import 'tests.pdf_fixtures' --hidden-import 'tests.test_sources' --hidden-import 'tests.test_writing' --exclude-module tkinter --exclude-module PyQt5 --exclude-module PyQt6 --exclude-module PySide2 --exclude-module PySide6 desktop.py
    if ($LASTEXITCODE -ne 0) { throw 'Desktop build failed.' }
    & $python collect_licenses.py (Join-Path $OutputDirectory 'PaperStudio\third-party-licenses')
    if ($LASTEXITCODE -ne 0) { throw 'Dependency license collection failed; do not distribute this build.' }
    Write-Output 'Build complete. Private data defaults to LOCALAPPDATA/PaperStudio; optionally set PAPER_STUDIO_HOME outside the checkout.'
} finally { Pop-Location }
