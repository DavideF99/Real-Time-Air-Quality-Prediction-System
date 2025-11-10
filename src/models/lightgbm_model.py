"""
LightGBM Model

Light Gradient Boosting Machine - fast and efficient!

How it works:
- Gradient boosting like XGBoost
- Leaf-wise tree growth (faster)
- Histogram-based splitting
- Optimized for speed and memory

Best for:
- Large datasets
- When training time matters
- Similar accuracy to XGBoost, faster
- Memory-efficient

Learning Notes:
- Developed by Microsoft
- Often faster than XGBoost
- Good for datasets with many features
- Requires less memory
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

# Try to import LightGBM
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logger.warning("LightGBM not installed. Install with: pip install lightgbm")


class LightGBMModel(BaseModel):
    """
    LightGBM (Light Gradient Boosting Machine) for AQI prediction.
    
    Fast gradient boosting that:
    1. Builds trees leaf-wise (not level-wise)
    2. Uses histogram-based splitting
    3. Optimized for speed and memory
    4. Similar accuracy to XGBoost
    
    Advantages:
    - Very fast training
    - Memory efficient
    - Handles large datasets well
    - Good accuracy
    - Built-in categorical features
    - Less prone to overfitting
    
    Usage:
        model = LightGBMModel(n_estimators=100, max_depth=6)
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
    """
    
    def __init__(self,
                 n_estimators: int = 100,
                 max_depth: int = -1,
                 learning_rate: float = 0.1,
                 num_leaves: int = 31,
                 subsample: float = 0.8,
                 colsample_bytree: float = 0.8,
                 reg_alpha: float = 0.0,
                 reg_lambda: float = 0.0,
                 random_state: int = 42,
                 n_jobs: int = -1):
        """
        Initialize LightGBM model.
        
        Args:
            n_estimators: Number of boosting rounds (default: 100)
                - More rounds = better fit but slower
                - Typical range: 50-500
            max_depth: Maximum tree depth (default: -1 = unlimited)
                - Limit to prevent overfitting
                - Typical range: 3-10, -1 for unlimited
            learning_rate: Step size (default: 0.1)
                - Lower = slower but better
                - Typical range: 0.01-0.3
            num_leaves: Maximum leaves per tree (default: 31)
                - More leaves = more complex model
                - Typical range: 20-50
            subsample: Fraction of samples (default: 0.8)
                - Prevents overfitting
                - Typical range: 0.5-1.0
            colsample_bytree: Fraction of features (default: 0.8)
                - Prevents overfitting
                - Typical range: 0.5-1.0
            reg_alpha: L1 regularization (default: 0.0)
            reg_lambda: L2 regularization (default: 0.0)
            random_state: Random seed
            n_jobs: CPU cores (-1 = all)
        """
        if not LIGHTGBM_AVAILABLE:
            raise ImportError("LightGBM not installed. Run: pip install lightgbm")
        
        model_params = {
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'learning_rate': learning_rate,
            'num_leaves': num_leaves,
            'subsample': subsample,
            'colsample_bytree': colsample_bytree,
            'reg_alpha': reg_alpha,
            'reg_lambda': reg_lambda,
            'random_state': random_state,
            'n_jobs': n_jobs
        }
        
        super().__init__(name="LightGBM", model_params=model_params)
        
        # Create LightGBM model
        self.model = lgb.LGBMRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            num_leaves=num_leaves,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            reg_alpha=reg_alpha,
            reg_lambda=reg_lambda,
            random_state=random_state,
            n_jobs=n_jobs,
            verbosity=-1  # Quiet mode
        )
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'LightGBMModel':
        """
        Train the LightGBM model.
        
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
        
        # Handle NaN values
        X_numeric = X_numeric.fillna(X_numeric.mean())
        
        logger.info(f"Training LightGBM with {len(numeric_cols)} features...")
        logger.info(f"Parameters: n_estimators={self.model_params['n_estimators']}, "
                   f"num_leaves={self.model_params['num_leaves']}, "
                   f"learning_rate={self.model_params['learning_rate']}")
        
        # Train model
        self.model.fit(X_numeric, y)
        
        self.feature_names = numeric_cols
        self.is_trained = True
        self.training_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✓ LightGBM trained in {self.training_time:.2f}s")
        logger.info(f"  Boosting rounds: {self.model.n_estimators}")
        logger.info(f"  Num leaves: {self.model.num_leaves}")
        
        # Log top features
        importances = self.get_feature_importance()
        if importances is not None:
            logger.info(f"  Top 5 features: {', '.join(importances.head().index.tolist())}")
        
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions with LightGBM.
        
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
        Get feature importance from LightGBM.
        
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
            'num_leaves': self.model.num_leaves,
            'max_depth': self.model.max_depth,
            'learning_rate': self.model.learning_rate,
            'n_features': len(self.feature_names)
        }
        
        # Get best iteration if early stopping was used
        if hasattr(self.model, 'best_iteration_'):
            info['best_iteration'] = self.model.best_iteration_
        
        return info


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Test LightGBM model.
    
    Run: python src/models/lightgbm_model.py
    """
    print("=" * 80)
    print("LIGHTGBM MODEL TEST")
    print("=" * 80)
    
    if not LIGHTGBM_AVAILABLE:
        print("\n❌ LightGBM not installed!")
        print("\nInstall with:")
        print("  pip install lightgbm")
        exit(1)
    
    # Create synthetic test data
    np.random.seed(42)
    n_samples = 200
    
    # Simulate features
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
    # Test 1: Default LightGBM
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 1: Default LightGBM")
    print("=" * 80)
    
    lgb_default = LightGBMModel()
    lgb_default.fit(X_train, y_train)
    metrics = lgb_default.evaluate(X_val, y_val)
    
    print("\nDefault LightGBM Metrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    print("\nBooster Info:")
    booster_info = lgb_default.get_booster_info()
    for key, value in booster_info.items():
        print(f"  {key}: {value}")
    
    # ========================================================================
    # Test 2: Optimized LightGBM
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 2: Optimized LightGBM (faster, regularized)")
    print("=" * 80)
    
    lgb_optimized = LightGBMModel(
        n_estimators=150,
        num_leaves=25,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=0.1
    )
    lgb_optimized.fit(X_train, y_train)
    metrics = lgb_optimized.evaluate(X_val, y_val)
    
    print("\nOptimized LightGBM Metrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    print("\nTop 5 Features:")
    importances = lgb_optimized.get_feature_importance()
    print(importances.head())
    
    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\n✅ LightGBM model works correctly!")
    print("\nKey advantages:")
    print("  • Very fast training")
    print("  • Memory efficient")
    print("  • Good accuracy")
    print("  • Handles large datasets")
    print("  • Similar to XGBoost but faster")
    print("\nNext: Test with real data via CLI:")
    print("  python scripts/train_models.py --model lightgbm --compare --visualize")