@echo off
chcp 65001 >nul
set QUIZNOVA_CLOUD=
set PORT=8765
python server.py
pause
