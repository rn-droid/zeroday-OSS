Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Starting LexiGuard (ZeroDay OSS Hacktoberfest 2026)" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

Set-Location -Path "$PSScriptRoot/backend"
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
