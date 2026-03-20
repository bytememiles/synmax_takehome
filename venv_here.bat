@echo off
REM Activate the venv in the *current* Command Prompt. Usage:  call venv_here.bat
REM (Do not use setlocal here — it would undo PATH when this file returns.)
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo [.venv] not found. Run: python -m venv .venv
    exit /b 1
)

call "%~dp0.venv\Scripts\activate.bat"
echo Venv active for this window.
