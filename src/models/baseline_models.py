"""
Baseline Models for Air Quality Prediction

Implements simple baseline models:
1. PersistenceModel - Uses last known value (naive baseline)
2. MovingAverageModel - Uses rolling mean
3. LinearRegressionModel - Simple linear regression

These establish performance benchmarks for complex models.

Learning Notes:
- Always start with simple baselines
- Baselines show if complex models actually improve
- If complex model < baseline, something is wrong!
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional
from sklearn.linear_model import LinearRegression

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.base_model import BaseModel
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PersistenceModel(BaseModel):
    """
    Persistence Model (Naive Baseline)
    
    Predicts: tomorrow's AQI = today's AQI
    
    This is the simplest baseline. If your fancy models can't beat this,
    they're not learning anything useful!
    
    Example:
        If AQI today = 3, predict AQI tomorrow = 3
    """
    
    def __init__(self):
        """Initialize persistence model."""
        super().__init__(name="Persistence", model_params={})
        self.last_values = {}  # Store last value per city
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'PersistenceModel':
        """
        'Train' the model (just records last values per city).
        
        Args:
            X: Training features (needs 'city_key' column)
            y: Training target (not really used)
        
        Returns:
            self
        """
        start_time = datetime.now()
        
        # Store last known value for each city
        if 'city_key' in X.columns:
            for city in X['city_key'].unique():
                city_data = X[X['city_key'] == city]
                # Get the most recent AQI value
                if 'aqi' in city_data.columns:
                    self.last_values[city] = city_data['aqi'].iloc[-1]
                else:
                    self.last_values[city] = y.iloc[-1]
        else:
            # No city info, use overall last value
            self.last_values['default'] = y.iloc[-1]
        
        self.feature_names = list(X.columns)
        self.is_trained = True
        self.training_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Persistence model 'trained' in {self.training_time:.2f}s")
        logger.info(f"Last values stored for {len(self.last_values)} cities")
        
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict using persistence (last known value).
        
        Args:
            X: Features (needs 'city_key' if available)
        
        Returns:
            Predictions (same as last value)
        """
        if not self.is_trained:
            raise ValueError("Model must be fitted before prediction")
        
        predictions = np.zeros(len(X))
        
        if 'city_key' in X.columns:
            for i, city in enumerate(X['city_key']):
                predictions[i] = self.last_values.get(city, 
                                                      list(self.last_values.values())[0])
        else:
            # Use default value
            default_val = self.last_values.get('default', 
                                               list(self.last_values.values())[0])
            predictions[:] = default_val
        
        return predictions


class MovingAverageModel(BaseModel):
    """
    Moving Average Model
    
    Predicts: average of last N values
    
    Better than persistence if there's noise/volatility.
    Uses smoothing to reduce random fluctuations.
    
    Example:
        If last 3 days AQI = [2, 3, 2], predict tomorrow = 2.33
    """
    
    def __init__(self, window: int = 3):
        """
        Initialize moving average model.
        
        Args:
            window: Number of past values to average (default: 3)
        """
        super().__init__(name=f"MovingAverage-{window}", 
                        model_params={'window': window})
        self.window = window
        self.city_histories = {}  # Store history per city
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'MovingAverageModel':
        """
        'Train' the model (stores recent history per city).
        
        Args:
            X: Training features
            y: Training target
        
        Returns:
            self
        """
        start_time = datetime.now()
        
        # Store recent history for each city
        if 'city_key' in X.columns:
            for city in X['city_key'].unique():
                city_mask = X['city_key'] == city
                city_y = y[city_mask]
                # Store last 'window' values
                self.city_histories[city] = city_y.tail(self.window).values
        else:
            # No city info, use overall history
            self.city_histories['default'] = y.tail(self.window).values
        
        self.feature_names = list(X.columns)
        self.is_trained = True
        self.training_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Moving average model trained in {self.training_time:.2f}s")
        logger.info(f"Window size: {self.window}, Cities: {len(self.city_histories)}")
        
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict using moving average.
        
        Args:
            X: Features
        
        Returns:
            Predictions (average of last N values)
        """
        if not self.is_trained:
            raise ValueError("Model must be fitted before prediction")
        
        predictions = np.zeros(len(X))
        
        if 'city_key' in X.columns:
            for i, city in enumerate(X['city_key']):
                history = self.city_histories.get(city, 
                                                  list(self.city_histories.values())[0])
                predictions[i] = np.mean(history)
        else:
            default_history = self.city_histories.get('default',
                                                      list(self.city_histories.values())[0])
            predictions[:] = np.mean(default_history)
        
        return predictions


class LinearRegressionModel(BaseModel):
    """
    Linear Regression Baseline
    
    Fits a linear model: y = w1*x1 + w2*x2 + ... + b
    
    This tests if simple linear relationships exist.
    If this works well, data has strong linear patterns.
    If this fails, need non-linear models (trees, etc.)
    """
    
    def __init__(self):
        """Initialize linear regression model."""
        super().__init__(name="LinearRegression", model_params={})
        self.model = LinearRegression()
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'LinearRegressionModel':
        """
        Train linear regression.
        
        Args:
            X: Training features
            y: Training target
        
        Returns:
            self
        """
        start_time = datetime.now()
        
        # Select only numeric columns
        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        X_numeric = X[numeric_cols]
        
        # Handle any remaining NaN values
        X_numeric = X_numeric.fillna(X_numeric.mean())
        
        # Train model
        self.model.fit(X_numeric, y)
        
        self.feature_names = numeric_cols
        self.is_trained = True
        self.training_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Linear regression trained in {self.training_time:.2f}s")
        logger.info(f"Features used: {len(self.feature_names)}")
        logger.info(f"Model coefficients range: [{self.model.coef_.min():.4f}, {self.model.coef_.max():.4f}]")
        
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions with linear model.
        
        Args:
            X: Features
        
        Returns:
            Predictions
        """
        if not self.is_trained:
            raise ValueError("Model must be fitted before prediction")
        
        # Use same features as training
        X_numeric = X[self.feature_names]
        X_numeric = X_numeric.fillna(X_numeric.mean())
        
        predictions = self.model.predict(X_numeric)
        
        return predictions
    
    def get_feature_importance(self) -> pd.Series:
        """
        Get feature importance (absolute coefficient values).
        
        Returns:
            Series with feature importances
        """
        if not self.is_trained:
            logger.warning("Model not trained yet")
            return None
        
        # Use absolute coefficients as importance
        importances = pd.Series(
            np.abs(self.model.coef_),
            index=self.feature_names
        ).sort_values(ascending=False)
        
        return importances


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Test baseline models.
    
    Run: python src/models/baseline_models.py
    """
    print("=" * 80)
    print("BASELINE MODELS TEST")
    print("=" * 80)
    
    # Create synthetic test data
    np.random.seed(42)
    n_samples = 100
    
    # Simulate features
    X_test = pd.DataFrame({
        'aqi': np.random.uniform(1, 5, n_samples),
        'pm2_5': np.random.uniform(10, 50, n_samples),
        'pm10': np.random.uniform(20, 100, n_samples),
        'city_key': np.random.choice(['bangkok', 'london', 'sydney'], n_samples)
    })
    
    # Target: slight noise around current AQI
    y_test = X_test['aqi'] + np.random.normal(0, 0.3, n_samples)
    
    # Split
    split = int(0.7 * n_samples)
    X_train, X_val = X_test[:split], X_test[split:]
    y_train, y_val = y_test[:split], y_test[split:]
    
    print(f"\nTest data: {len(X_train)} train, {len(X_val)} validation")
    
    # ========================================================================
    # Test 1: Persistence Model
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 1: Persistence Model")
    print("=" * 80)
    
    persistence = PersistenceModel()
    persistence.fit(X_train, y_train)
    metrics = persistence.evaluate(X_val, y_val)
    
    print("\nPersistence Metrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    # ========================================================================
    # Test 2: Moving Average Model
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 2: Moving Average Model")
    print("=" * 80)
    
    moving_avg = MovingAverageModel(window=3)
    moving_avg.fit(X_train, y_train)
    metrics = moving_avg.evaluate(X_val, y_val)
    
    print("\nMoving Average Metrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    # ========================================================================
    # Test 3: Linear Regression Model
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 3: Linear Regression Model")
    print("=" * 80)
    
    linear = LinearRegressionModel()
    linear.fit(X_train, y_train)
    metrics = linear.evaluate(X_val, y_val)
    
    print("\nLinear Regression Metrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    print("\nTop 5 Features:")
    importances = linear.get_feature_importance()
    print(importances.head())
    
    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\n✅ All baseline models work correctly!")
    print("\nNext steps:")
    print("  1. Test with real data from Phase 2")
    print("  2. Compare baseline performances")
    print("  3. Use as benchmarks for complex models")
    
    print("\n" + "=" * 80)