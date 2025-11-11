"""
API Testing Script

Tests all API endpoints.

Run:
    # Start API first:
    bash scripts/start_api.sh
    
    # Then in another terminal:
    python scripts/test_api.py
"""

import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"


def test_root():
    """Test root endpoint."""
    print("\n" + "=" * 80)
    print("TEST 1: Root Endpoint")
    print("=" * 80)
    
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    print("✓ Root endpoint works!")


def test_health():
    """Test health check."""
    print("\n" + "=" * 80)
    print("TEST 2: Health Check")
    print("=" * 80)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'
    print("✓ Health check passed!")


def test_list_models():
    """Test list models endpoint."""
    print("\n" + "=" * 80)
    print("TEST 3: List Models")
    print("=" * 80)
    
    response = requests.get(f"{BASE_URL}/models")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    print("✓ List models works!")


def test_single_prediction():
    """Test single prediction."""
    print("\n" + "=" * 80)
    print("TEST 4: Single Prediction")
    print("=" * 80)
    
    payload = {
        "city": "bangkok",
        "aqi": 2.5,
        "pm2_5": 25.0,
        "pm10": 45.0,
        "no2": 15.0,
        "o3": 85.0,
        "co": 250.0,
        "so2": 5.0,
        "nh3": 2.0,
        "model": "xgboost"
    }
    
    print("\nRequest:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(f"{BASE_URL}/predict", json=payload)
    print(f"\nStatus: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    result = response.json()
    assert 'predicted_aqi' in result
    assert 1.0 <= result['predicted_aqi'] <= 5.0
    print("✓ Prediction successful!")
    print(f"\n📊 Predicted AQI: {result['predicted_aqi']:.2f}")
    print(f"📋 Category: {result['predicted_category']}")
    print(f"💬 Message: {result['health_message']}")


def test_batch_prediction():
    """Test batch prediction."""
    print("\n" + "=" * 80)
    print("TEST 5: Batch Prediction")
    print("=" * 80)
    
    payload = {
        "requests": [
            {
                "city": "bangkok",
                "aqi": 2.5,
                "pm2_5": 25.0,
                "pm10": 45.0,
                "no2": 15.0,
                "o3": 85.0,
                "model": "xgboost"
            },
            {
                "city": "london",
                "aqi": 1.8,
                "pm2_5": 18.0,
                "pm10": 30.0,
                "no2": 12.0,
                "o3": 70.0,
                "model": "lightgbm"
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/predict/batch", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nTotal predictions: {result['total_predictions']}")
        
        for pred in result['predictions']:
            print(f"\n  {pred['city']}:")
            print(f"    Current: {pred['current_aqi']:.2f}")
            print(f"    Predicted: {pred['predicted_aqi']:.2f}")
            print(f"    Category: {pred['predicted_category']}")
        
        print("✓ Batch prediction successful!")
    else:
        print(f"Response: {response.text}")


def test_model_info():
    """Test model info endpoint."""
    print("\n" + "=" * 80)
    print("TEST 6: Model Info")
    print("=" * 80)
    
    response = requests.get(f"{BASE_URL}/models/xgboost")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    print("✓ Model info retrieved!")


def test_invalid_input():
    """Test error handling."""
    print("\n" + "=" * 80)
    print("TEST 7: Invalid Input (Error Handling)")
    print("=" * 80)
    
    payload = {
        "city": "bangkok",
        "aqi": 10.0,  # Invalid (> 5)
        "pm2_5": 25.0,
        "pm10": 45.0,
        "no2": 15.0,
        "o3": 85.0
    }
    
    response = requests.post(f"{BASE_URL}/predict", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 422  # Validation error
    print("✓ Validation working correctly!")


def main():
    """Run all tests."""
    print("=" * 80)
    print("AIR QUALITY PREDICTOR API - TEST SUITE")
    print("=" * 80)
    print(f"\nTesting API at: {BASE_URL}")
    print(f"Time: {datetime.now()}")
    
    try:
        # Check if API is running
        requests.get(f"{BASE_URL}/health", timeout=2)
    except requests.exceptions.ConnectionError:
        print("\n❌ API is not running!")
        print("\nPlease start the API first:")
        print("  bash src/api/start_api.sh")
        return
    
    try:
        test_root()
        test_health()
        test_list_models()
        test_single_prediction()
        test_batch_prediction()
        test_model_info()
        test_invalid_input()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        print("\nAPI is working correctly! 🎉")
        print("\nNext steps:")
        print("  1. Try the interactive docs: http://localhost:8000/docs")
        print("  2. Test with your own data")
        print("  3. Build the Streamlit dashboard")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()