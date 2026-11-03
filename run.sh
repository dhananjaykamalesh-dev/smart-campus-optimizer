#!/usr/bin/env bash
echo "========================================================"
echo "  Launching Smart Campus Optimization System..."
echo "========================================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed!"
    echo "Please install Python 3.10+ from https://www.python.org/"
    exit 1
fi

echo "[1/2] Installing requirements..."
pip3 install -r requirements.txt --quiet

echo "[2/2] Starting Streamlit..."
echo "Opening in browser at http://localhost:8501"
streamlit run app.py
