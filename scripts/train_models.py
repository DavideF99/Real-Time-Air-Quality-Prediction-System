#!/usr/bin/env python3
"""
Train Models - Command Line Interface

Production-ready script for training air quality prediction models.

Usage:
    # Train all baseline models
    python scripts/train_models.py --model all-baselines
    
    # Train specific model
    python scripts/train_models.py --model persistence
    python scripts/train_models.py --model linear
    
    # Train and compare
    python scripts/train_models.py --model all-baselines --compare
    
    # Future: Train tree-based models
    python scripts/train_models.py --model random-forest
    python scripts/train_models.py --model xgboost

Learning Notes:
- CLI makes it easy to run from terminal/scripts
- Argparse provides clean command-line interface
- Can be scheduled/automated
- Production-ready error handling
"""

import sys
from pathlib import Path
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger
from src.models.train import ModelTrainer, train_baseline_models
from src.models.evaluate import ModelEvaluator

logger = get_logger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Train air quality prediction models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train all baseline models
  python scripts/train_models.py --model all-baselines
  
  # Train specific baseline
  python scripts/train_models.py --model persistence
  python scripts/train_models.py --model moving-average
  python scripts/train_models.py --model linear
  
  # Train and compare
  python scripts/train_models.py --model all-baselines --compare
  
  # Future: Train advanced models
  python scripts/train_models.py --model random-forest
  python scripts/train_models.py --model xgboost
  python scripts/train_models.py --model lightgbm
        """
    )
    
    parser.add_argument(
        '--model',
        type=str,
        required=True,
        choices=[
            'all-baselines',
            'persistence',
            'moving-average',
            'linear',
            'random-forest',  # Future
            'xgboost',        # Future
            'lightgbm'        # Future
        ],
        help='Which model(s) to train'
    )
    
    parser.add_argument(
        '--compare',
        action='store_true',
        help='Generate model comparison after training'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save trained models (for testing)'
    )
    
    parser.add_argument(
        '--visualize',
        action='store_true',
        help='Generate visualization plots'
    )
    
    parser.add_argument(
        '--feature-selection',
        action='store_true',
        help='Use feature selection (top 25 from correlation + MI)'
    )
    
    return parser.parse_args()

def train_tree_model(model_type: str, save: bool = True):
    """
    Train a tree-based model.
    
    Args:
        model_type: Type of model to train
        save: Whether to save the model
    """
    trainer = ModelTrainer()
    
    # Import models
    if model_type == 'random-forest':
        from src.models.random_forest_model import RandomForestModel
        model = RandomForestModel(n_estimators=100, max_depth=15, random_state=42)
        name = 'RandomForest'
    
    elif model_type == 'xgboost':
        try:
            from src.models.xgboost_model import XGBoostModel
            model = XGBoostModel(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
            name = 'XGBoost'
        except ImportError:
            logger.error("XGBoost not installed. Run: pip install xgboost")
            return None, None
    
    elif model_type == 'lightgbm':
        try:
            from src.models.lightgbm_model import LightGBMModel
            model = LightGBMModel(n_estimators=100, num_leaves=31, learning_rate=0.1, random_state=42)
            name = 'LightGBM'
        except ImportError:
            logger.error("LightGBM not installed. Run: pip install lightgbm")
            return None, None
    
    else:
        logger.error(f"Unknown tree model type: {model_type}")
        return None, None
    
    logger.info(f"\nTraining {name}...")
    trained_model, results = trainer.train_model(model, name, save_model=save)
    
    return trained_model, results

def train_single_baseline(model_type: str, save: bool = True):
    """
    Train a single baseline model.
    
    Args:
        model_type: Type of model to train
        save: Whether to save the model
    """
    from src.models.baseline_models import (
        PersistenceModel,
        MovingAverageModel,
        LinearRegressionModel
    )
    
    trainer = ModelTrainer()
    
    # Map model type to class and name
    model_map = {
        'persistence': (PersistenceModel(), 'Persistence'),
        'moving-average': (MovingAverageModel(window=3), 'MovingAverage-3'),
        'linear': (LinearRegressionModel(), 'LinearRegression')
    }
    
    if model_type not in model_map:
        logger.error(f"Unknown baseline model type: {model_type}")
        return None
    
    model, name = model_map[model_type]
    
    logger.info(f"\nTraining {name}...")
    trained_model, results = trainer.train_model(model, name, save_model=save)
    
    return trained_model, results


def main():
    """Main execution function."""
    args = parse_arguments()
    
    logger.info("=" * 80)
    logger.info("AIR QUALITY MODEL TRAINING")
    logger.info("=" * 80)
    logger.info(f"Model: {args.model}")
    logger.info(f"Compare: {args.compare}")
    logger.info(f"Save models: {not args.no_save}")
    logger.info("=" * 80)
    
    save_models = not args.no_save
    
    try:
        # Check if data files exist
        data_dir = project_root / 'data' / 'processed'
        required_files = ['train_data.csv', 'val_data.csv', 'test_data.csv']
        missing_files = [f for f in required_files 
                        if not (data_dir / f).exists()]
        
        if missing_files:
            logger.error("Missing required data files:")
            for f in missing_files:
                logger.error(f"  - {f}")
            logger.error("\nPlease run Phase 2 notebook (04_statistical_analysis.ipynb)")
            logger.error("to generate train/val/test datasets.")
            return
        
        # Train models
        if args.model == 'all-baselines':
            logger.info("\nTraining all baseline models...")
            results = train_baseline_models()
            models_trained = list(results.keys())
        
        elif args.model in ['persistence', 'moving-average', 'linear']:
            logger.info(f"\nTraining {args.model} model...")
            model, results = train_single_baseline(args.model, save=save_models)
            if model:
                models_trained = [results['model_name']]
            else:
                logger.error("Training failed")
                return
        
        elif args.model == 'random-forest':
            logger.info("\nTraining Random Forest model...")
            model, results = train_tree_model('random-forest', save=save_models)
            if model:
                models_trained = [results['model_name']]
            else:
                logger.error("Training failed")
                return
        
        elif args.model == 'xgboost':
            logger.info("\nTraining XGBoost model...")
            model, results = train_tree_model('xgboost', save=save_models)
            if model:
                models_trained = [results['model_name']]
            else:
                logger.error("Training failed")
                return
        
        elif args.model == 'lightgbm':
            logger.info("\nTraining LightGBM model...")
            model, results = train_tree_model('lightgbm', save=save_models)
            if model:
                models_trained = [results['model_name']]
            else:
                logger.error("Training failed")
                return
        
        else:
            logger.error(f"Unknown model: {args.model}")
            return
        
        logger.info("\n" + "=" * 80)
        logger.info("TRAINING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Trained {len(models_trained)} model(s):")
        for name in models_trained:
            logger.info(f"  ✓ {name}")
        
        # Compare models if requested
        if args.compare and len(models_trained) > 1:
            logger.info("\n" + "=" * 80)
            logger.info("GENERATING MODEL COMPARISON")
            logger.info("=" * 80)
            
            evaluator = ModelEvaluator()
            df_comparison = evaluator.compare_models(
                models_trained,
                save=True
            )
            
            # Show best model
            if not df_comparison.empty:
                best_model = df_comparison.iloc[0]['Model']
                best_rmse = df_comparison.iloc[0]['Val RMSE']
                
                logger.info("\n" + "=" * 80)
                logger.info("BEST MODEL")
                logger.info("=" * 80)
                logger.info(f"Model: {best_model}")
                logger.info(f"Validation RMSE: {best_rmse:.4f}")
                logger.info("=" * 80)
        
        # Generate visualizations if requested
        if args.visualize:
            logger.info("\n" + "=" * 80)
            logger.info("GENERATING VISUALIZATIONS")
            logger.info("=" * 80)
            
            evaluator = ModelEvaluator()
            
            # Load test data for visualization
            from src.models.train import ModelTrainer
            trainer = ModelTrainer()
            _, _, X_test, _, _, y_test = trainer.load_data()
            
            for model_name in models_trained:
                logger.info(f"\nGenerating plots for {model_name}...")
                
                try:
                    # Load model
                    from src.models.base_model import BaseModel
                    model_path = project_root / 'data' / 'models' / f"{model_name.lower().replace(' ', '_')}.joblib"
                    
                    if model_path.exists():
                        # Get predictions
                        if model_name == 'Persistence':
                            from src.models.baseline_models import PersistenceModel
                            model = PersistenceModel.load(model_path)
                        elif 'MovingAverage' in model_name:
                            from src.models.baseline_models import MovingAverageModel
                            model = MovingAverageModel.load(model_path)
                        elif model_name == 'LinearRegression':
                            from src.models.baseline_models import LinearRegressionModel
                            model = LinearRegressionModel.load(model_path)
                        
                        y_pred = model.predict(X_test)
                        
                        # Generate plots
                        evaluator.plot_predictions(y_test.values, y_pred, model_name)
                        evaluator.plot_error_distribution(y_test.values, y_pred, model_name)
                        
                        # Feature importance if available
                        if hasattr(model, 'get_feature_importance'):
                            evaluator.plot_feature_importance(model_name)
                    
                except Exception as e:
                    logger.warning(f"Could not generate plots for {model_name}: {str(e)}")
        
        logger.info("\n" + "=" * 80)
        logger.info("ALL DONE! 🎉")
        logger.info("=" * 80)
        logger.info("\nNext steps:")
        logger.info("  1. Review results in: data/models/")
        logger.info("  2. Check visualizations in: visualizations/models/")
        logger.info("  3. Compare model performance")
        logger.info("  4. Select best model for deployment")
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()