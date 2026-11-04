@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PORT=8765
set QUIZNOVA_CLOUD=
where python >nul 2>nul
if errorlevel 1 (
  echo Python 3.10 or later is required. Install Python and retry.
  pause
  exit /b 1
)
python server.py
pause
