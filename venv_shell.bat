@echo off
REM Double-click this file to open a new Command Prompt in this repo with .venv activated.
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo [.venv] not found. From this folder run:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -e ".[dev]"
    pause
    exit /b 1
)

set "BOOT=%TEMP%\synmax_takehome_venv_boot.bat"
(
    echo @echo off
    echo cd /d "%~dp0"
    echo call "%~dp0.venv\Scripts\activate.bat"
    echo echo Venv active.
    echo python --version
) > "%BOOT%"

start "venv: python_dev_candidate" cmd /k call "%BOOT%"
