$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create Python environment.' }
}
& '.\.venv\Scripts\python.exe' -m pip install -r backend/requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }

if (-not (Test-Path -LiteralPath 'frontend\node_modules')) {
    Push-Location frontend
    npm install
    Pop-Location
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
}
Push-Location frontend
npm run build
Pop-Location
if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }

Write-Host 'Open http://127.0.0.1:8000. Initial model download/loading may take several minutes.'
& '.\.venv\Scripts\python.exe' -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
