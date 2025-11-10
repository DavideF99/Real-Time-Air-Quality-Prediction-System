"""
Model Evaluation Module

Utilities for evaluating and comparing models:
1. Load trained models
2. Generate predictions
3. Create visualizations
4. Compare multiple models

Learning Notes:
- Comprehensive evaluation beyond simple metrics
- Visual analysis reveals model behavior
- Error analysis shows where models struggle
- Comparison helps select best model
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Set plotting style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class ModelEvaluator:
    """
    Handles model evaluation and comparison.
    
    Usage:
        evaluator = ModelEvaluator()
        evaluator.plot_predictions(model, X_test, y_test)
        evaluator.compare_models(['RandomForest', 'XGBoost'])
    """
    
    def __init__(self, models_dir: Optional[Path] = None):
        """
        Initialize evaluator.
        
        Args:
            models_dir: Directory with saved models
        """
        self.models_dir = models_dir or (project_root / 'data' / 'models')
        self.viz_dir = project_root / 'visualizations' / 'models'
        self.viz_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ModelEvaluator initialized")
        logger.info(f"Models directory: {self.models_dir}")
        logger.info(f"Visualizations directory: {self.viz_dir}")
    
    def load_results(self, model_name: str) -> Dict[str, Any]:
        """
        Load results for a specific model.
        
        Args:
            model_name: Name of the model
        
        Returns:
            Results dictionary
        """
        results_file = self.models_dir / f"{model_name.lower().replace(' ', '_')}_results.json"
        
        if not results_file.exists():
            raise FileNotFoundError(f"Results not found: {results_file}")
        
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        logger.info(f"Loaded results for {model_name}")
        return results
    
    def plot_predictions(self, 
                        y_true: np.ndarray,
                        y_pred: np.ndarray,
                        model_name: str,
                        save: bool = True) -> None:
        """
        Plot actual vs predicted values.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            model_name: Model name for title
            save: Whether to save the plot
        """
        fig, axes = plt.subplots(1, 2, figsize=(15, 5))
        
        # Scatter plot: predicted vs actual
        axes[0].scatter(y_true, y_pred, alpha=0.6, edgecolors='k', linewidth=0.5)
        
        # Perfect prediction line
        min_val = min(y_true.min(), y_pred.min())
        max_val = max(y_true.max(), y_pred.max())
        axes[0].plot([min_val, max_val], [min_val, max_val], 
                    'r--', lw=2, label='Perfect Prediction')
        
        axes[0].set_xlabel('Actual AQI', fontsize=12)
        axes[0].set_ylabel('Predicted AQI', fontsize=12)
        axes[0].set_title(f'{model_name}: Predictions vs Actual', fontsize=14)
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Residual plot
        residuals = y_true - y_pred
        axes[1].scatter(y_pred, residuals, alpha=0.6, edgecolors='k', linewidth=0.5)
        axes[1].axhline(y=0, color='r', linestyle='--', lw=2)
        axes[1].set_xlabel('Predicted AQI', fontsize=12)
        axes[1].set_ylabel('Residuals (Actual - Predicted)', fontsize=12)
        axes[1].set_title(f'{model_name}: Residual Analysis', fontsize=14)
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            save_path = self.viz_dir / f"{model_name.lower().replace(' ', '_')}_predictions.png"
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved prediction plot: {save_path}")
        
        plt.show()
    
    def plot_error_distribution(self,
                               y_true: np.ndarray,
                               y_pred: np.ndarray,
                               model_name: str,
                               save: bool = True) -> None:
        """
        Plot error distribution analysis.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            model_name: Model name
            save: Whether to save plot
        """
        errors = y_true - y_pred
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. Error histogram
        axes[0, 0].hist(errors, bins=30, edgecolor='black', alpha=0.7)
        axes[0, 0].axvline(x=0, color='r', linestyle='--', lw=2)
        axes[0, 0].set_xlabel('Error (Actual - Predicted)', fontsize=11)
        axes[0, 0].set_ylabel('Frequency', fontsize=11)
        axes[0, 0].set_title('Error Distribution', fontsize=12)
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Absolute error distribution
        abs_errors = np.abs(errors)
        axes[0, 1].hist(abs_errors, bins=30, edgecolor='black', alpha=0.7, color='orange')
        axes[0, 1].set_xlabel('Absolute Error', fontsize=11)
        axes[0, 1].set_ylabel('Frequency', fontsize=11)
        axes[0, 1].set_title('Absolute Error Distribution', fontsize=12)
        axes[0, 1].grid(True, alpha=0.3)
        
        # Add mean absolute error line
        mae = abs_errors.mean()
        axes[0, 1].axvline(x=mae, color='r', linestyle='--', lw=2, 
                          label=f'MAE = {mae:.3f}')
        axes[0, 1].legend()
        
        # 3. Q-Q plot (check if errors are normally distributed)
        from scipy import stats
        stats.probplot(errors, dist="norm", plot=axes[1, 0])
        axes[1, 0].set_title('Q-Q Plot (Normality Check)', fontsize=12)
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Error by actual value
        axes[1, 1].scatter(y_true, abs_errors, alpha=0.6, edgecolors='k', linewidth=0.5)
        axes[1, 1].set_xlabel('Actual AQI', fontsize=11)
        axes[1, 1].set_ylabel('Absolute Error', fontsize=11)
        axes[1, 1].set_title('Error vs Actual Value', fontsize=12)
        axes[1, 1].grid(True, alpha=0.3)
        
        # Add trend line
        z = np.polyfit(y_true, abs_errors, 1)
        p = np.poly1d(z)
        axes[1, 1].plot(y_true, p(y_true), "r--", lw=2, label='Trend')
        axes[1, 1].legend()
        
        plt.suptitle(f'{model_name}: Error Analysis', fontsize=16, y=1.00)
        plt.tight_layout()
        
        if save:
            save_path = self.viz_dir / f"{model_name.lower().replace(' ', '_')}_errors.png"
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved error analysis: {save_path}")
        
        plt.show()
    
    def compare_models(self, 
                      model_names: List[str],
                      metric: str = 'rmse',
                      save: bool = True) -> pd.DataFrame:
        """
        Compare multiple models.
        
        Args:
            model_names: List of model names to compare
            metric: Which metric to focus on
            save: Whether to save comparison plot
        
        Returns:
            DataFrame with comparison results
        """
        logger.info(f"Comparing {len(model_names)} models...")
        
        # Collect results
        comparison_data = []
        
        for name in model_names:
            try:
                results = self.load_results(name)
                
                comparison_data.append({
                    'Model': name,
                    'Train RMSE': results['metrics']['train']['rmse'],
                    'Val RMSE': results['metrics']['validation']['rmse'],
                    'Test RMSE': results['metrics']['test']['rmse'],
                    'Train MAE': results['metrics']['train']['mae'],
                    'Val MAE': results['metrics']['validation']['mae'],
                    'Test MAE': results['metrics']['test']['mae'],
                    'Train R²': results['metrics']['train']['r2'],
                    'Val R²': results['metrics']['validation']['r2'],
                    'Test R²': results['metrics']['test']['r2'],
                    'Training Time (s)': results['training_time']
                })
            except FileNotFoundError:
                logger.warning(f"Results not found for {name}, skipping")
        
        if not comparison_data:
            logger.error("No results found for comparison")
            return pd.DataFrame()
        
        df_comparison = pd.DataFrame(comparison_data)
        
        # Sort by validation RMSE (lower is better)
        df_comparison = df_comparison.sort_values('Val RMSE')
        
        # Log results
        logger.info("\n" + "=" * 100)
        logger.info("MODEL COMPARISON")
        logger.info("=" * 100)
        print(df_comparison.to_string(index=False))
        logger.info("=" * 100)
        
        # Create comparison plot
        self._plot_model_comparison(df_comparison, save=save)
        
        # Save comparison table
        comparison_path = self.models_dir / 'model_comparison.csv'
        df_comparison.to_csv(comparison_path, index=False)
        logger.info(f"\n✓ Comparison saved to: {comparison_path}")
        
        return df_comparison
    
    def _plot_model_comparison(self, 
                              df_comparison: pd.DataFrame,
                              save: bool = True) -> None:
        """Create comparison visualization."""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        models = df_comparison['Model']
        x = np.arange(len(models))
        width = 0.25
        
        # 1. RMSE comparison
        axes[0, 0].bar(x - width, df_comparison['Train RMSE'], width, 
                      label='Train', alpha=0.8)
        axes[0, 0].bar(x, df_comparison['Val RMSE'], width, 
                      label='Validation', alpha=0.8)
        axes[0, 0].bar(x + width, df_comparison['Test RMSE'], width, 
                      label='Test', alpha=0.8)
        axes[0, 0].set_xlabel('Model', fontsize=11)
        axes[0, 0].set_ylabel('RMSE', fontsize=11)
        axes[0, 0].set_title('RMSE Comparison (Lower is Better)', fontsize=12)
        axes[0, 0].set_xticks(x)
        axes[0, 0].set_xticklabels(models, rotation=45, ha='right')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3, axis='y')
        
        # 2. MAE comparison
        axes[0, 1].bar(x - width, df_comparison['Train MAE'], width, 
                      label='Train', alpha=0.8)
        axes[0, 1].bar(x, df_comparison['Val MAE'], width, 
                      label='Validation', alpha=0.8)
        axes[0, 1].bar(x + width, df_comparison['Test MAE'], width, 
                      label='Test', alpha=0.8)
        axes[0, 1].set_xlabel('Model', fontsize=11)
        axes[0, 1].set_ylabel('MAE', fontsize=11)
        axes[0, 1].set_title('MAE Comparison (Lower is Better)', fontsize=12)
        axes[0, 1].set_xticks(x)
        axes[0, 1].set_xticklabels(models, rotation=45, ha='right')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3, axis='y')
        
        # 3. R² comparison
        axes[1, 0].bar(x - width, df_comparison['Train R²'], width, 
                      label='Train', alpha=0.8)
        axes[1, 0].bar(x, df_comparison['Val R²'], width, 
                      label='Validation', alpha=0.8)
        axes[1, 0].bar(x + width, df_comparison['Test R²'], width, 
                      label='Test', alpha=0.8)
        axes[1, 0].set_xlabel('Model', fontsize=11)
        axes[1, 0].set_ylabel('R² Score', fontsize=11)
        axes[1, 0].set_title('R² Comparison (Higher is Better)', fontsize=12)
        axes[1, 0].set_xticks(x)
        axes[1, 0].set_xticklabels(models, rotation=45, ha='right')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3, axis='y')
        
        # 4. Training time
        axes[1, 1].bar(models, df_comparison['Training Time (s)'], alpha=0.8, color='teal')
        axes[1, 1].set_xlabel('Model', fontsize=11)
        axes[1, 1].set_ylabel('Training Time (seconds)', fontsize=11)
        axes[1, 1].set_title('Training Time Comparison', fontsize=12)
        axes[1, 1].set_xticklabels(models, rotation=45, ha='right')
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        plt.suptitle('Model Performance Comparison', fontsize=16, y=0.995)
        plt.tight_layout()
        
        if save:
            save_path = self.viz_dir / 'model_comparison.png'
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved comparison plot: {save_path}")
        
        plt.show()
    
    def plot_feature_importance(self, 
                               model_name: str,
                               top_n: int = 20,
                               save: bool = True) -> None:
        """
        Plot feature importance for a model.
        
        Args:
            model_name: Name of the model
            top_n: Number of top features to show
            save: Whether to save plot
        """
        results = self.load_results(model_name)
        
        if 'feature_importance' not in results:
            logger.warning(f"{model_name} does not have feature importance")
            return
        
        importance = results['feature_importance']
        
        # Convert to DataFrame for plotting
        df_imp = pd.DataFrame(list(importance.items()), 
                             columns=['Feature', 'Importance'])
        df_imp = df_imp.head(top_n)
        
        # Plot
        plt.figure(figsize=(12, 8))
        plt.barh(range(len(df_imp)), df_imp['Importance'], alpha=0.8)
        plt.yticks(range(len(df_imp)), df_imp['Feature'])
        plt.xlabel('Importance', fontsize=12)
        plt.ylabel('Feature', fontsize=12)
        plt.title(f'{model_name}: Top {top_n} Most Important Features', fontsize=14)
        plt.gca().invert_yaxis()  # Highest at top
        plt.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        
        if save:
            save_path = self.viz_dir / f"{model_name.lower().replace(' ', '_')}_importance.png"
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved feature importance: {save_path}")
        
        plt.show()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Test the evaluation module.
    
    Run: python src/models/evaluate.py
    """
    print("=" * 80)
    print("MODEL EVALUATION MODULE TEST")
    print("=" * 80)
    
    evaluator = ModelEvaluator()
    
    # Check for baseline results
    models_to_compare = ['Persistence', 'MovingAverage-3', 'LinearRegression']
    
    available_models = []
    for model in models_to_compare:
        results_file = evaluator.models_dir / f"{model.lower().replace(' ', '_')}_results.json"
        if results_file.exists():
            available_models.append(model)
    
    if available_models:
        print(f"\n✓ Found results for {len(available_models)} models")
        print("\nComparing models...")
        
        df_comparison = evaluator.compare_models(available_models)
        
        print("\n✓ Evaluation module working correctly!")
    else:
        print("\n⚠ No model results found")
        print("Please run: python src/models/train.py")
        print("to train baseline models first.")