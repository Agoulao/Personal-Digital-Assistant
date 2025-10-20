@echo off
REM Change directory to the folder where this BAT is located
cd /d "%~dp0"

echo =======================================
echo   Personal Digital Assistant Launcher
echo =======================================

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10 before running this assistant.
    pause
    exit /b
)

REM Install required dependencies from src/requirements.txt
echo Installing/updating dependencies...
python -m pip install --upgrade pip
python -m pip install -r src\requirements.txt

REM Launch the assistant from src/main.py
echo Starting the assistant...
python src\main.py

pause
