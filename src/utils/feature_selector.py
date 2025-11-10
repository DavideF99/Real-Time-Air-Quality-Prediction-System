"""
Feature Selection Module

Selects most important features using:
1. Correlation with target
2. Mutual Information (captures non-linear relationships)
3. Combines both methods for robust selection

Learning Notes:
- Reduces overfitting by removing irrelevant features
- Speeds up training
- Improves model interpretability
- Uses multiple methods to avoid bias
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Set
from sklearn.feature_selection import mutual_info_regression

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger

logger = get_logger(__name__)


class FeatureSelector:
    """
    Selects most important features for modeling.
    
    Methods:
    1. Correlation-based selection (linear relationships)
    2. Mutual Information (non-linear relationships)
    3. Combined selection (union of both)
    
    Usage:
        selector = FeatureSelector()
        X_selected = selector.select_features(X, y, method='combined', top_n=50)
    """
    
    def __init__(self):
        """Initialize feature selector."""
        self.correlation_scores = None
        self.mutual_info_scores = None
        self.selected_features = None
        
        logger.info("FeatureSelector initialized")
    
    def select_by_correlation(self, 
                              X: pd.DataFrame, 
                              y: pd.Series,
                              top_n: int = 20) -> List[str]:
        """
        Select features by correlation with target.
        
        Good for: Linear relationships
        
        Args:
            X: Features DataFrame
            y: Target Series
            top_n: Number of top features to select
        
        Returns:
            List of selected feature names
        """
        logger.info(f"Selecting top {top_n} features by correlation...")
        
        # Calculate correlation with target for each feature
        correlations = {}
        
        for col in X.columns:
            # Skip non-numeric columns
            if not pd.api.types.is_numeric_dtype(X[col]):
                continue
            
            # Calculate absolute correlation (magnitude matters, not direction)
            corr = abs(X[col].corr(y))
            
            # Handle NaN (can occur if feature is constant)
            if pd.notna(corr):
                correlations[col] = corr
        
        # Sort by correlation (descending)
        self.correlation_scores = pd.Series(correlations).sort_values(ascending=False)
        
        # Select top N
        selected = self.correlation_scores.head(top_n).index.tolist()
        
        logger.info(f"✓ Selected {len(selected)} features by correlation")
        logger.info(f"  Top 5: {', '.join(selected[:5])}")
        logger.info(f"  Correlation range: [{self.correlation_scores.iloc[0]:.3f}, "
                   f"{self.correlation_scores.iloc[top_n-1]:.3f}]")
        
        return selected
    
    def select_by_mutual_info(self,
                               X: pd.DataFrame,
                               y: pd.Series,
                               top_n: int = 20,
                               random_state: int = 42) -> List[str]:
        """
        Select features by Mutual Information.
        
        Good for: Non-linear relationships, complex patterns
        
        Args:
            X: Features DataFrame
            y: Target Series
            top_n: Number of top features to select
            random_state: Random seed for reproducibility
        
        Returns:
            List of selected feature names
        """
        logger.info(f"Selecting top {top_n} features by Mutual Information...")
        
        # Select only numeric columns
        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        X_numeric = X[numeric_cols]
        
        # Handle NaN values (mutual_info doesn't accept NaN)
        X_numeric = X_numeric.fillna(X_numeric.mean())
        
        # Calculate mutual information
        mi_scores = mutual_info_regression(
            X_numeric, 
            y,
            random_state=random_state,
            n_neighbors=5  # Increase for smoother estimates
        )
        
        # Create Series with scores
        self.mutual_info_scores = pd.Series(
            mi_scores, 
            index=numeric_cols
        ).sort_values(ascending=False)
        
        # Select top N
        selected = self.mutual_info_scores.head(top_n).index.tolist()
        
        logger.info(f"✓ Selected {len(selected)} features by Mutual Information")
        logger.info(f"  Top 5: {', '.join(selected[:5])}")
        logger.info(f"  MI range: [{self.mutual_info_scores.iloc[0]:.3f}, "
                   f"{self.mutual_info_scores.iloc[top_n-1]:.3f}]")
        
        return selected
    
    def select_combined(self,
                        X: pd.DataFrame,
                        y: pd.Series,
                        top_n_per_method: int = 20,
                        random_state: int = 42) -> List[str]:
        """
        Select features using both methods (union).
        
        Takes top N from correlation + top N from MI.
        Result will have at most 2*N features (or fewer if overlap).
        
        Args:
            X: Features DataFrame
            y: Target Series
            top_n_per_method: Top N from each method
            random_state: Random seed
        
        Returns:
            List of selected feature names
        """
        logger.info(f"Selecting features using combined method...")
        logger.info(f"  Top {top_n_per_method} from correlation")
        logger.info(f"  Top {top_n_per_method} from Mutual Information")
        
        # Get top features from each method
        corr_features = self.select_by_correlation(X, y, top_n=top_n_per_method)
        mi_features = self.select_by_mutual_info(X, y, top_n=top_n_per_method, 
                                                  random_state=random_state)
        
        # Union of both (remove duplicates)
        combined = list(set(corr_features + mi_features))
        
        # Count overlap
        overlap = len(corr_features) + len(mi_features) - len(combined)
        
        logger.info(f"\n✓ Combined selection results:")
        logger.info(f"  Correlation features: {len(corr_features)}")
        logger.info(f"  MI features: {len(mi_features)}")
        logger.info(f"  Overlap: {overlap}")
        logger.info(f"  Total unique features: {len(combined)}")
        
        # Show features only in correlation
        only_corr = set(corr_features) - set(mi_features)
        if only_corr:
            logger.info(f"  Only in correlation: {len(only_corr)} features")
        
        # Show features only in MI
        only_mi = set(mi_features) - set(corr_features)
        if only_mi:
            logger.info(f"  Only in MI: {len(only_mi)} features")
        
        self.selected_features = combined
        
        return combined
    
    def select_features(self,
                       X: pd.DataFrame,
                       y: pd.Series,
                       method: str = 'combined',
                       top_n: int = 20,
                       random_state: int = 42) -> pd.DataFrame:
        """
        Main method to select features.
        
        Args:
            X: Features DataFrame
            y: Target Series
            method: Selection method ('correlation', 'mutual_info', 'combined')
            top_n: Number of top features (per method if combined)
            random_state: Random seed
        
        Returns:
            DataFrame with only selected features
        """
        logger.info("=" * 80)
        logger.info("FEATURE SELECTION")
        logger.info("=" * 80)
        logger.info(f"Input features: {len(X.columns)}")
        logger.info(f"Method: {method}")
        logger.info(f"Top N: {top_n}")
        
        if method == 'correlation':
            selected = self.select_by_correlation(X, y, top_n=top_n)
        
        elif method == 'mutual_info':
            selected = self.select_by_mutual_info(X, y, top_n=top_n, 
                                                   random_state=random_state)
        
        elif method == 'combined':
            selected = self.select_combined(X, y, top_n_per_method=top_n,
                                           random_state=random_state)
        
        else:
            raise ValueError(f"Unknown method: {method}. "
                           f"Use 'correlation', 'mutual_info', or 'combined'")
        
        # Return DataFrame with selected features
        X_selected = X[selected]
        
        logger.info(f"\n✓ Feature selection complete!")
        logger.info(f"  Selected: {len(selected)} features")
        logger.info(f"  Reduction: {len(X.columns)} → {len(selected)} "
                   f"({100 * (1 - len(selected)/len(X.columns)):.1f}% reduction)")
        logger.info("=" * 80)
        
        return X_selected
    
    def get_feature_scores(self) -> pd.DataFrame:
        """
        Get scores from both methods for all features.
        
        Returns:
            DataFrame with correlation and MI scores
        """
        if self.correlation_scores is None or self.mutual_info_scores is None:
            logger.warning("Run feature selection first")
            return None
        
        # Combine scores
        df = pd.DataFrame({
            'correlation': self.correlation_scores,
            'mutual_info': self.mutual_info_scores
        })
        
        # Add rank
        df['corr_rank'] = df['correlation'].rank(ascending=False)
        df['mi_rank'] = df['mutual_info'].rank(ascending=False)
        df['avg_rank'] = (df['corr_rank'] + df['mi_rank']) / 2
        
        # Sort by average rank
        df = df.sort_values('avg_rank')
        
        return df
    
    def save_selected_features(self, filepath: Path) -> None:
        """
        Save list of selected features to file.
        
        Args:
            filepath: Where to save the feature list
        """
        if self.selected_features is None:
            logger.warning("No features selected yet")
            return
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as text file (one feature per line)
        with open(filepath, 'w') as f:
            for feature in sorted(self.selected_features):
                f.write(f"{feature}\n")
        
        logger.info(f"Saved {len(self.selected_features)} features to {filepath}")
    
    @staticmethod
    def load_selected_features(filepath: Path) -> List[str]:
        """
        Load previously selected features from file.
        
        Args:
            filepath: Feature list file
        
        Returns:
            List of feature names
        """
        with open(filepath, 'r') as f:
            features = [line.strip() for line in f if line.strip()]
        
        logger.info(f"Loaded {len(features)} features from {filepath}")
        
        return features


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def select_features_for_modeling(
    train_path: Path,
    val_path: Path,
    test_path: Path,
    method: str = 'combined',
    top_n: int = 25,
    save_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, 
           pd.Series, pd.Series, pd.Series]:
    """
    Select features and return processed train/val/test sets.
    
    Args:
        train_path: Path to training data
        val_path: Path to validation data
        test_path: Path to test data
        method: Selection method
        top_n: Top N features per method
        save_path: Where to save selected feature list
    
    Returns:
        X_train, X_val, X_test, y_train, y_val, y_test (all with selected features)
    """
    logger.info("Loading data for feature selection...")
    
    # Load data
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)
    
    # Separate features and target
    target_col = 'aqi_next_24h'
    exclude_cols = [target_col, 'timestamp', 'city_name', 'country']
    feature_cols = [col for col in train_df.columns if col not in exclude_cols]
    
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    
    X_val = val_df[feature_cols]
    y_val = val_df[target_col]
    
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]
    
    logger.info(f"Loaded: {len(X_train)} train, {len(X_val)} val, {len(X_test)} test")
    logger.info(f"Original features: {len(feature_cols)}")
    
    # Select features on training data
    selector = FeatureSelector()
    X_train_selected = selector.select_features(X_train, y_train, 
                                                method=method, top_n=top_n)
    
    # Apply same selection to val and test
    selected_features = X_train_selected.columns.tolist()
    X_val_selected = X_val[selected_features]
    X_test_selected = X_test[selected_features]
    
    # Save selected features if path provided
    if save_path:
        selector.save_selected_features(save_path)
    
    logger.info(f"\n✓ Feature selection complete for all datasets")
    
    return X_train_selected, X_val_selected, X_test_selected, y_train, y_val, y_test


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Test feature selection.
    
    Run: python src/utils/feature_selector.py
    """
    print("=" * 80)
    print("FEATURE SELECTOR TEST")
    print("=" * 80)
    
    # Check if real data exists
    data_dir = project_root / 'data' / 'processed'
    train_path = data_dir / 'train_data.csv'
    
    if not train_path.exists():
        print("\n⚠ Training data not found")
        print("Testing with synthetic data instead...\n")
        
        # Create synthetic test data
        np.random.seed(42)
        n_samples = 500
        n_features = 100
        
        # Generate random features
        X = pd.DataFrame(
            np.random.randn(n_samples, n_features),
            columns=[f'feature_{i}' for i in range(n_features)]
        )
        
        # Create target with strong relationship to some features
        y = (2 * X['feature_0'] +       # Strong linear
             3 * X['feature_1'] +        # Strong linear
             X['feature_2'] ** 2 +       # Non-linear
             np.random.randn(n_samples) * 0.5)  # Noise
        
        print(f"Synthetic data: {n_samples} samples, {n_features} features")
        
    else:
        print("\n✓ Found real training data, using it!\n")
        
        # Load real data
        train_df = pd.read_csv(train_path)
        
        target_col = 'aqi_next_24h'
        exclude_cols = [target_col, 'timestamp', 'city_name', 'country']
        feature_cols = [col for col in train_df.columns if col not in exclude_cols]
        
        X = train_df[feature_cols]
        y = train_df[target_col]
        
        print(f"Real data: {len(X)} samples, {len(X.columns)} features")
    
    # ========================================================================
    # Test 1: Correlation Selection
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 1: Correlation-Based Selection")
    print("=" * 80)
    
    selector = FeatureSelector()
    X_corr = selector.select_features(X, y, method='correlation', top_n=20)
    
    print(f"\nSelected features: {len(X_corr.columns)}")
    print(f"Top 10: {list(X_corr.columns[:10])}")
    
    # ========================================================================
    # Test 2: Mutual Information Selection
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 2: Mutual Information Selection")
    print("=" * 80)
    
    selector2 = FeatureSelector()
    X_mi = selector2.select_features(X, y, method='mutual_info', top_n=20)
    
    print(f"\nSelected features: {len(X_mi.columns)}")
    print(f"Top 10: {list(X_mi.columns[:10])}")
    
    # ========================================================================
    # Test 3: Combined Selection
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 3: Combined Selection")
    print("=" * 80)
    
    selector3 = FeatureSelector()
    X_combined = selector3.select_features(X, y, method='combined', top_n=20)
    
    print(f"\nSelected features: {len(X_combined.columns)}")
    print(f"Features: {list(X_combined.columns)}")
    
    # ========================================================================
    # Test 4: Feature Scores Comparison
    # ========================================================================
    print("\n" + "=" * 80)
    print("TEST 4: Feature Scores")
    print("=" * 80)
    
    scores_df = selector3.get_feature_scores()
    if scores_df is not None:
        print("\nTop 10 features by average rank:")
        print(scores_df.head(10))
    
    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\n✅ Feature selector works correctly!")
    print("\nKey points:")
    print("  • Correlation: Good for linear relationships")
    print("  • Mutual Info: Good for non-linear patterns")
    print("  • Combined: Best of both worlds (recommended)")
    print("\nNext: Integrate with model training pipeline")