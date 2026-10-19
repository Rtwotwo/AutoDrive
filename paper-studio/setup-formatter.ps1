$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw 'Node.js/npm is required for the optional formatter.' }
& npm install --prefix (Join-Path $PSScriptRoot '.runtime') --no-audit --no-fund bun
if ($LASTEXITCODE -ne 0) { throw 'Bun installation failed.' }
Write-Output 'Project-local Bun installed. The formatter may download its npm dependencies on first use.'
