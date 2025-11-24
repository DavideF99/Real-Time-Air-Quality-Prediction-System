"""
Model Unit Tests

Tests for ML models and training pipeline.

Run:
    pytest tests/test_models_unit.py -v
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path


# ============================================================================
# BASE MODEL TESTS
# ============================================================================

@pytest.mark.unit
def test_base_model_initialization():
    """Test BaseModel can be initialized."""
    from src.models.base_model import BaseModel
    
    # BaseModel is abstract, so we can't instantiate it directly
    # But we can test its structure
    assert hasattr(BaseModel, 'fit')
    assert hasattr(BaseModel, 'predict')
    assert hasattr(BaseModel, 'evaluate')
    assert hasattr(BaseModel, 'save')
    assert hasattr(BaseModel, 'load')


# ============================================================================
# BASELINE MODELS TESTS
# ============================================================================

@pytest.mark.unit
def test_persistence_model(sample_features, sample_target):
    """Test PersistenceModel."""
    from src.models.baseline_models import PersistenceModel
    
    model = PersistenceModel()
    assert model.name == "Persistence"
    assert not model.is_trained
    
    # Add city_key for training
    X = sample_features.copy()
    X['city_key'] = 'bangkok'
    
    # Train
    model.fit(X, sample_target)
    assert model.is_trained
    
    # Predict
    predictions = model.predict(X.head(5))
    assert len(predictions) == 5
    assert all(1.0 <= p <= 5.0 for p in predictions)


@pytest.mark.unit
def test_moving_average_model(sample_features, sample_target):
    """Test MovingAverageModel."""
    from src.models.baseline_models import MovingAverageModel
    
    model = MovingAverageModel(window=3)
    assert model.name == "MovingAverage-3"
    
    X = sample_features.copy()
    X['city_key'] = 'bangkok'
    
    model.fit(X, sample_target)
    assert model.is_trained
    
    predictions = model.predict(X.head(5))
    assert len(predictions) == 5


@pytest.mark.unit
def test_linear_regression_model(sample_features, sample_target):
    """Test LinearRegressionModel."""
    from src.models.baseline_models import LinearRegressionModel
    
    model = LinearRegressionModel()
    assert model.name == "LinearRegression"
    
    model.fit(sample_features, sample_target)
    assert model.is_trained
    
    predictions = model.predict(sample_features.head(5))
    assert len(predictions) == 5
    
    # Test feature importance
    importance = model.get_feature_importance()
    assert importance is not None
    assert len(importance) > 0


# ============================================================================
# RANDOM FOREST TESTS
# ============================================================================

@pytest.mark.unit
def test_random_forest_initialization():
    """Test RandomForestModel initialization."""
    from src.models.random_forest_model import RandomForestModel
    
    model = RandomForestModel(n_estimators=10, max_depth=5)
    assert model.name == "RandomForest"
    assert model.model_params['n_estimators'] == 10
    assert model.model_params['max_depth'] == 5


@pytest.mark.unit
def test_random_forest_training(sample_features, sample_target):
    """Test RandomForestModel training."""
    from src.models.random_forest_model import RandomForestModel
    
    model = RandomForestModel(n_estimators=10, max_depth=5)
    model.fit(sample_features, sample_target)
    
    assert model.is_trained
    assert model.training_time is not None
    assert model.training_time > 0
    
    # Test prediction
    predictions = model.predict(sample_features.head(5))
    assert len(predictions) == 5
    assert all(isinstance(p, (int, float, np.number)) for p in predictions)


@pytest.mark.unit
def test_random_forest_feature_importance(sample_features, sample_target):
    """Test RandomForest feature importance."""
    from src.models.random_forest_model import RandomForestModel
    
    model = RandomForestModel(n_estimators=10)
    model.fit(sample_features, sample_target)
    
    importance = model.get_feature_importance()
    assert importance is not None
    assert len(importance) == len(sample_features.columns)
    assert all(importance >= 0)


# ============================================================================
# MODEL EVALUATION TESTS
# ============================================================================

@pytest.mark.unit
def test_model_evaluate(sample_features, sample_target):
    """Test model evaluation."""
    from src.models.baseline_models import LinearRegressionModel
    
    model = LinearRegressionModel()
    model.fit(sample_features, sample_target)
    
    metrics = model.evaluate(sample_features, sample_target)
    
    # Check all metrics are present
    assert 'rmse' in metrics
    assert 'mae' in metrics
    assert 'r2' in metrics
    assert 'mape' in metrics
    assert 'category_accuracy' in metrics
    assert 'within_1_aqi' in metrics
    
    # Check metrics are reasonable
    assert metrics['rmse'] >= 0
    assert metrics['mae'] >= 0
    assert 0 <= metrics['r2'] <= 1 or metrics['r2'] < 0  # R2 can be negative
    assert metrics['mape'] >= 0
    assert 0 <= metrics['category_accuracy'] <= 1
    assert 0 <= metrics['within_1_aqi'] <= 1


# ============================================================================
# MODEL PERSISTENCE TESTS
# ============================================================================

@pytest.mark.unit
def test_model_save_load(sample_features, sample_target, tmp_path):
    """Test model save and load."""
    from src.models.baseline_models import LinearRegressionModel
    
    # Train model
    model = LinearRegressionModel()
    model.fit(sample_features, sample_target)
    
    # Save
    save_path = tmp_path / "test_model.joblib"
    model.save(save_path)
    assert save_path.exists()
    
    # Load
    loaded_model = LinearRegressionModel.load(save_path)
    assert loaded_model.is_trained
    assert loaded_model.name == model.name
    
    # Test predictions match
    pred1 = model.predict(sample_features.head(5))
    pred2 = loaded_model.predict(sample_features.head(5))
    np.testing.assert_array_almost_equal(pred1, pred2)


# ============================================================================
# TRAINER TESTS
# ============================================================================

@pytest.mark.unit
def test_model_trainer_initialization():
    """Test ModelTrainer initialization."""
    from src.models.train import ModelTrainer
    
    trainer = ModelTrainer()
    assert trainer.data_dir.exists()
    assert trainer.results_dir.exists()


# ============================================================================
# FEATURE SELECTOR TESTS
# ============================================================================

@pytest.mark.unit
def test_feature_selector_correlation(sample_features, sample_target):
    """Test correlation-based feature selection."""
    from src.utils.feature_selector import FeatureSelector
    
    selector = FeatureSelector()
    selected = selector.select_by_correlation(sample_features, sample_target, top_n=5)
    
    assert len(selected) == 5
    assert all(col in sample_features.columns for col in selected)


@pytest.mark.unit
def test_feature_selector_mutual_info(sample_features, sample_target):
    """Test mutual information feature selection."""
    from src.utils.feature_selector import FeatureSelector
    
    selector = FeatureSelector()
    selected = selector.select_by_mutual_info(sample_features, sample_target, top_n=5)
    
    assert len(selected) == 5
    assert all(col in sample_features.columns for col in selected)


@pytest.mark.unit
def test_feature_selector_combined(sample_features, sample_target):
    """Test combined feature selection."""
    from src.utils.feature_selector import FeatureSelector
    
    selector = FeatureSelector()
    X_selected = selector.select_features(
        sample_features, 
        sample_target,
        method='combined',
        top_n=5
    )
    
    assert isinstance(X_selected, pd.DataFrame)
    assert len(X_selected.columns) >= 5  # At least 5 (could be more if overlap)
    assert len(X_selected.columns) <= 10  # At most 10 (5 from each method)


# ============================================================================
# DATA VALIDATION TESTS
# ============================================================================

@pytest.mark.unit
def test_aqi_value_validation():
    """Test AQI value validation."""
    from tests.conftest import assert_valid_aqi
    
    # Valid values
    assert_valid_aqi(1.0)
    assert_valid_aqi(2.5)
    assert_valid_aqi(5.0)
    
    # Invalid values
    with pytest.raises(AssertionError):
        assert_valid_aqi(0.5)  # Too low
    
    with pytest.raises(AssertionError):
        assert_valid_aqi(6.0)  # Too high
    
    with pytest.raises(AssertionError):
        assert_valid_aqi("invalid")  # Not numeric


@pytest.mark.unit
def test_dataframe_validation(sample_dataframe):
    """Test DataFrame validation."""
    from tests.conftest import assert_dataframe_valid
    
    # Valid DataFrame
    assert_dataframe_valid(sample_dataframe)
    
    # Required columns
    assert_dataframe_valid(
        sample_dataframe,
        required_columns=['aqi', 'pm2_5', 'timestamp']
    )
    
    # Empty DataFrame
    with pytest.raises(AssertionError):
        assert_dataframe_valid(pd.DataFrame())
    
    # Missing column
    with pytest.raises(AssertionError):
        assert_dataframe_valid(
            sample_dataframe,
            required_columns=['nonexistent_column']
        )


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

@pytest.mark.unit
def test_get_aqi_category():
    """Test AQI category mapping."""
    from src.api.models import get_aqi_category
    
    assert get_aqi_category(1.0).value == "Good"
    assert get_aqi_category(2.0).value == "Moderate"
    assert get_aqi_category(3.0).value == "Unhealthy for Sensitive Groups"
    assert get_aqi_category(4.0).value == "Unhealthy"
    assert get_aqi_category(5.0).value == "Very Unhealthy"


@pytest.mark.unit
def test_get_health_message():
    """Test health message generation."""
    from src.api.models import get_health_message
    
    # Good air quality
    message = get_health_message(1.0)
    assert "good" in message.lower() or "perfect" in message.lower()
    
    # Unhealthy
    message = get_health_message(4.0)
    assert "health effects" in message.lower() or "reduce" in message.lower()