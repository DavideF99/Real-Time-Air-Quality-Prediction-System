"""
Data Collection Status Dashboard

Quick overview of your data collection progress.

Usage:
    python scripts/check_status.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.cleaners import DataCleaner
from src.utils.config import get_config


def format_duration(start_date, end_date):
    """Format duration between two dates."""
    delta = end_date - start_date
    days = delta.days
    hours = delta.seconds // 3600
    return f"{days} days, {hours} hours"


def main():
    print("\n" + "=" * 70)
    print("📊 AIR QUALITY DATA COLLECTION STATUS")
    print("=" * 70 + "\n")
    
    config = get_config()
    cleaner = DataCleaner()
    
    # Check raw data directory
    raw_dir = config.get_raw_data_dir()
    csv_files = list(raw_dir.glob("aqi_data_*.csv"))
    
    print(f"📁 Raw Data Files: {len(csv_files)}")
    
    if not csv_files:
        print("\n❌ No data collected yet!")
        print("\n💡 Run this command to collect your first data:")
        print("   python scripts/collect_data.py")
        return
    
    print(f"   Latest: {csv_files[-1].name if csv_files else 'None'}")
    print()
    
    # Load all data
    try:
        df = cleaner.load_all_raw_data()
        
        if df.empty:
            print("❌ Data files exist but are empty!")
            return
        
        # Convert timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Basic statistics
        print("📈 COLLECTION STATISTICS")
        print("-" * 70)
        print(f"Total Records: {len(df)}")
        print(f"Unique Cities: {df['city_key'].nunique()}")
        print(f"Cities: {', '.join(df['city_name'].unique())}")
        print()
        
        # Date range
        start_date = df['timestamp'].min()
        end_date = df['timestamp'].max()
        duration = format_duration(start_date, end_date)
        
        print("📅 TIME RANGE")
        print("-" * 70)
        print(f"First Collection: {start_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Last Collection:  {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {duration}")
        print()
        
        # Records per city
        print("🌍 RECORDS PER CITY")
        print("-" * 70)
        city_counts = df.groupby('city_name').size().sort_values(ascending=False)
        for city, count in city_counts.items():
            print(f"   {city:20s}: {count:4d} records")
        print()
        
        # Data quality
        completeness = ((1 - df.isnull().sum() / len(df)) * 100).mean()
        print("✅ DATA QUALITY")
        print("-" * 70)
        print(f"Overall Completeness: {completeness:.1f}%")
        print()
        
        # Current AQI status
        latest = df.sort_values('timestamp').groupby('city_key').last()
        print("🌡️  LATEST AIR QUALITY")
        print("-" * 70)
        
        aqi_labels = {1: 'Good', 2: 'Fair', 3: 'Moderate', 4: 'Poor', 5: 'Very Poor'}
        
        for _, row in latest.iterrows():
            aqi_label = aqi_labels.get(row['aqi'], 'Unknown')
            emoji = '🟢' if row['aqi'] <= 2 else '🟡' if row['aqi'] == 3 else '🔴'
            print(f"   {emoji} {row['city_name']:15s}: AQI {row['aqi']} ({aqi_label:12s}) | PM2.5: {row['pm2_5']:6.2f} μg/m³")
        print()
        
        # Progress towards goals
        print("🎯 PROGRESS TOWARDS MODELING")
        print("-" * 70)
        
        target_records = 1000  # 7 days of data
        progress = (len(df) / target_records) * 100
        
        print(f"Current: {len(df)} records")
        print(f"Target:  {target_records} records (7 days)")
        print(f"Progress: {progress:.1f}%")
        
        if len(df) < 500:
            print(f"\n📊 Status: Collecting data... ({500 - len(df)} more for minimum)")
            print("   Keep collecting! Aim for at least 3-5 days.")
        elif len(df) < 1000:
            print(f"\n✅ Status: Ready for basic EDA! ({1000 - len(df)} more for optimal)")
            print("   You can start Phase 2 exploratory analysis.")
        else:
            print("\n🎉 Status: Excellent dataset! Ready for full modeling!")
            print("   You have enough data for Phase 2 & 3.")
        
        print()
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error loading data: {e}")
        print("   Run: python -m src.data.cleaners")


if __name__ == "__main__":
    main()