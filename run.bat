@echo off
chcp 65001 >nul
echo ====================================================
echo   ระบบรายงานวิจัยประจำเดือน -- Streamlit Dashboard
echo ====================================================
echo.

REM --- หา Python command ที่ใช้งานได้ ---
set PYTHON_CMD=

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    goto :found_python
)

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto :found_python
)

python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
    goto :found_python
)

echo [ERROR] ไม่พบ Python กรุณาติดตั้ง Python 3.10+
echo         ดาวน์โหลดได้ที่ https://www.python.org/downloads/
echo         ** สำคัญ: ติ๊ก "Add Python to PATH" ตอนติดตั้ง **
pause
exit /b 1

:found_python
echo [OK] ใช้คำสั่ง: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

REM --- ติดตั้ง dependencies ---
echo [1/2] กำลังติดตั้ง dependencies...
%PYTHON_CMD% -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] ติดตั้ง dependencies ไม่สำเร็จ
    pause
    exit /b 1
)
echo [OK] ติดตั้งสำเร็จ
echo.

REM --- เปิด Dashboard ---
echo [2/2] กำลังเปิด Dashboard...
echo       เปิดเบราว์เซอร์ไปที่ http://localhost:8501
echo       (กด Ctrl+C เพื่อหยุด)
echo.

%PYTHON_CMD% -m streamlit run app.py ^
    --server.port=8501 ^
    --server.address=0.0.0.0 ^
    --browser.gatherUsageStats=false

pause
