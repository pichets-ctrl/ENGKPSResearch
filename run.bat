@echo off
chcp 65001 >nul
echo ====================================================
echo   ระบบรายงานวิจัยประจำเดือน — Streamlit Dashboard
echo ====================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] ไม่พบ Python  กรุณาติดตั้ง Python 3.10+ และเพิ่มใน PATH
    pause
    exit /b 1
)

echo [1/2] กำลังติดตั้ง dependencies...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] ติดตั้ง dependencies ไม่สำเร็จ
    pause
    exit /b 1
)

echo [2/2] กำลังเปิด Dashboard...
echo       เปิดเบราว์เซอร์ไปที่ http://localhost:8501
echo       (กด Ctrl+C เพื่อหยุด)
echo.
streamlit run app.py ^
    --server.port=8501 ^
    --server.address=0.0.0.0 ^
    --browser.gatherUsageStats=false

pause
