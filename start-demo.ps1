$ErrorActionPreference = "Stop"
$workspacePath = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path "$workspacePath\backend\.venv\Scripts\python.exe")) {
    py -m venv "$workspacePath\backend\.venv"
    & "$workspacePath\backend\.venv\Scripts\python.exe" -m pip install -r "$workspacePath\backend\requirements.txt"
}

if (-not (Test-Path "$workspacePath\frontend\node_modules")) {
    Push-Location "$workspacePath\frontend"
    npm install
    Pop-Location
}

Start-Process -FilePath "$workspacePath\backend\.venv\Scripts\python.exe" -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000" -WorkingDirectory "$workspacePath\backend" -WindowStyle Hidden
Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev", "--", "--host", "127.0.0.1" -WorkingDirectory "$workspacePath\frontend" -WindowStyle Hidden

Write-Host "ClassMind is starting: http://localhost:5173" -ForegroundColor Green
Write-Host "API docs: http://localhost:8000/docs"

