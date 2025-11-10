import pandas as pd
import numpy as np

# Load all datasets
train_df = pd.read_csv('data/processed/train_data.csv')
val_df = pd.read_csv('data/processed/val_data.csv')
test_df = pd.read_csv('data/processed/test_data.csv')

print('=' * 80)
print('DATA DISTRIBUTION ANALYSIS')
print('=' * 80)

# Check target distribution
print('\nTarget (aqi_next_24h) Statistics:')
print(f'Train - Mean: {train_df["aqi_next_24h"].mean():.3f}, Std: {train_df["aqi_next_24h"].std():.3f}')
print(f'Val   - Mean: {val_df["aqi_next_24h"].mean():.3f}, Std: {val_df["aqi_next_24h"].std():.3f}')
print(f'Test  - Mean: {test_df["aqi_next_24h"].mean():.3f}, Std: {test_df["aqi_next_24h"].std():.3f}')

# Check if cities are balanced
if 'city_key' in train_df.columns:
    print('\nCity Distribution:')
    print('Train:')
    print(train_df['city_key'].value_counts())
    print('\nValidation:')
    print(val_df['city_key'].value_counts())
    print('\nTest:')
    print(test_df['city_key'].value_counts())

# Check temporal distribution
if 'timestamp' in train_df.columns:
    print('\nTemporal Coverage:')
    print(f'Train: {train_df["timestamp"].min()} to {train_df["timestamp"].max()}')
    print(f'Val:   {val_df["timestamp"].min()} to {val_df["timestamp"].max()}')
    print(f'Test:  {test_df["timestamp"].min()} to {test_df["timestamp"].max()}')

# Check for data leakage - are lag features correlating TOO strongly?
print('\nChecking for potential data leakage...')
lag_cols = [col for col in train_df.columns if 'lag' in col]
if lag_cols:
    print(f'Found {len(lag_cols)} lag features')
    # Check if any lag feature has correlation > 0.95 with target
    for col in lag_cols[:5]:  # Check first 5
        if col in train_df.columns:
            corr = train_df[col].corr(train_df['aqi_next_24h'])
            print(f'{col}: r={corr:.3f}')
            if abs(corr) > 0.95:
                print(f'  ⚠️  SUSPICIOUSLY HIGH!')

print('\n' + '=' * 80)
