# Build Windows desktop bundle (PyInstaller onedir) for AI Powered Construction Violation Detection.
# Prerequisites: Node.js, Python venv with backend deps + pip install pyinstaller
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host ">>> npm ci / install frontend..."
Set-Location (Join-Path $root "frontend")
if (Test-Path "package-lock.json") { npm ci } else { npm install }
npm run build

Write-Host ">>> PyInstaller..."
Set-Location (Join-Path $root "backend")
if (-not (Test-Path "venv\Scripts\python.exe")) {
  Write-Error "Create backend venv first: cd backend; py -3.13 -m venv venv; .\venv\Scripts\pip install -r requirements.txt"
}
& .\venv\Scripts\pip.exe install pyinstaller
& .\venv\Scripts\pyinstaller.exe --clean --noconfirm windows_bundle.spec

Write-Host ">>> Output: backend\dist\ConstructionViolationDetection\ConstructionViolationDetection.exe"
Write-Host "    Copy .env next to the exe (see README). Open http://127.0.0.1:8000"
