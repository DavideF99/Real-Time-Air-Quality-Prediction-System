"""
Test Fixtures and Configuration

Shared fixtures for all tests.

Usage:
    pytest tests/
"""

import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ============================================================================
# DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_pollutants():
    """Sample pollutant data for testing."""
    return {
        'aqi': 2.5,
        'pm2_5': 25.0,
        'pm10': 45.0,
        'no2': 15.0,
        'o3': 85.0,
        'co': 250.0,
        'so2': 5.0,
        'nh3': 2.0
    }


@pytest.fixture
def sample_dataframe():
    """Sample DataFrame for testing."""
    np.random.seed(42)
    
    n_samples = 100
    dates = pd.date_range(start='2025-01-01', periods=n_samples, freq='H')
    
    df = pd.DataFrame({
        'timestamp': dates,
        'city_key': np.random.choice(['bangkok', 'london', 'sydney'], n_samples),
        'city_name': np.random.choice(['Bangkok', 'London', 'Sydney'], n_samples),
        'country': np.random.choice(['Thailand', 'UK', 'Australia'], n_samples),
        'aqi': np.random.uniform(1, 5, n_samples),
        'pm2_5': np.random.uniform(10, 50, n_samples),
        'pm10': np.random.uniform(20, 100, n_samples),
        'no2': np.random.uniform(5, 40, n_samples),
        'o3': np.random.uniform(50, 150, n_samples),
        'co': np.random.uniform(200, 400, n_samples),
        'so2': np.random.uniform(0, 20, n_samples),
        'nh3': np.random.uniform(0, 10, n_samples)
    })
    
    return df


@pytest.fixture
def sample_features():
    """Sample engineered features DataFrame."""
    np.random.seed(42)
    
    n_samples = 100  # Changed from 50 to 100 to match sample_dataframe
    
    df = pd.DataFrame({
        'aqi': np.random.uniform(1, 5, n_samples),
        'pm2_5': np.random.uniform(10, 50, n_samples),
        'pm10': np.random.uniform(20, 100, n_samples),
        'no2': np.random.uniform(5, 40, n_samples),
        'o3': np.random.uniform(50, 150, n_samples),
        'aqi_lag_1h': np.random.uniform(1, 5, n_samples),
        'aqi_lag_24h': np.random.uniform(1, 5, n_samples),
        'aqi_rolling_mean_24h': np.random.uniform(1, 5, n_samples),
        'aqi_rolling_std_24h': np.random.uniform(0, 1, n_samples),
        'hour_sin': np.sin(np.random.uniform(0, 2*np.pi, n_samples)),
        'hour_cos': np.cos(np.random.uniform(0, 2*np.pi, n_samples)),
        'city_key': np.random.choice([0, 1, 2], n_samples)
    })
    
    return df


@pytest.fixture
def sample_target():
    """Sample target variable."""
    np.random.seed(42)
    return pd.Series(np.random.uniform(1, 5, 100))  # Changed from 50 to 100


# ============================================================================
# API FIXTURES
# ============================================================================

@pytest.fixture
def api_prediction_request():
    """Sample API prediction request."""
    return {
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


@pytest.fixture
def api_batch_request(api_prediction_request):
    """Sample batch prediction request."""
    return {
        "requests": [
            api_prediction_request,
            {**api_prediction_request, "city": "london", "aqi": 1.8}
        ]
    }


# ============================================================================
# MODEL FIXTURES
# ============================================================================

@pytest.fixture
def mock_model():
    """Mock model for testing."""
    from unittest.mock import Mock
    
    model = Mock()
    model.name = "MockModel"
    model.is_trained = True
    model.feature_names = ['aqi', 'pm2_5', 'pm10', 'no2', 'o3']
    model.predict.return_value = np.array([2.8])
    model.evaluate.return_value = {
        'rmse': 0.4,
        'mae': 0.3,
        'r2': 0.5,
        'mape': 15.0,
        'category_accuracy': 0.8,
        'within_1_aqi': 0.9
    }
    
    return model


@pytest.fixture
def temp_model_file(tmp_path, mock_model):
    """Temporary model file for testing."""
    import joblib
    
    model_data = {
        'name': 'TestModel',
        'model': mock_model,
        'model_params': {},
        'feature_names': mock_model.feature_names,
        'is_trained': True,
        'training_time': 1.0,
        'metrics': {},
        'saved_at': datetime.now().isoformat()
    }
    
    model_path = tmp_path / "test_model.joblib"
    joblib.dump(model_data, model_path)
    
    return model_path


# ============================================================================
# FILE FIXTURES
# ============================================================================

@pytest.fixture
def temp_data_dir(tmp_path):
    """Temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create subdirectories
    (data_dir / "raw").mkdir()
    (data_dir / "processed").mkdir()
    (data_dir / "models").mkdir()
    (data_dir / "logs").mkdir()
    
    return data_dir


@pytest.fixture
def sample_csv_file(tmp_path, sample_dataframe):
    """Sample CSV file for testing."""
    csv_path = tmp_path / "test_data.csv"
    sample_dataframe.to_csv(csv_path, index=False)
    return csv_path


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_logs():
    """Cleanup log files after each test."""
    yield
    # Add cleanup code here if needed


@pytest.fixture(scope="session")
def performance_results():
    """Store performance test results."""
    return {}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def assert_valid_aqi(value):
    """Assert AQI value is valid."""
    assert isinstance(value, (int, float)), "AQI must be numeric"
    assert 1.0 <= value <= 5.0, f"AQI must be between 1 and 5, got {value}"


def assert_valid_prediction_response(response):
    """Assert prediction response has valid structure."""
    required_keys = [
        'city', 'current_aqi', 'predicted_aqi', 
        'predicted_category', 'confidence_interval',
        'health_message', 'model_used', 'timestamp'
    ]
    
    for key in required_keys:
        assert key in response, f"Missing key: {key}"
    
    assert_valid_aqi(response['predicted_aqi'])
    assert 'lower' in response['confidence_interval']
    assert 'upper' in response['confidence_interval']


def assert_dataframe_valid(df, required_columns=None):
    """Assert DataFrame is valid."""
    assert isinstance(df, pd.DataFrame), "Must be a DataFrame"
    assert len(df) > 0, "DataFrame must not be empty"
    
    if required_columns:
        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"


# ============================================================================
# PYTEST HOOKS
# ============================================================================

def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "api: API tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Add markers based on test name
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "api" in item.nodeid:
            item.add_marker(pytest.mark.api)
        else:
            item.add_marker(pytest.mark.unit)