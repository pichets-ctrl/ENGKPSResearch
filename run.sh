#!/usr/bin/env bash
set -e

echo "===================================================="
echo "  ระบบรายงานวิจัยประจำเดือน — Streamlit Dashboard"
echo "===================================================="
echo

PYTHON=python3
command -v python3 &>/dev/null || PYTHON=python

if ! command -v "$PYTHON" &>/dev/null; then
    echo "[ERROR] ไม่พบ Python  กรุณาติดตั้ง Python 3.10+ ก่อน"
    exit 1
fi

echo "[1/2] กำลังติดตั้ง dependencies..."
"$PYTHON" -m pip install -r requirements.txt --quiet

echo "[2/2] กำลังเปิด Dashboard..."
echo "      เปิดเบราว์เซอร์ไปที่ http://localhost:8501"
echo "      (กด Ctrl+C เพื่อหยุด)"
echo

"$PYTHON" -m streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --browser.gatherUsageStats=false
