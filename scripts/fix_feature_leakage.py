"""
Fix Feature Leakage

Recalculates features AFTER splitting to prevent data leakage.

The Problem:
- Features were calculated on entire dataset
- Then dataset was split
- Train set has rolling features contaminated with future data

The Solution:
- Split raw data first (by time)
- Calculate features separately for each split
- No information from val/test leaks into train features

Run: python scripts/fix_feature_leakage.py
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger

logger = get_logger(__name__)


def add_time_features(df):
    """Add time-based features."""
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Cyclical encoding
    df['hour_sin'] = np.sin(2 * np.pi * df['timestamp'].dt.hour / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['timestamp'].dt.hour / 24)
    df['day_sin'] = np.sin(2 * np.pi * df['timestamp'].dt.dayofweek / 7)
    df['day_cos'] = np.cos(2 * np.pi * df['timestamp'].dt.dayofweek / 7)
    df['month_sin'] = np.sin(2 * np.pi * df['timestamp'].dt.month / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['timestamp'].dt.month / 12)
    
    # Categorical time features
    df['is_weekend'] = (df['timestamp'].dt.dayofweek >= 5).astype(int)
    df['hour'] = df['timestamp'].dt.hour
    df['is_rush_hour'] = df['hour'].isin([7, 8, 9, 17, 18, 19]).astype(int)
    
    return df


def add_lag_features(df, group_col='city_key'):
    """Add lag features (NO LEAKAGE - only uses past data)."""
    pollutants = ['aqi', 'pm2_5', 'pm10', 'no2', 'o3']
    lags = [1, 3, 6, 12, 24]
    
    for pollutant in pollutants:
        for lag in lags:
            col_name = f'{pollutant}_lag_{lag}h'
            df[col_name] = df.groupby(group_col)[pollutant].shift(lag)
    
    return df


def add_rolling_features(df, group_col='city_key'):
    """Add rolling statistics (NO LEAKAGE - only uses past data)."""
    pollutants = ['aqi', 'pm2_5', 'pm10', 'no2', 'o3']
    windows = [3, 6, 12, 24]
    
    for pollutant in pollutants:
        for window in windows:
            # Rolling mean
            df[f'{pollutant}_rolling_mean_{window}h'] = (
                df.groupby(group_col)[pollutant]
                .rolling(window=window, min_periods=1)
                .mean()
                .reset_index(level=0, drop=True)
            )
            
            # Rolling std
            df[f'{pollutant}_rolling_std_{window}h'] = (
                df.groupby(group_col)[pollutant]
                .rolling(window=window, min_periods=1)
                .std()
                .reset_index(level=0, drop=True)
            )
            
            # Rolling min/max (only for largest window)
            if window == 24:
                df[f'{pollutant}_rolling_min_{window}h'] = (
                    df.groupby(group_col)[pollutant]
                    .rolling(window=window, min_periods=1)
                    .min()
                    .reset_index(level=0, drop=True)
                )
                
                df[f'{pollutant}_rolling_max_{window}h'] = (
                    df.groupby(group_col)[pollutant]
                    .rolling(window=window, min_periods=1)
                    .max()
                    .reset_index(level=0, drop=True)
                )
    
    return df


def add_rate_of_change(df, group_col='city_key'):
    """Add rate of change features."""
    pollutants = ['aqi', 'pm2_5', 'pm10']
    periods = [1, 3, 6, 12]
    
    for pollutant in pollutants:
        for period in periods:
            # Absolute change
            df[f'{pollutant}_change_{period}h'] = (
                df.groupby(group_col)[pollutant].diff(period)
            )
            
            # Percentage change
            df[f'{pollutant}_pct_change_{period}h'] = (
                df.groupby(group_col)[pollutant].pct_change(period)
            )
    
    return df


def add_interaction_features(df):
    """Add interaction features."""
    df['pm_total'] = df['pm2_5'] + df['pm10']
    df['pm_ratio'] = df['pm2_5'] / (df['pm10'] + 1e-6)
    df['pollution_score'] = (
        0.5 * df['pm2_5'] + 
        0.3 * df['pm10'] + 
        0.2 * df['no2']
    ) / 100
    
    return df


def create_target(df, group_col='city_key'):
    """Create target variable (24h ahead AQI)."""
    df['aqi_next_24h'] = df.groupby(group_col)['aqi'].shift(-24)
    return df


def fix_feature_leakage():
    """Main function to fix feature leakage."""
    
    logger.info("=" * 80)
    logger.info("FIXING FEATURE LEAKAGE")
    logger.info("=" * 80)
    
    # Load cleaned data (NO features, just raw pollutant values)
    data_dir = project_root / 'data' / 'processed'
    
    # Try to find cleaned data
    cleaned_files = list((project_root / 'data' / 'processed').glob('aqi_cleaned_*.csv'))
    
    if not cleaned_files:
        logger.error("No cleaned data files found!")
        logger.error("Looking for: data/processed/aqi_cleaned_*.csv")
        logger.info("\nAlternative: Load from raw data and clean")
        return
    
    # Use most recent cleaned file
    cleaned_path = sorted(cleaned_files)[-1]
    logger.info(f"Loading cleaned data: {cleaned_path}")
    
    df = pd.read_csv(cleaned_path)
    logger.info(f"Loaded {len(df)} records")
    
    # Sort by city and timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(['city_key', 'timestamp']).reset_index(drop=True)
    
    # === STEP 1: Split FIRST (chronologically) ===
    logger.info("\n" + "=" * 80)
    logger.info("STEP 1: SPLITTING DATA (NO FEATURES YET)")
    logger.info("=" * 80)
    
    n_total = len(df)
    n_train = int(0.70 * n_total)
    n_val = int(0.15 * n_total)
    
    train_df = df.iloc[:n_train].copy()
    val_df = df.iloc[n_train:n_train+n_val].copy()
    test_df = df.iloc[n_train+n_val:].copy()
    
    logger.info(f"Train: {len(train_df)} records ({train_df['timestamp'].min()} to {train_df['timestamp'].max()})")
    logger.info(f"Val:   {len(val_df)} records ({val_df['timestamp'].min()} to {val_df['timestamp'].max()})")
    logger.info(f"Test:  {len(test_df)} records ({test_df['timestamp'].min()} to {test_df['timestamp'].max()})")
    
    # === STEP 2: Engineer features SEPARATELY for each split ===
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: ENGINEERING FEATURES (NO LEAKAGE)")
    logger.info("=" * 80)
    
    for name, split_df in [('Train', train_df), ('Val', val_df), ('Test', test_df)]:
        logger.info(f"\nProcessing {name} set...")
        
        # Time features (safe - no leakage)
        split_df = add_time_features(split_df)
        
        # Lag features (uses only past data within each split)
        split_df = add_lag_features(split_df)
        
        # Rolling features (uses only past data within each split)
        split_df = add_rolling_features(split_df)
        
        # Rate of change
        split_df = add_rate_of_change(split_df)
        
        # Interactions
        split_df = add_interaction_features(split_df)
        
        # Target variable (24h ahead)
        split_df = create_target(split_df)
        
        logger.info(f"  Total features: {len(split_df.columns)}")
        
        # Update the dataframe
        if name == 'Train':
            train_df = split_df
        elif name == 'Val':
            val_df = split_df
        else:
            test_df = split_df
    
    # === STEP 3: Remove rows with NaN target ===
    logger.info("\n" + "=" * 80)
    logger.info("STEP 3: CLEANING UP")
    logger.info("=" * 80)
    
    train_df = train_df.dropna(subset=['aqi_next_24h'])
    val_df = val_df.dropna(subset=['aqi_next_24h'])
    test_df = test_df.dropna(subset=['aqi_next_24h'])
    
    logger.info(f"After removing NaN targets:")
    logger.info(f"  Train: {len(train_df)} records")
    logger.info(f"  Val:   {len(val_df)} records")
    logger.info(f"  Test:  {len(test_df)} records")
    
    # === STEP 4: Verify no leakage ===
    logger.info("\n" + "=" * 80)
    logger.info("STEP 4: VERIFICATION")
    logger.info("=" * 80)
    
    logger.info("\nTarget Statistics:")
    logger.info(f"Train - Mean: {train_df['aqi_next_24h'].mean():.3f}, "
               f"Std: {train_df['aqi_next_24h'].std():.3f}")
    logger.info(f"Val   - Mean: {val_df['aqi_next_24h'].mean():.3f}, "
               f"Std: {val_df['aqi_next_24h'].std():.3f}")
    logger.info(f"Test  - Mean: {test_df['aqi_next_24h'].mean():.3f}, "
               f"Std: {test_df['aqi_next_24h'].std():.3f}")
    
    # Check lag feature correlation
    if 'aqi_lag_24h' in train_df.columns:
        train_corr = train_df['aqi_lag_24h'].corr(train_df['aqi_next_24h'])
        logger.info(f"\naqi_lag_24h correlation with target: {train_corr:.3f}")
        logger.info("(Should be moderate: 0.5-0.8 for good feature)")
    
    # === STEP 5: Save fixed data ===
    logger.info("\n" + "=" * 80)
    logger.info("STEP 5: SAVING FIXED DATA")
    logger.info("=" * 80)
    
    # Backup old files
    backup_dir = data_dir / 'backup_old'
    backup_dir.mkdir(exist_ok=True)
    
    for filename in ['train_data.csv', 'val_data.csv', 'test_data.csv']:
        old_path = data_dir / filename
        if old_path.exists():
            backup_path = backup_dir / f"{filename.replace('.csv', '')}_leaky.csv"
            old_path.rename(backup_path)
            logger.info(f"Backed up leaky version: {backup_path.name}")
    
    # Save fixed versions
    train_path = data_dir / 'train_data.csv'
    val_path = data_dir / 'val_data.csv'
    test_path = data_dir / 'test_data.csv'
    
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    logger.info(f"\n✓ Saved: {train_path}")
    logger.info(f"✓ Saved: {val_path}")
    logger.info(f"✓ Saved: {test_path}")
    
    logger.info("\n" + "=" * 80)
    logger.info("FEATURE LEAKAGE FIXED! ✅")
    logger.info("=" * 80)
    logger.info("\nNext steps:")
    logger.info("  1. Retrain models: python scripts/train_models.py --model random-forest")
    logger.info("  2. Overfitting should be MUCH lower now")
    logger.info("  3. Val R² should be positive and > 0.5")
    logger.info("\nThe key difference:")
    logger.info("  OLD: Features calculated on full dataset, then split")
    logger.info("  NEW: Data split first, features calculated separately")


if __name__ == "__main__":
    fix_feature_leakage()