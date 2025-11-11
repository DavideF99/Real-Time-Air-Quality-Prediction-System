"""
Model Predictor

Handles loading trained models and making predictions.

Learning Notes:
- Lazy loading: Models loaded only when needed
- Singleton pattern: One instance per model
- Feature engineering: Applied same as training
- Caching: Avoid reloading models
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ModelPredictor:
    """
    Loads and manages ML models for predictions.
    
    Features:
    - Lazy loading (load on first use)
    - Model caching (avoid reloading)
    - Feature engineering
    - Confidence intervals
    
    Usage:
        predictor = ModelPredictor()
        prediction, confidence = predictor.predict(
            city='bangkok',
            pollutants={'aqi': 2.5, 'pm2_5': 25.0, ...},
            model_name='xgboost'
        )
    """
    
    def __init__(self, models_dir: Optional[Path] = None):
        """
        Initialize predictor.
        
        Args:
            models_dir: Directory with trained models
        """
        self.models_dir = models_dir or (project_root / 'data' / 'models')
        self.loaded_models = {}  # Cache for loaded models
        self.model_metadata = {}  # Model info
        
        logger.info("ModelPredictor initialized")
        logger.info(f"Models directory: {self.models_dir}")
        
        # Load available models
        self._discover_models()
    
    def _discover_models(self):
        """Discover available model files."""
        model_files = list(self.models_dir.glob('*.joblib'))
        
        self.available_models = [
            f.stem for f in model_files 
            if f.stem not in ['persistence', 'movingaverage-3', 'movingaverage-7']
        ]
        
        logger.info(f"Found {len(self.available_models)} models: {self.available_models}")
    
    def load_model(self, model_name: str):
        """
        Load a specific model.
        
        Args:
            model_name: Name of model to load
        
        Returns:
            Loaded model instance
        """
        # Check cache first
        if model_name in self.loaded_models:
            logger.debug(f"Using cached {model_name} model")
            return self.loaded_models[model_name]
        
        # Load model
        model_path = self.models_dir / f"{model_name}.joblib"
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        logger.info(f"Loading {model_name} model...")
        
        # Import appropriate model class
        if model_name == 'xgboost':
            from src.models.xgboost_model import XGBoostModel
            model = XGBoostModel.load(model_path)
        elif model_name == 'lightgbm':
            from src.models.lightgbm_model import LightGBMModel
            model = LightGBMModel.load(model_path)
        elif model_name == 'randomforest':
            from src.models.random_forest_model import RandomForestModel
            model = RandomForestModel.load(model_path)
        elif model_name == 'linearregression':
            from src.models.baseline_models import LinearRegressionModel
            model = LinearRegressionModel.load(model_path)
        else:
            raise ValueError(f"Unknown model: {model_name}")
        
        # Cache model
        self.loaded_models[model_name] = model
        
        # Load metadata
        results_path = self.models_dir / f"{model_name}_results.json"
        if results_path.exists():
            import json
            with open(results_path) as f:
                self.model_metadata[model_name] = json.load(f)
        
        logger.info(f"✓ Loaded {model_name} model")
        
        return model
    
    def engineer_features(self, 
                         city: str,
                         pollutants: Dict[str, float]) -> pd.DataFrame:
        """
        Engineer features from raw pollutant values.
        
        For API predictions, we create simplified features.
        In production, you'd have historical data for lags/rolling stats.
        
        Args:
            city: City name
            pollutants: Dictionary of pollutant values
        
        Returns:
            DataFrame with engineered features
        """
        # Start with raw values
        features = pollutants.copy()
        
        # Add city encoding
        city_encoding = {
            'bangkok': 0,
            'durban': 1,
            'sao_paulo': 2,
            'sydney': 3,
            'london': 4,
            'new_york': 5
        }
        features['city_key'] = city_encoding.get(city, 0)
        
        # Add time features (current time)
        now = datetime.now()
        features['hour_sin'] = np.sin(2 * np.pi * now.hour / 24)
        features['hour_cos'] = np.cos(2 * np.pi * now.hour / 24)
        features['day_sin'] = np.sin(2 * np.pi * now.weekday() / 7)
        features['day_cos'] = np.cos(2 * np.pi * now.weekday() / 7)
        features['is_weekend'] = 1 if now.weekday() >= 5 else 0
        features['is_rush_hour'] = 1 if now.hour in [7, 8, 9, 17, 18, 19] else 0
        
        # Simplified features (assume recent history similar to current)
        # In production, you'd query database for actual historical data
        
        # Lag features (approximate as current values)
        for pollutant in ['aqi', 'pm2_5', 'pm10', 'no2', 'o3']:
            if pollutant in features:
                features[f'{pollutant}_lag_1h'] = features[pollutant]
                features[f'{pollutant}_lag_3h'] = features[pollutant]
        
        # Rolling statistics (approximate)
        for pollutant in ['aqi', 'pm2_5', 'pm10', 'no2', 'o3']:
            if pollutant in features:
                # Assume slight variation from current
                base_val = features[pollutant]
                features[f'{pollutant}_rolling_mean_24h'] = base_val * 0.98
                features[f'{pollutant}_rolling_mean_12h'] = base_val * 0.99
                features[f'{pollutant}_rolling_mean_6h'] = base_val
                features[f'{pollutant}_rolling_mean_3h'] = base_val * 1.01
                
                features[f'{pollutant}_rolling_min_24h'] = base_val * 0.85
                features[f'{pollutant}_rolling_min_12h'] = base_val * 0.90
                
                features[f'{pollutant}_rolling_max_24h'] = base_val * 1.15
                features[f'{pollutant}_rolling_max_12h'] = base_val * 1.10
        
        # Interaction features
        if 'pm2_5' in features and 'pm10' in features:
            features['pm_total'] = features['pm2_5'] + features['pm10']
            features['pm_ratio'] = features['pm2_5'] / (features['pm10'] + 1e-6)
        
        if 'pm2_5' in features and 'no2' in features:
            features['pollution_score'] = (
                0.5 * features['pm2_5'] + 
                0.3 * features.get('pm10', 0) + 
                0.2 * features['no2']
            ) / 100
        
        # Convert to DataFrame
        df = pd.DataFrame([features])
        
        return df
    
    def predict(self,
                city: str,
                pollutants: Dict[str, float],
                model_name: str = 'xgboost') -> Tuple[float, Dict[str, float]]:
        """
        Make AQI prediction.
        
        Args:
            city: City name
            pollutants: Dictionary of pollutant values
            model_name: Model to use
        
        Returns:
            (prediction, confidence_interval)
        """
        logger.info(f"Making prediction for {city} using {model_name}")
        
        # Load model
        model = self.load_model(model_name)
        
        # Engineer features
        X = self.engineer_features(city, pollutants)
        
        # Select features that model was trained on
        model_features = model.feature_names
        
        # Get available features
        available_features = [f for f in model_features if f in X.columns]
        
        # Add missing features as zeros
        for feature in model_features:
            if feature not in X.columns:
                X[feature] = 0.0
        
        # Select in correct order
        X = X[model_features]
        
        # Make prediction
        prediction = model.predict(X)[0]
        
        # Clip to valid AQI range
        prediction = np.clip(prediction, 1.0, 5.0)
        
        # Calculate confidence interval (approximate)
        # In production, use model's uncertainty estimation
        if model_name in self.model_metadata:
            val_rmse = self.model_metadata[model_name]['metrics']['validation']['rmse']
        else:
            val_rmse = 0.4  # Default estimate
        
        confidence_interval = {
            'lower': max(1.0, prediction - val_rmse),
            'upper': min(5.0, prediction + val_rmse)
        }
        
        logger.info(f"✓ Prediction: {prediction:.2f} [{confidence_interval['lower']:.2f}, {confidence_interval['upper']:.2f}]")
        
        return prediction, confidence_interval
    
    def get_model_info(self, model_name: str) -> Dict:
        """
        Get information about a model.
        
        Args:
            model_name: Model name
        
        Returns:
            Model metadata dictionary
        """
        if model_name not in self.model_metadata:
            # Try to load
            self.load_model(model_name)
        
        return self.model_metadata.get(model_name, {})
    
    def list_models(self) -> list:
        """
        List available models.
        
        Returns:
            List of model names
        """
        return self.available_models


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test the predictor."""
    
    print("=" * 80)
    print("MODEL PREDICTOR TEST")
    print("=" * 80)
    
    # Initialize predictor
    predictor = ModelPredictor()
    
    print(f"\nAvailable models: {predictor.list_models()}")
    
    # Test prediction
    print("\n" + "=" * 80)
    print("TEST PREDICTION")
    print("=" * 80)
    
    # Sample input
    test_pollutants = {
        'aqi': 2.5,
        'pm2_5': 25.0,
        'pm10': 45.0,
        'no2': 15.0,
        'o3': 85.0,
        'co': 250.0,
        'so2': 5.0,
        'nh3': 2.0
    }
    
    print(f"\nInput:")
    print(f"  City: Bangkok")
    for key, value in test_pollutants.items():
        print(f"  {key}: {value}")
    
    # Try each available model
    for model_name in predictor.list_models():
        try:
            print(f"\nTrying {model_name}...")
            prediction, confidence = predictor.predict(
                city='bangkok',
                pollutants=test_pollutants,
                model_name=model_name
            )
            
            print(f"✓ {model_name} prediction: {prediction:.2f}")
            print(f"  Confidence interval: [{confidence['lower']:.2f}, {confidence['upper']:.2f}]")
            
        except Exception as e:
            print(f"✗ {model_name} failed: {str(e)}")
    
    print("\n" + "=" * 80)
    print("✓ Predictor test complete!")
    print("=" * 80)