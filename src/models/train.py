"""
Model Training Module

Handles model training workflow:
1. Load data
2. Train model
3. Evaluate on train/val sets
4. Save model and results

Works with ANY model that inherits from BaseModel.

Learning Notes:
- Separates training logic from model implementation
- Reusable across all models
- Proper train/val/test methodology
- Comprehensive logging and error handling
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger(__name__)
config = get_config()


class ModelTrainer:
    """
    Handles the complete training workflow for any model.
    
    Usage:
        trainer = ModelTrainer()
        model, results = trainer.train_model(
            model=my_model,
            model_name='RandomForest'
        )
    """
    
    def __init__(self, data_dir: Optional[Path] = None, use_feature_selection: bool = False):
        """
        Initialize trainer.
        
        Args:
            data_dir: Directory with train/val/test data
            use_feature_selection: Whether to use feature selection
        """
        self.data_dir = data_dir or (project_root / 'data' / 'processed')
        self.results_dir = project_root / 'data' / 'models'
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.use_feature_selection = use_feature_selection
        
        logger.info(f"ModelTrainer initialized")
        logger.info(f"Data directory: {self.data_dir}")
        logger.info(f"Results directory: {self.results_dir}")
        logger.info(f"Feature selection: {use_feature_selection}")
    
    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame,
                                   pd.Series, pd.Series, pd.Series]:
        """
        Load train/validation/test datasets.
        
        Returns:
            X_train, X_val, X_test, y_train, y_val, y_test
        """
        logger.info("Loading datasets...")
        
        try:
            # Load training data
            train_path = self.data_dir / 'train_data.csv'
            if not train_path.exists():
                raise FileNotFoundError(f"Training data not found: {train_path}")
            train_df = pd.read_csv(train_path)
            logger.info(f"✓ Loaded training data: {len(train_df)} records")
            
            # Load validation data
            val_path = self.data_dir / 'val_data.csv'
            if not val_path.exists():
                raise FileNotFoundError(f"Validation data not found: {val_path}")
            val_df = pd.read_csv(val_path)
            logger.info(f"✓ Loaded validation data: {len(val_df)} records")
            
            # Load test data
            test_path = self.data_dir / 'test_data.csv'
            if not test_path.exists():
                raise FileNotFoundError(f"Test data not found: {test_path}")
            test_df = pd.read_csv(test_path)
            logger.info(f"✓ Loaded test data: {len(test_df)} records")
            
            # Separate features and target
            target_col = 'aqi_next_24h'
            
            if target_col not in train_df.columns:
                raise ValueError(f"Target column '{target_col}' not found in data")
            
            # Features (everything except target and metadata)
            exclude_cols = [target_col, 'timestamp', 'city_name', 'country']
            feature_cols = [col for col in train_df.columns 
                          if col not in exclude_cols]
            
            X_train = train_df[feature_cols]
            y_train = train_df[target_col]
            
            X_val = val_df[feature_cols]
            y_val = val_df[target_col]
            
            X_test = test_df[feature_cols]
            y_test = test_df[target_col]
            
            logger.info(f"Features: {len(feature_cols)} columns")
            logger.info(f"Target: {target_col}")
            
            return X_train, X_val, X_test, y_train, y_val, y_test
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise
    
    def train_model(self, 
                   model: Any,
                   model_name: str,
                   save_model: bool = True) -> Tuple[Any, Dict[str, Any]]:
        """
        Train a model and evaluate it.
        
        Args:
            model: Model instance (must inherit from BaseModel)
            model_name: Name for saving results
            save_model: Whether to save the trained model
        
        Returns:
            (trained_model, results_dict)
        """
        logger.info("=" * 80)
        logger.info(f"TRAINING: {model_name}")
        logger.info("=" * 80)
        
        try:
            # Load data
            X_train, X_val, X_test, y_train, y_val, y_test = self.load_data()
            
            # Train model
            logger.info(f"\nTraining {model_name}...")
            start_time = datetime.now()
            
            model.fit(X_train, y_train)
            
            training_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✓ Training completed in {training_time:.2f} seconds")
            
            # Evaluate on train set
            logger.info("\nEvaluating on training set...")
            train_metrics = model.evaluate(X_train, y_train)
            
            # Evaluate on validation set
            logger.info("Evaluating on validation set...")
            val_metrics = model.evaluate(X_val, y_val)
            
            # Evaluate on test set
            logger.info("Evaluating on test set...")
            test_metrics = model.evaluate(X_test, y_test)
            
            # Compile results
            results = {
                'model_name': model_name,
                'training_time': training_time,
                'timestamp': datetime.now().isoformat(),
                'data_info': {
                    'n_train': len(X_train),
                    'n_val': len(X_val),
                    'n_test': len(X_test),
                    'n_features': len(X_train.columns)
                },
                'metrics': {
                    'train': train_metrics,
                    'validation': val_metrics,
                    'test': test_metrics
                }
            }
            
            # Get feature importance if available
            feature_importance = model.get_feature_importance()
            if feature_importance is not None:
                results['feature_importance'] = feature_importance.head(20).to_dict()
            
            # Log summary
            self._log_results_summary(results)
            
            # Save model
            if save_model:
                model_path = self.results_dir / f"{model_name.lower().replace(' ', '_')}.joblib"
                model.save(model_path)
                results['model_path'] = str(model_path)
            
            # Save results
            results_path = self.results_dir / f"{model_name.lower().replace(' ', '_')}_results.json"
            with open(results_path, 'w') as f:
                # Convert numpy types to native Python for JSON serialization
                results_json = self._convert_to_json_serializable(results)
                json.dump(results_json, f, indent=2)
            
            logger.info(f"\n✓ Results saved to: {results_path}")
            
            return model, results
            
        except Exception as e:
            logger.error(f"Error during training: {str(e)}")
            raise
    
    def _log_results_summary(self, results: Dict[str, Any]) -> None:
        """Log a summary of training results."""
        logger.info("\n" + "=" * 80)
        logger.info("RESULTS SUMMARY")
        logger.info("=" * 80)
        
        # Training info
        logger.info(f"\nModel: {results['model_name']}")
        logger.info(f"Training time: {results['training_time']:.2f}s")
        logger.info(f"Features: {results['data_info']['n_features']}")
        
        # Metrics comparison
        logger.info("\nPerformance Metrics:")
        logger.info("-" * 80)
        logger.info(f"{'Metric':<20} {'Train':<15} {'Validation':<15} {'Test':<15}")
        logger.info("-" * 80)
        
        train_metrics = results['metrics']['train']
        val_metrics = results['metrics']['validation']
        test_metrics = results['metrics']['test']
        
        for metric in ['rmse', 'mae', 'r2', 'within_1_aqi']:
            logger.info(f"{metric.upper():<20} "
                       f"{train_metrics[metric]:<15.4f} "
                       f"{val_metrics[metric]:<15.4f} "
                       f"{test_metrics[metric]:<15.4f}")
        
        # Overfitting check
        val_rmse = val_metrics['rmse']
        train_rmse = train_metrics['rmse']
        overfitting = ((val_rmse - train_rmse) / train_rmse) * 100
        
        logger.info("\nOverfitting Analysis:")
        logger.info(f"  Train RMSE: {train_rmse:.4f}")
        logger.info(f"  Val RMSE: {val_rmse:.4f}")
        logger.info(f"  Difference: {overfitting:.2f}%")
        
        if overfitting > 20:
            logger.warning("⚠ Possible overfitting detected (>20% difference)")
        elif overfitting < 5:
            logger.info("✓ Good generalization (< 5% difference)")
        else:
            logger.info("✓ Acceptable generalization")
        
        logger.info("=" * 80)
    
    def _convert_to_json_serializable(self, obj: Any) -> Any:
        """Convert numpy/pandas types to JSON-serializable types."""
        if isinstance(obj, dict):
            return {key: self._convert_to_json_serializable(value) 
                   for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_json_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
        else:
            return obj


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def train_baseline_models() -> Dict[str, Any]:
    """
    Train all baseline models.
    
    Returns:
        Dictionary with all results
    """
    from src.models.baseline_models import (
        PersistenceModel,
        MovingAverageModel,
        LinearRegressionModel
    )
    
    trainer = ModelTrainer()
    all_results = {}
    
    # Train persistence model
    logger.info("\n\n" + "="*80)
    logger.info("BASELINE MODELS TRAINING")
    logger.info("="*80)
    
    models_to_train = [
        (PersistenceModel(), "Persistence"),
        (MovingAverageModel(window=3), "MovingAverage-3"),
        (MovingAverageModel(window=7), "MovingAverage-7"),
        (LinearRegressionModel(), "LinearRegression")
    ]
    
    for model, name in models_to_train:
        try:
            _, results = trainer.train_model(model, name)
            all_results[name] = results
        except Exception as e:
            logger.error(f"Failed to train {name}: {str(e)}")
    
    # Save combined results
    combined_path = trainer.results_dir / 'baseline_models_comparison.json'
    with open(combined_path, 'w') as f:
        json.dump(trainer._convert_to_json_serializable(all_results), f, indent=2)
    
    logger.info(f"\n✓ All baseline results saved to: {combined_path}")
    
    return all_results


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Test the training module.
    
    Run: python src/models/train.py
    """
    print("=" * 80)
    print("MODEL TRAINING MODULE TEST")
    print("=" * 80)
    
    # Check if data exists
    data_dir = project_root / 'data' / 'processed'
    
    required_files = ['train_data.csv', 'val_data.csv', 'test_data.csv']
    missing_files = [f for f in required_files 
                    if not (data_dir / f).exists()]
    
    if missing_files:
        print("\n⚠ Missing data files:")
        for f in missing_files:
            print(f"  - {f}")
        print("\nPlease run Phase 2 notebook (04_statistical_analysis.ipynb)")
        print("to generate train/val/test datasets.")
    else:
        print("\n✓ All required data files found")
        print("\nTesting with baseline models...")
        
        # Train all baseline models
        results = train_baseline_models()
        
        print("\n" + "=" * 80)
        print("TRAINING COMPLETE")
        print("=" * 80)
        print(f"\nTrained {len(results)} models successfully!")
        print("\nResults saved in: data/models/")