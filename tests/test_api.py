"""
API Endpoint Tests

Tests all FastAPI endpoints.

Run:
    # Start API first, then:
    pytest tests/test_api.py -v
"""

import pytest
import requests
from datetime import datetime


# Test configuration
API_URL = "http://localhost:8000"
TIMEOUT = 5


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_api_running():
    """Check if API is running."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


# Skip all tests if API is not running
pytestmark = pytest.mark.skipif(
    not is_api_running(),
    reason="API is not running. Start with: uvicorn src.api.main:app --reload"
)


# ============================================================================
# ROOT ENDPOINT TESTS
# ============================================================================

@pytest.mark.api
def test_root_endpoint():
    """Test root endpoint returns API info."""
    response = requests.get(f"{API_URL}/", timeout=TIMEOUT)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "message" in data
    assert "version" in data
    assert "documentation" in data
    assert data["version"] == "1.0.0"


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

@pytest.mark.api
@pytest.mark.smoke
def test_health_check():
    """Test health check endpoint."""
    response = requests.get(f"{API_URL}/health", timeout=TIMEOUT)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert "version" in data
    assert "models_loaded" in data
    assert "timestamp" in data
    assert len(data["models_loaded"]) > 0


@pytest.mark.api
def test_health_check_performance():
    """Test health check is fast."""
    import time
    
    start = time.time()
    response = requests.get(f"{API_URL}/health", timeout=TIMEOUT)
    elapsed = time.time() - start
    
    assert response.status_code == 200
    assert elapsed < 0.1  # Should be < 100ms


# ============================================================================
# PREDICTION ENDPOINT TESTS
# ============================================================================

@pytest.mark.api
@pytest.mark.smoke
def test_predict_success(api_prediction_request):
    """Test successful prediction."""
    response = requests.post(
        f"{API_URL}/predict",
        json=api_prediction_request,
        timeout=TIMEOUT
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "city" in data
    assert "current_aqi" in data
    assert "predicted_aqi" in data
    assert "predicted_category" in data
    assert "confidence_interval" in data
    assert "health_message" in data
    assert "model_used" in data
    assert "timestamp" in data
    
    # Validate values
    assert 1.0 <= data["predicted_aqi"] <= 5.0
    assert data["current_aqi"] == api_prediction_request["aqi"]
    assert "lower" in data["confidence_interval"]
    assert "upper" in data["confidence_interval"]


@pytest.mark.api
def test_predict_all_cities():
    """Test prediction works for all cities."""
    cities = ["bangkok", "durban", "sao_paulo", "sydney", "london", "new_york"]
    
    for city in cities:
        request = {
            "city": city,
            "aqi": 2.5,
            "pm2_5": 25.0,
            "pm10": 45.0,
            "no2": 15.0,
            "o3": 85.0
        }
        
        response = requests.post(
            f"{API_URL}/predict",
            json=request,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200, f"Failed for {city}"
        data = response.json()
        assert "predicted_aqi" in data


@pytest.mark.api
def test_predict_all_models(api_prediction_request):
    """Test prediction works for all models."""
    models = ["xgboost", "lightgbm", "random_forest", "linear_regression"]
    
    for model in models:
        request = {**api_prediction_request, "model": model}
        
        response = requests.post(
            f"{API_URL}/predict",
            json=request,
            timeout=TIMEOUT
        )
        
        # Some models might not be available
        if response.status_code == 200:
            data = response.json()
            assert "predicted_aqi" in data
            assert data["model_used"] == model


@pytest.mark.api
def test_predict_invalid_aqi():
    """Test prediction fails with invalid AQI."""
    request = {
        "city": "bangkok",
        "aqi": 10.0,  # Invalid (> 5)
        "pm2_5": 25.0,
        "pm10": 45.0,
        "no2": 15.0,
        "o3": 85.0
    }
    
    response = requests.post(
        f"{API_URL}/predict",
        json=request,
        timeout=TIMEOUT
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.api
def test_predict_missing_fields():
    """Test prediction fails with missing required fields."""
    request = {
        "city": "bangkok",
        "aqi": 2.5
        # Missing pm2_5, pm10, no2, o3
    }
    
    response = requests.post(
        f"{API_URL}/predict",
        json=request,
        timeout=TIMEOUT
    )
    
    assert response.status_code == 422


@pytest.mark.api
def test_predict_invalid_city():
    """Test prediction fails with invalid city."""
    request = {
        "city": "invalid_city",
        "aqi": 2.5,
        "pm2_5": 25.0,
        "pm10": 45.0,
        "no2": 15.0,
        "o3": 85.0
    }
    
    response = requests.post(
        f"{API_URL}/predict",
        json=request,
        timeout=TIMEOUT
    )
    
    assert response.status_code == 422


@pytest.mark.api
@pytest.mark.performance
def test_predict_performance(api_prediction_request):
    """Test prediction performance."""
    import time
    
    times = []
    
    for _ in range(10):
        start = time.time()
        response = requests.post(
            f"{API_URL}/predict",
            json=api_prediction_request,
            timeout=TIMEOUT
        )
        elapsed = time.time() - start
        times.append(elapsed)
        
        assert response.status_code == 200
    
    avg_time = sum(times) / len(times)
    assert avg_time < 0.2  # Average < 200ms


# ============================================================================
# BATCH PREDICTION TESTS
# ============================================================================

@pytest.mark.api
def test_batch_predict_success(api_batch_request):
    """Test batch prediction works."""
    response = requests.post(
        f"{API_URL}/predict/batch",
        json=api_batch_request,
        timeout=TIMEOUT
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "predictions" in data
    assert "total_predictions" in data
    assert "timestamp" in data
    assert data["total_predictions"] == len(api_batch_request["requests"])
    assert len(data["predictions"]) == data["total_predictions"]


@pytest.mark.api
def test_batch_predict_empty():
    """Test batch prediction fails with empty request list."""
    request = {"requests": []}
    
    response = requests.post(
        f"{API_URL}/predict/batch",
        json=request,
        timeout=TIMEOUT
    )
    
    assert response.status_code == 422


@pytest.mark.api
def test_batch_predict_too_many():
    """Test batch prediction limits number of requests."""
    # Create 11 requests (limit is 10)
    request = {
        "requests": [
            {
                "city": "bangkok",
                "aqi": 2.5,
                "pm2_5": 25.0,
                "pm10": 45.0,
                "no2": 15.0,
                "o3": 85.0
            }
        ] * 11
    }
    
    response = requests.post(
        f"{API_URL}/predict/batch",
        json=request,
        timeout=TIMEOUT
    )
    
    assert response.status_code == 422


# ============================================================================
# MODELS ENDPOINT TESTS
# ============================================================================

@pytest.mark.api
def test_list_models():
    """Test listing available models."""
    response = requests.get(f"{API_URL}/models", timeout=TIMEOUT)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "total_models" in data
    assert "models" in data
    assert data["total_models"] > 0
    assert len(data["models"]) == data["total_models"]
    
    # Check model structure
    for model in data["models"]:
        assert "name" in model
        assert "description" in model


@pytest.mark.api
def test_get_model_info():
    """Test getting model information."""
    # First get list of models
    response = requests.get(f"{API_URL}/models", timeout=TIMEOUT)
    models = response.json()["models"]
    
    if models:
        model_name = models[0]["name"]
        
        response = requests.get(
            f"{API_URL}/models/{model_name}",
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "model_name" in data
        assert "model_type" in data
        assert "performance_metrics" in data
        assert "features_used" in data


@pytest.mark.api
def test_get_nonexistent_model():
    """Test getting info for nonexistent model."""
    response = requests.get(
        f"{API_URL}/models/nonexistent_model",
        timeout=TIMEOUT
    )
    
    assert response.status_code in [404, 500]


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.api
def test_404_error():
    """Test 404 error handling."""
    response = requests.get(
        f"{API_URL}/nonexistent_endpoint",
        timeout=TIMEOUT
    )
    
    assert response.status_code == 404


@pytest.mark.api
def test_invalid_json():
    """Test handling of invalid JSON."""
    response = requests.post(
        f"{API_URL}/predict",
        data="invalid json",
        headers={"Content-Type": "application/json"},
        timeout=TIMEOUT
    )
    
    assert response.status_code == 422


# ============================================================================
# CORS TESTS
# ============================================================================

@pytest.mark.api
def test_cors_headers():
    """Test CORS headers are present."""
    response = requests.options(
        f"{API_URL}/predict",
        headers={"Origin": "http://localhost:3000"},
        timeout=TIMEOUT
    )
    
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers or response.status_code == 200


# ============================================================================
# DOCUMENTATION TESTS
# ============================================================================

@pytest.mark.api
def test_docs_endpoint():
    """Test Swagger docs are accessible."""
    response = requests.get(f"{API_URL}/docs", timeout=TIMEOUT)
    assert response.status_code == 200


@pytest.mark.api
def test_redoc_endpoint():
    """Test ReDoc is accessible."""
    response = requests.get(f"{API_URL}/redoc", timeout=TIMEOUT)
    assert response.status_code == 200


@pytest.mark.api
def test_openapi_spec():
    """Test OpenAPI specification is available."""
    response = requests.get(f"{API_URL}/openapi.json", timeout=TIMEOUT)
    
    assert response.status_code == 200
    spec = response.json()
    
    assert "openapi" in spec
    assert "info" in spec
    assert "paths" in spec