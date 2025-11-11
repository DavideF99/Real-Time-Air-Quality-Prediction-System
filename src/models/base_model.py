"""
Base Model Class

Provides common interface for all models in the project.

Learning Notes:
- Abstract base class ensures consistency across models
- Standardized fit/predict interface
- Built-in evaluation metrics
- Model persistence (save/load)
"""

import sys
from pathlib import Path
from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseModel(ABC):
    """
    Abstract base class for all ML models.
    
    This ensures all models have consistent interface:
    - fit() for training
    - predict() for inference
    - evaluate() for metrics
    - save() and load() for persistence
    
    Usage:
        class MyModel(BaseModel):
            def fit(self, X, y):
                # Your training code
                pass
            
            def predict(self, X):
                # Your prediction code
                pass
    """
    
    def __init__(self, name: str, model_params: Optional[Dict] = None):
        """
        Initialize base model.
        
        Args:
            name: Model name (e.g., 'RandomForest', 'XGBoost')
            model_params: Hyperparameters for the model
        """
        self.name = name
        self.model_params = model_params or {}
        self.model = None
        self.is_trained = False
        self.feature_names = None
        self.training_time = None
        self.metrics = {}
        
        logger.info(f"Initialized {self.name} model")
    
    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'BaseModel':
        """
        Train the model.
        
        Args:
            X: Training features
            y: Training target
            
        Returns:
            self (for method chaining)
        """
        pass
    
    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions.
        
        Args:
            X: Features for prediction
            
        Returns:
            Predictions array
        """
        pass
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """
        Evaluate model on given data.
        
        Args:
            X: Features
            y: True target values
            
        Returns:
            Dictionary of metrics
        """
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        
        if not self.is_trained:
            raise ValueError(f"{self.name} must be trained before evaluation")
        
        # Make predictions
        y_pred = self.predict(X)
        
        # Calculate metrics
        metrics = {
            'rmse': np.sqrt(mean_squared_error(y, y_pred)),
            'mae': mean_absolute_error(y, y_pred),
            'r2': r2_score(y, y_pred),
            'mape': np.mean(np.abs((y - y_pred) / (y + 1e-10))) * 100  # +epsilon to avoid division by zero
        }
        
        # AQI category accuracy (within same category)
        y_cat = (y / 1).astype(int).clip(1, 5)  # Convert to 1-5 scale
        y_pred_cat = (y_pred / 1).astype(int).clip(1, 5)
        metrics['category_accuracy'] = (y_cat == y_pred_cat).mean()
        
        # Within 1 AQI unit
        metrics['within_1_aqi'] = (np.abs(y - y_pred) <= 1).mean()
        
        logger.info(f"{self.name} - RMSE: {metrics['rmse']:.4f}, MAE: {metrics['mae']:.4f}, R²: {metrics['r2']:.4f}")
        
        return metrics
    
    def save(self, filepath: Path) -> None:
        """
        Save model to disk.
        
        Args:
            filepath: Where to save the model
        """
        if not self.is_trained:
            logger.warning(f"Saving untrained {self.name} model")
        
        # Prepare model data
        model_data = {
            'name': self.name,
            'model': self.model,
            'model_params': self.model_params,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained,
            'training_time': self.training_time,
            'metrics': self.metrics,
            'saved_at': datetime.now().isoformat()
        }
        
        # Save to disk
        filepath.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model_data, filepath)
        
        logger.info(f"Saved {self.name} model to {filepath}")
    
    @classmethod
    def load(cls, filepath: Path) -> 'BaseModel':
        """
        Load model from disk.
        
        Args:
            filepath: Model file location
            
        Returns:
            Loaded model instance
        """
        # Load model data
        model_data = joblib.load(filepath)
        
        # Create instance WITHOUT name parameter (models don't need it when loading)
        instance = cls(**model_data.get('model_params', {}))
        
        # Restore state
        instance.name = model_data['name']
        instance.model = model_data['model']
        instance.feature_names = model_data['feature_names']
        instance.is_trained = model_data['is_trained']
        instance.training_time = model_data['training_time']
        instance.metrics = model_data.get('metrics', {})
        
        logger.info(f"Loaded {instance.name} model from {filepath}")
        
        return instance
    
    def get_feature_importance(self) -> Optional[pd.Series]:
        """
        Get feature importance (if model supports it).
        
        Returns:
            Series with feature importances or None
        """
        if not self.is_trained:
            logger.warning("Model not trained yet")
            return None
        
        if hasattr(self.model, 'feature_importances_'):
            importances = pd.Series(
                self.model.feature_importances_,
                index=self.feature_names
            ).sort_values(ascending=False)
            return importances
        else:
            logger.info(f"{self.name} does not support feature importance")
            return None
    
    def __repr__(self) -> str:
        """String representation of model."""
        status = "trained" if self.is_trained else "untrained"
        return f"{self.name}(status={status}, params={len(self.model_params)})"


if __name__ == "__main__":
    """
    Test the base model class.
    
    Run: python src/models/base_model.py
    """
    print("=" * 80)
    print("BASE MODEL CLASS TEST")
    print("=" * 80)
    
    # This is an abstract class, so we can't instantiate it directly
    # But we can test the structure
    
    print("\n✅ BaseModel class defined successfully")
    print("\nKey methods:")
    print("  - fit(X, y) - Train the model")
    print("  - predict(X) - Make predictions")
    print("  - evaluate(X, y) - Calculate metrics")
    print("  - save(filepath) - Save to disk")
    print("  - load(filepath) - Load from disk")
    print("  - get_feature_importance() - Feature ranking")
    
    print("\n✅ Ready to create specific model implementations!")