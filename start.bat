@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
node --version
if errorlevel 1 (
  echo Please install Node.js 24 from https://nodejs.org/
  pause
  exit /b 1
)
.venv\Scripts\python.exe run.py --open-browser
pause
