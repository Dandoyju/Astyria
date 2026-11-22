@echo off
cd /d "%~dp0"
set PORT=8000
if not "%1"=="" set PORT=%1
python server.py %PORT%
pause
