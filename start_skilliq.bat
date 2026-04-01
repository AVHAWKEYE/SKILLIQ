@echo off
REM SkillIQ Startup Script for Windows - Enhanced Version

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                  SkillIQ - Starting Server                ║
echo ║          AI-Powered Student Performance Platform          ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

cd /d P:\SkillIQ

REM Create virtual environment if it doesn't exist
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
)

REM Install/update dependencies
echo Installing dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt -q

REM Start the server
echo.
echo ─────────────────────────────────────────────────────────────
echo Starting SkillIQ Server...
echo ─────────────────────────────────────────────────────────────
echo.
echo ✓ Frontend:    http://127.0.0.1:8000
echo ✓ Auth Page:   http://127.0.0.1:8000/auth.html
echo ✓ API Docs:    http://127.0.0.1:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo ─────────────────────────────────────────────────────────────
echo.

".venv\Scripts\python.exe" server.py

pause
