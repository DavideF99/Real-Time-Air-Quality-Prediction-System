"""
Random Forest Model

Ensemble of decision trees for robust predictions.

How it works:
- Creates multiple decision trees
- Each tree trained on random subset of data
- Final prediction = average of all trees
- Reduces overfitting, handles non-linearity

Best for:
- Non-linear relationships
- Feature interactions
- Robust to outliers
- Good baseline for tree-based methods

Learning Notes:
- n_estimators: Number of trees (more = better, slower)
- max_depth: Maximum tree depth (prevents overfitting)
- min_samples_split: Minimum samples to split node
- Bootstrap sampling reduces variance
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional, Dict
from sklearn.ensemble import RandomForestRegressor

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.base_model import BaseModel
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RandomForestModel(BaseModel):
    """
    Random Forest Regressor for AQI prediction.
    
    Ensemble method that:
    1. Creates many decision trees
    2. Each tree sees random subset of data
    3. Averages predictions from all trees
    
    Advantages:
    - Handles non-linear relationships
    - Automatic feature interactions
    - Robust to outliers
    - Feature importance ranking
    - Less prone to overfitting than single tree
    
    Usage:
        model = RandomForestModel(n_estimators=100, max_depth=10)
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
    """
    
    def __init__(self, 
                 n_estimators: int = 100,
                 max_depth: Optional[int] = None,
                 min_samples_split: int = 2,
                 min_samples_leaf: int = 1,
                 max_features: str = 'sqrt',
                 random_state: int = 42,
                 n_jobs: int = -1):
        """
        Initialize Random Forest model.
        
        Args:
            n_estimators: Number of trees in forest (default: 100)
                - More trees = better performance but slower
                - Typical range: 50-500
            max_depth: Maximum depth of trees (default: None = unlimited)
                - Limit to prevent overfitting
                - Typical range: 5-20
            min_samples_split: Min samples required to split node (default: 2)
                - Higher = simpler trees
            min_samples_leaf: Min samples in leaf node (default: 1)
                - Higher = smoother predictions
            max_features: Features to consider for split (default: 'sqrt')
                - 'sqrt': sqrt(n_features) - good for many features
                - 'log2': log2(n_features)
                - int: specific number
            random_state: Random seed for reproducibility
            n_jobs: CPU cores to use (-1 = all cores)
        """
        model_params = {
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'min_samples_split': min_samples_split,
            'min_samples_leaf': min_samples_leaf,
            'max_features': max_features,
            'random_state': random_state,
            'n_jobs': n_jobs
        }
        
        super().__init__(name="RandomForest", model_params=model_params)
        
        # Create sklearn model
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            max_features=max_features,
            random_state=random_state,
            n_jobs=n_jobs,
            verbose=0
        )
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'RandomForestModel':
        """
        Train the Random Forest model.
        
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
        
        # Handle any remaining NaN values
        X_numeric = X_numeric.fillna(X_numeric.mean())
        
        logger.info(f"Training Random Forest with {len(numeric_cols)} features...")
        logger.info(f"Parameters: {self.model_params}")
        
        # Train model
        self.model.fit(X_numeric, y)
        
        self.feature_names = numeric_cols
        self.is_trained = True
        self.training_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✓ Random Forest trained in {self.training_time:.2f}s")
        logger.info(f"  Trees: {self.model.n_estimators}")
        logger.info(f"  Max depth: {self.model.max_depth if self.model.max_depth else 'unlimited'}")
        
        # Log top features
        importances = self.get_feature_importance()
        if importances is not None:
            logger.info(f"  Top 5 features: {', '.join(importances.head().index.tolist())}")
        
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions with Random Forest.
        
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
        Get feature importance from the forest.
        
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
    
    def get_tree_info(self) -> Dict:
        """
        Get information about the forest.
        
        Returns:
            Dictionary with tree statistics
        """
        if not self.is_trained:
            return {}
        
        # Get depths of all trees
        tree_depths = [tree.get_depth() for tree in self.model.estimators_]
        
        # Get number of leaves for all trees
        tree_leaves = [tree.get_n_leaves() for tree in self.model.estimators_]
        
        info = {
            'n_trees': self.model.n_estimators,
            'avg_depth': np.mean(tree_depths),
            'max_depth': np.max(tree_depths),
            'min_depth': np.min(tree_depths),
            'avg_leaves': np.mean(tree_leaves),
            'total_leaves': np.sum(tree_leaves)
        }
        
        return info


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Test Random Forest model.
    
    Run: python src/models/random_forest_model.py
    """
    print("=" * 80)
    print("RANDOM FOREST MODEL TEST")
    print("=" * 80)
    
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
    
    # Target: non-linear combination with noise
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
    # Test 1: Default Random Forest
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 1: Default Random Forest")
    print("=" * 80)
    
    rf_default = RandomForestModel()
    rf_default.fit(X_train, y_train)
    metrics = rf_default.evaluate(X_val, y_val)
    
    print("\nDefault Random Forest Metrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    print("\nTree Info:")
    tree_info = rf_default.get_tree_info()
    for key, value in tree_info.items():
        print(f"  {key}: {value:.2f}")
    
    # ========================================================================
    # Test 2: Optimized Random Forest
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 2: Optimized Random Forest (more trees, limited depth)")
    print("=" * 80)
    
    rf_optimized = RandomForestModel(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5
    )
    rf_optimized.fit(X_train, y_train)
    metrics = rf_optimized.evaluate(X_val, y_val)
    
    print("\nOptimized Random Forest Metrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    print("\nTop 5 Features:")
    importances = rf_optimized.get_feature_importance()
    print(importances.head())
    
    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\n✅ Random Forest model works correctly!")
    print("\nKey advantages:")
    print("  • Handles non-linear relationships")
    print("  • Automatic feature interactions")
    print("  • Built-in feature importance")
    print("  • Robust to outliers")
    print("\nNext: Test with real data via CLI:")
    print("  python scripts/train_models.py --model random-forest --compare --visualize")