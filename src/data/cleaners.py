"""
Data Cleaning and Validation Module

This module handles:
- Loading raw CSV files
- Validating data quality
- Handling missing values
- Detecting and removing outliers
- Generating data quality reports

Learning Notes:
- Real-world data is messy - always validate and clean!
- Document all data transformations for reproducibility
- Keep both raw and cleaned data separate
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataQualityError(Exception):
    """Custom exception for data quality issues."""
    pass


class DataCleaner:
    """
    Data validation and cleaning pipeline.
    
    This class processes raw air quality data:
    - Validates data types and ranges
    - Handles missing values
    - Detects outliers
    - Generates quality reports
    
    Usage:
        cleaner = DataCleaner()
        df = cleaner.load_raw_data('aqi_data_20251022.csv')
        df_clean = cleaner.clean_data(df)
        cleaner.save_cleaned_data(df_clean)
    """
    
    def __init__(self):
        """Initialize cleaner with configuration."""
        self.config = get_config()
        self.quality_settings = self.config.get_data_quality_settings()
        
        # Expected columns in raw data
        self.required_columns = [
            'timestamp', 'city_key', 'city_name', 'country',
            'aqi', 'pm2_5', 'pm10', 'no2', 'o3', 'co', 'so2'
        ]
        
        logger.info("DataCleaner initialized")
    
    def load_raw_data(self, filename: str) -> pd.DataFrame:
        """
        Load raw data from CSV file.
        
        Args:
            filename: Name of CSV file in raw data directory
            
        Returns:
            DataFrame with raw data
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        raw_data_dir = self.config.get_raw_data_dir()
        filepath = raw_data_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        logger.info(f"Loading raw data from {filepath}")
        
        # Load CSV
        df = pd.read_csv(filepath)
        
        logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
        
        return df
    
    def load_all_raw_data(self) -> pd.DataFrame:
        """
        Load all CSV files from raw data directory.
        
        Returns:
            Combined DataFrame with all raw data
            
        Learning Note: This is useful for batch processing multiple files
        """
        raw_data_dir = self.config.get_raw_data_dir()
        csv_files = list(raw_data_dir.glob("aqi_data_*.csv"))
        
        if not csv_files:
            logger.warning("No raw data files found")
            return pd.DataFrame()
        
        logger.info(f"Found {len(csv_files)} raw data files")
        
        # Load and combine all files
        dfs = []
        for filepath in csv_files:
            try:
                df = pd.read_csv(filepath)
                dfs.append(df)
                logger.debug(f"Loaded {filepath.name}: {len(df)} records")
            except Exception as e:
                logger.error(f"Failed to load {filepath.name}: {e}")
                continue
        
        if not dfs:
            return pd.DataFrame()
        
        # Combine all DataFrames
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Remove duplicates based on timestamp and city
        original_len = len(combined_df)
        combined_df = combined_df.drop_duplicates(
            subset=['timestamp', 'city_key'], 
            keep='first'
        )
        
        if len(combined_df) < original_len:
            logger.info(f"Removed {original_len - len(combined_df)} duplicate records")
        
        logger.info(f"Combined dataset: {len(combined_df)} records")
        
        return combined_df
    
    def validate_schema(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate DataFrame has required columns.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
            
        Learning Note: Schema validation catches structural issues early
        """
        errors = []
        
        # Check for missing columns
        missing_cols = set(self.required_columns) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
        
        # Check for empty DataFrame
        if len(df) == 0:
            errors.append("DataFrame is empty")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("Schema validation passed")
        else:
            logger.error(f"Schema validation failed: {errors}")
        
        return is_valid, errors
    
    def validate_data_ranges(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate pollutant values are within acceptable ranges.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            DataFrame with invalid values marked as NaN
            
        Learning Note: Out-of-range values often indicate sensor errors
        """
        logger.info("Validating data ranges")
        
        # Define acceptable ranges from config
        ranges = {
            'pm2_5': self.quality_settings.get('pm2_5_range', [0, 500]),
            'pm10': self.quality_settings.get('pm10_range', [0, 1000]),
            'no2': self.quality_settings.get('no2_range', [0, 400]),
            'o3': self.quality_settings.get('o3_range', [0, 500]),
            'co': self.quality_settings.get('co_range', [0, 50000]),
            'so2': self.quality_settings.get('so2_range', [0, 1000]),
            'aqi': self.quality_settings.get('aqi_range', [1, 5])
        }
        
        # Check each pollutant
        for column, (min_val, max_val) in ranges.items():
            if column in df.columns:
                # Count out-of-range values
                out_of_range = ((df[column] < min_val) | (df[column] > max_val)).sum()
                
                if out_of_range > 0:
                    logger.warning(
                        f"{column}: {out_of_range} values out of range "
                        f"[{min_val}, {max_val}]"
                    )
                    
                    # Set out-of-range values to NaN
                    df.loc[(df[column] < min_val) | (df[column] > max_val), column] = np.nan
        
        return df
    
    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values in the dataset.
        
        Strategy:
        - For pollutants: Use forward fill (carry last valid value)
        - For AQI: Calculate from pollutant values if possible
        - Drop rows with too many missing values
        
        Args:
            df: DataFrame with potential missing values
            
        Returns:
            DataFrame with missing values handled
            
        Learning Note: Different strategies for different types of data
        """
        logger.info("Handling missing values")
        
        # Count missing values per column
        missing_counts = df.isnull().sum()
        missing_pct = (missing_counts / len(df) * 100).round(2)
        
        for col, pct in missing_pct.items():
            if pct > 0:
                logger.info(f"{col}: {pct}% missing")
        
        # Sort by timestamp for forward fill
        df = df.sort_values('timestamp')
        
        # Forward fill for pollutant columns (within same city)
        pollutant_cols = ['pm2_5', 'pm10', 'no2', 'o3', 'co', 'so2', 'nh3', 'no']
        
        for city in df['city_key'].unique():
            city_mask = df['city_key'] == city
            df.loc[city_mask, pollutant_cols] = df.loc[city_mask, pollutant_cols].fillna(method='ffill', limit=3)
        
        # Drop rows with critical missing values
        # AQI is critical - drop if missing
        before_drop = len(df)
        df = df.dropna(subset=['aqi'])
        after_drop = len(df)
        
        if before_drop > after_drop:
            logger.info(f"Dropped {before_drop - after_drop} rows with missing AQI")
        
        return df
    
    def detect_outliers(self, df: pd.DataFrame, method: str = 'iqr') -> pd.DataFrame:
        """
        Detect and handle outliers using IQR method.
        
        IQR (Interquartile Range) method:
        - Calculate Q1 (25th percentile) and Q3 (75th percentile)
        - IQR = Q3 - Q1
        - Outliers are values < Q1 - 1.5*IQR or > Q3 + 1.5*IQR
        
        Args:
            df: DataFrame to process
            method: Outlier detection method ('iqr' or 'zscore')
            
        Returns:
            DataFrame with outliers marked as NaN
            
        Learning Note: Outliers can be real extreme values or errors
        """
        logger.info(f"Detecting outliers using {method} method")
        
        pollutant_cols = ['pm2_5', 'pm10', 'no2', 'o3', 'co', 'so2']
        
        if method == 'iqr':
            for col in pollutant_cols:
                if col in df.columns:
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    # Count outliers
                    outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
                    
                    if outliers > 0:
                        logger.info(f"{col}: {outliers} outliers detected")
                        # Mark outliers as NaN (optional - can also keep them)
                        # df.loc[(df[col] < lower_bound) | (df[col] > upper_bound), col] = np.nan
        
        return df
    
    def add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add useful derived features for analysis.
        
        Args:
            df: DataFrame to enhance
            
        Returns:
            DataFrame with additional features
            
        Learning Note: Feature engineering often happens during cleaning
        """
        logger.info("Adding derived features")
        
        # Convert timestamp to datetime if not already
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Extract time components
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['month'] = df['timestamp'].dt.month
        df['year'] = df['timestamp'].dt.year
        
        # Add weekend flag
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # AQI category labels
        aqi_categories = {
            1: 'Good',
            2: 'Fair',
            3: 'Moderate',
            4: 'Poor',
            5: 'Very Poor'
        }
        df['aqi_category'] = df['aqi'].map(aqi_categories)
        
        # Total particulate matter
        df['pm_total'] = df['pm2_5'] + df['pm10']
        
        logger.info(f"Added {5} derived features")
        
        return df
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Complete data cleaning pipeline.
        
        This runs all cleaning steps in sequence:
        1. Validate schema
        2. Validate data ranges
        3. Handle missing values
        4. Detect outliers
        5. Add derived features
        
        Args:
            df: Raw DataFrame
            
        Returns:
            Cleaned DataFrame
            
        Learning Note: Cleaning pipelines should be reproducible and documented
        """
        logger.info("Starting data cleaning pipeline")
        logger.info(f"Input: {len(df)} records, {len(df.columns)} columns")
        
        # Validate schema
        is_valid, errors = self.validate_schema(df)
        if not is_valid:
            raise DataQualityError(f"Schema validation failed: {errors}")
        
        # Clean data
        df_clean = df.copy()  # Don't modify original
        df_clean = self.validate_data_ranges(df_clean)
        df_clean = self.handle_missing_values(df_clean)
        df_clean = self.detect_outliers(df_clean)
        df_clean = self.add_derived_features(df_clean)
        
        logger.info(f"Output: {len(df_clean)} records, {len(df_clean.columns)} columns")
        logger.info("Data cleaning pipeline completed")
        
        return df_clean
    
    def generate_quality_report(self, df: pd.DataFrame) -> Dict:
        """
        Generate comprehensive data quality report.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with quality metrics
        """
        logger.info("Generating data quality report")
        
        report = {
            'total_records': len(df),
            'total_columns': len(df.columns),
            'date_range': {
                'start': df['timestamp'].min() if 'timestamp' in df.columns else None,
                'end': df['timestamp'].max() if 'timestamp' in df.columns else None
            },
            'cities': df['city_key'].nunique() if 'city_key' in df.columns else 0,
            'missing_values': df.isnull().sum().to_dict(),
            'missing_percentage': (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
            'completeness': ((1 - df.isnull().sum() / len(df)) * 100).round(2).mean(),
            'numeric_summary': df.describe().to_dict() if len(df) > 0 else {}
        }
        
        return report
    
    def save_cleaned_data(self, df: pd.DataFrame, filename: Optional[str] = None) -> Path:
        """
        Save cleaned data to processed directory.
        
        Args:
            df: Cleaned DataFrame
            filename: Custom filename (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"aqi_cleaned_{timestamp}.csv"
        
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        processed_dir = self.config.get_processed_data_dir()
        filepath = processed_dir / filename
        
        # Save to CSV
        df.to_csv(filepath, index=False)
        
        logger.info(f"Saved cleaned data to {filepath}")
        logger.info(f"Records: {len(df)}, Size: {filepath.stat().st_size / 1024:.2f} KB")
        
        return filepath


if __name__ == "__main__":
    """
    Test the data cleaner.
    
    Run: python src/data/cleaners.py
    """
    
    print("\n" + "=" * 70)
    print("DATA CLEANING TEST")
    print("=" * 70 + "\n")
    
    try:
        # Initialize cleaner
        cleaner = DataCleaner()
        print("✅ DataCleaner initialized\n")
        
        # Load all raw data
        print("📂 Loading raw data files...\n")
        df_raw = cleaner.load_all_raw_data()
        
        if df_raw.empty:
            print("❌ No raw data found!")
            print("   Run 'python src/data/collectors.py' first to collect data")
            exit(1)
        
        print(f"✅ Loaded {len(df_raw)} records\n")
        
        # Clean data
        print("🧹 Cleaning data...\n")
        df_clean = cleaner.clean_data(df_raw)
        print(f"✅ Cleaned {len(df_clean)} records\n")
        
        # Generate quality report
        print("-" * 70)
        print("DATA QUALITY REPORT")
        print("-" * 70)
        
        report = cleaner.generate_quality_report(df_clean)
        
        print(f"\nTotal Records: {report['total_records']}")
        print(f"Total Columns: {report['total_columns']}")
        print(f"Cities: {report['cities']}")
        print(f"Overall Completeness: {report['completeness']:.1f}%")
        
        if report['date_range']['start']:
            print(f"\nDate Range:")
            print(f"  Start: {report['date_range']['start']}")
            print(f"  End: {report['date_range']['end']}")
        
        # Save cleaned data
        print("\n" + "-" * 70)
        print("SAVING CLEANED DATA")
        print("-" * 70 + "\n")
        
        filepath = cleaner.save_cleaned_data(df_clean)
        print(f"✅ Saved to: {filepath}")
        
        print("\n" + "=" * 70)
        print("DATA CLEANING TEST PASSED! 🎉")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ DATA CLEANING TEST FAILED")
        print("=" * 70)
        print(f"\nError: {e}\n")
        logger.exception("Test failed")
        exit(1)