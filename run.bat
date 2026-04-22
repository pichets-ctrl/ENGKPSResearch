@echo off
chcp 65001 >nul 2>&1

echo ============================================================
echo   Research Dashboard - Streamlit
echo ============================================================
echo.

REM --- Find Python ---
set PYTHON_CMD=

py --version >nul 2>&1
if %errorlevel% equ 0 set PYTHON_CMD=py

if "%PYTHON_CMD%"=="" (
    python --version >nul 2>&1
    if %errorlevel% equ 0 set PYTHON_CMD=python
)

if "%PYTHON_CMD%"=="" (
    python3 --version >nul 2>&1
    if %errorlevel% equ 0 set PYTHON_CMD=python3
)

if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python not found.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo IMPORTANT: Check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Using: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

REM --- Install dependencies ---
echo [1/2] Installing dependencies...
%PYTHON_CMD% -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.
echo.

REM --- Launch dashboard ---
echo [2/2] Starting dashboard...
echo       Open browser at: http://localhost:8501
echo       Press Ctrl+C to stop.
echo.

%PYTHON_CMD% -m streamlit run app.py ^
    --server.port=8501 ^
    --server.address=0.0.0.0 ^
    --browser.gatherUsageStats=false

pause
