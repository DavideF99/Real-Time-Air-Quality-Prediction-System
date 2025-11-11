#!/bin/bash

# Start Air Quality Predictor Dashboard
# 
# Usage:
#   bash scripts/start_dashboard.sh

echo "================================================================================"
echo "STARTING AIR QUALITY PREDICTOR DASHBOARD"
echo "================================================================================"

# Navigate to project root
cd "$(dirname "$0")/.."

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    echo "Please create venv first: python -m venv venv"
    exit 1
fi

# Check if API is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  API is not running!"
    echo ""
    echo "Please start the API in another terminal:"
    echo "  uvicorn src.api.main:app --reload"
    echo ""
    read -p "Press Enter once API is running, or Ctrl+C to exit..."
fi

echo "✓ API is running"
echo ""

# Start dashboard
echo "Starting Streamlit dashboard..."
echo ""
echo "Dashboard will open at: http://localhost:8501"
echo ""
echo "Press CTRL+C to stop"
echo "================================================================================"
echo ""

streamlit run src/dashboard/app.py