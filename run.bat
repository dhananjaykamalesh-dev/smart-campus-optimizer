@echo off
title Smart Campus Optimizer Launcher
echo ========================================================
echo   Launching Smart Campus Optimization System...
echo ========================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your system PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    echo IMPORTANT: Make sure to check the box "Add Python to PATH" during installation.
    echo.
    pause
    exit /b
)

echo [1/2] Checking and installing required packages...
pip install -r requirements.txt --quiet

echo [2/2] Starting Streamlit Web Application...
echo The app will open in your browser shortly at http://localhost:8501
echo Press Ctrl+C in this window anytime to stop the server.
echo.
streamlit run app.py

pause

