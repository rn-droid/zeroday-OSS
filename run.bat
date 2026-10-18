@echo off
echo ============================================================
echo   Starting LexiGuard (ZeroDay OSS Hacktoberfest 2026)
echo ============================================================
cd backend
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
pause
