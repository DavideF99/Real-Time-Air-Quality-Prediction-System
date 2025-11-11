#!/bin/bash

# Start Air Quality Predictor API
# 
# Usage:
#   bash scripts/start_api.sh

echo "================================================================================"
echo "STARTING AIR QUALITY PREDICTOR API"
echo "================================================================================"

# Navigate to project root
cd "$(dirname "$0")/.."

# Activate virtual environment
source venv/bin/activate

# Check if models exist
if [ ! -d "data/models" ] || [ -z "$(ls -A data/models/*.joblib 2>/dev/null)" ]; then
    echo "❌ No trained models found in data/models/"
    echo "Please train models first:"
    echo "  python scripts/train_models.py --model xgboost"
    exit 1
fi

echo "✓ Found trained models"
echo ""

# Start API
echo "Starting FastAPI server..."
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo "Alternative docs:  http://localhost:8000/redoc"
echo "Health check:      http://localhost:8000/health"
echo ""
echo "Press CTRL+C to stop"
echo "================================================================================"
echo ""

uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000