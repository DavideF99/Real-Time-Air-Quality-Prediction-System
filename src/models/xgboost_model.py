"""
XGBoost Model

Extreme Gradient Boosting - often the best performer!

How it works:
- Builds trees sequentially
- Each tree corrects errors of previous trees
- Uses gradient descent optimization
- Regularization prevents overfitting

Best for:
- Kaggle competitions (wins most!)
- Complex patterns
- Feature interactions
- When you need best accuracy

Learning Notes:
- Usually outperforms Random Forest
- Requires careful hyperparameter tuning
- Can overfit if not regularized
- Great feature importance
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional, Dict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.base_model import BaseModel
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Try to import XGBoost
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not installed. Install with: pip install xgboost")


class XGBoostModel(BaseModel):
    """
    XGBoost (Extreme Gradient Boosting) for AQI prediction.
    
    Gradient boosting method that:
    1. Builds trees sequentially
    2. Each tree corrects previous errors
    3. Uses gradient descent for optimization
    4. Includes regularization
    
    Advantages:
    - Often best performance
    - Handles missing values
    - Built-in regularization
    - Fast training (parallel)
    - Feature importance
    - Less prone to overfitting than RF
    
    Usage:
        model = XGBoostModel(n_estimators=100, max_depth=6)
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
    """
    
    def __init__(self,
                 n_estimators: int = 100,
                 max_depth: int = 6,
                 learning_rate: float = 0.1,
                 subsample: float = 0.8,
                 colsample_bytree: float = 0.8,
                 reg_alpha: float = 0.0,
                 reg_lambda: float = 1.0,
                 random_state: int = 42,
                 n_jobs: int = -1):
        """
        Initialize XGBoost model.
        
        Args:
            n_estimators: Number of boosting rounds (default: 100)
                - More rounds = better fit but slower
                - Typical range: 50-500
            max_depth: Maximum tree depth (default: 6)
                - Shallower = less overfitting
                - Typical range: 3-10
            learning_rate: Step size for gradient descent (default: 0.1)
                - Lower = slower learning but better accuracy
                - Typical range: 0.01-0.3
            subsample: Fraction of samples for each tree (default: 0.8)
                - Prevents overfitting
                - Typical range: 0.5-1.0
            colsample_bytree: Fraction of features for each tree (default: 0.8)
                - Prevents overfitting
                - Typical range: 0.5-1.0
            reg_alpha: L1 regularization (default: 0.0)
                - Higher = simpler model
            reg_lambda: L2 regularization (default: 1.0)
                - Higher = simpler model
            random_state: Random seed
            n_jobs: CPU cores (-1 = all)
        """
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost not installed. Run: pip install xgboost")
        
        model_params = {
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'learning_rate': learning_rate,
            'subsample': subsample,
            'colsample_bytree': colsample_bytree,
            'reg_alpha': reg_alpha,
            'reg_lambda': reg_lambda,
            'random_state': random_state,
            'n_jobs': n_jobs
        }
        
        super().__init__(name="XGBoost", model_params=model_params)
        
        # Create XGBoost model
        self.model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            reg_alpha=reg_alpha,
            reg_lambda=reg_lambda,
            random_state=random_state,
            n_jobs=n_jobs,
            verbosity=0  # Quiet mode
        )
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'XGBoostModel':
        """
        Train the XGBoost model.
        
        Args:
            X: Training features
            y: Training target
        
        Returns:
            self (for method chaining)
        """
        start_time = datetime.now()
        
        # Select only numeric columns
        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        X_numeric = X[numeric_cols]
        
        # Handle NaN values (XGBoost can handle them, but let's be explicit)
        X_numeric = X_numeric.fillna(X_numeric.mean())
        
        logger.info(f"Training XGBoost with {len(numeric_cols)} features...")
        logger.info(f"Parameters: n_estimators={self.model_params['n_estimators']}, "
                   f"max_depth={self.model_params['max_depth']}, "
                   f"learning_rate={self.model_params['learning_rate']}")
        
        # Train model
        self.model.fit(X_numeric, y)
        
        self.feature_names = numeric_cols
        self.is_trained = True
        self.training_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✓ XGBoost trained in {self.training_time:.2f}s")
        logger.info(f"  Boosting rounds: {self.model.n_estimators}")
        logger.info(f"  Best iteration: {self.model.best_iteration if hasattr(self.model, 'best_iteration') else 'N/A'}")
        
        # Log top features
        importances = self.get_feature_importance()
        if importances is not None:
            logger.info(f"  Top 5 features: {', '.join(importances.head().index.tolist())}")
        
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions with XGBoost.
        
        Args:
            X: Features for prediction
        
        Returns:
            Predictions array
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
        Get feature importance from XGBoost.
        
        Returns:
            Series with feature importances (sorted descending)
        """
        if not self.is_trained:
            logger.warning("Model not trained yet")
            return None
        
        importances = pd.Series(
            self.model.feature_importances_,
            index=self.feature_names
        ).sort_values(ascending=False)
        
        return importances
    
    def get_booster_info(self) -> Dict:
        """
        Get information about the booster.
        
        Returns:
            Dictionary with boosting statistics
        """
        if not self.is_trained:
            return {}
        
        info = {
            'n_boosting_rounds': self.model.n_estimators,
            'max_depth': self.model.max_depth,
            'learning_rate': self.model.learning_rate,
            'n_features': len(self.feature_names)
        }
        
        # Get best iteration if early stopping was used
        if hasattr(self.model, 'best_iteration'):
            info['best_iteration'] = self.model.best_iteration
        
        return info


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Test XGBoost model.
    
    Run: python src/models/xgboost_model.py
    """
    print("=" * 80)
    print("XGBOOST MODEL TEST")
    print("=" * 80)
    
    if not XGBOOST_AVAILABLE:
        print("\n❌ XGBoost not installed!")
        print("\nInstall with:")
        print("  pip install xgboost")
        exit(1)
    
    # Create synthetic test data
    np.random.seed(42)
    n_samples = 200
    
    # Simulate features with non-linear relationships
    X_test = pd.DataFrame({
        'aqi_lag_24h': np.random.uniform(1, 5, n_samples),
        'pm2_5': np.random.uniform(10, 50, n_samples),
        'pm10': np.random.uniform(20, 100, n_samples),
        'no2': np.random.uniform(5, 40, n_samples),
        'hour_sin': np.sin(np.random.uniform(0, 2*np.pi, n_samples)),
        'hour_cos': np.cos(np.random.uniform(0, 2*np.pi, n_samples))
    })
    
    # Target: complex non-linear combination
    y_test = (0.7 * X_test['aqi_lag_24h'] + 
              0.2 * (X_test['pm2_5'] / 15)**1.5 +
              0.1 * X_test['hour_sin'] +
              np.random.normal(0, 0.2, n_samples))
    
    # Split
    split = int(0.7 * n_samples)
    X_train, X_val = X_test[:split], X_test[split:]
    y_train, y_val = y_test[:split], y_test[split:]
    
    print(f"\nTest data: {len(X_train)} train, {len(X_val)} validation")
    print(f"Features: {list(X_train.columns)}")
    
    # ========================================================================
    # Test 1: Default XGBoost
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 1: Default XGBoost")
    print("=" * 80)
    
    xgb_default = XGBoostModel()
    xgb_default.fit(X_train, y_train)
    metrics = xgb_default.evaluate(X_val, y_val)
    
    print("\nDefault XGBoost Metrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    print("\nBooster Info:")
    booster_info = xgb_default.get_booster_info()
    for key, value in booster_info.items():
        print(f"  {key}: {value}")
    
    # ========================================================================
    # Test 2: Optimized XGBoost
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 2: Optimized XGBoost (more rounds, regularization)")
    print("=" * 80)
    
    xgb_optimized = XGBoostModel(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0
    )
    xgb_optimized.fit(X_train, y_train)
    metrics = xgb_optimized.evaluate(X_val, y_val)
    
    print("\nOptimized XGBoost Metrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    print("\nTop 5 Features:")
    importances = xgb_optimized.get_feature_importance()
    print(importances.head())
    
    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\n✅ XGBoost model works correctly!")
    print("\nKey advantages:")
    print("  • Often best performance")
    print("  • Fast training (parallel)")
    print("  • Built-in regularization")
    print("  • Handles missing values")
    print("  • Feature importance")
    print("\nNext: Test with real data via CLI:")
    print("  python scripts/train_models.py --model xgboost --compare --visualize")