@echo off
setlocal
title Tipping Point
cd /d "%~dp0"

set "PY="
py -3 --version >nul 2>nul && set "PY=py -3"
if not defined PY python --version >nul 2>nul && set "PY=python"
if not defined PY (
  echo Python 3.10 or newer is needed.
  echo Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH",
  echo then double-click start.bat again.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo First run: setting things up. This takes a minute or two...
  %PY% -m venv .venv || goto fail
)
".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt || goto fail
".venv\Scripts\python.exe" start.py
pause
exit /b 0

:fail
echo.
echo Setup failed. See the message above.
pause
exit /b 1
