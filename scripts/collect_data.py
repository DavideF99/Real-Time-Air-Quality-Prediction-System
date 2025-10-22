"""
Automated Data Collection Script

This script:
1. Fetches air quality data for all configured cities
2. Saves raw data to CSV
3. Cleans and validates the data
4. Saves processed data
5. Generates a quality report

Run this script hourly to build your dataset:
- Manually: python scripts/collect_data.py
- With cron (Linux/Mac): Add to crontab
- With Task Scheduler (Windows): Create scheduled task

Learning Notes:
- Building ML models requires lots of data
- Run this for 7-14 days before training models
- Monitor logs to catch issues early
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.collectors import AirQualityCollector
from src.data.cleaners import DataCleaner
from src.utils.logger import get_logger, LoggerSetup

# Initialize logging
LoggerSetup.setup()
logger = get_logger(__name__)


def main():
    """Main data collection workflow."""
    
    logger.info("=" * 70)
    logger.info("STARTING DATA COLLECTION WORKFLOW")
    logger.info("=" * 70)
    
    try:
        # Step 1: Collect raw data
        logger.info("Step 1: Collecting raw data from API")
        collector = AirQualityCollector()
        
        all_data = collector.fetch_all_cities()
        
        if not all_data:
            logger.error("No data collected! Exiting.")
            return 1
        
        logger.info(f"Successfully collected data for {len(all_data)} cities")
        
        # Step 2: Save raw data
        logger.info("Step 2: Saving raw data")
        raw_filepath = collector.save_to_csv(all_data)
        logger.info(f"Raw data saved to: {raw_filepath}")
        
        # Step 3: Clean data
        logger.info("Step 3: Cleaning and validating data")
        cleaner = DataCleaner()
        
        # Load the raw file we just created
        df_raw = cleaner.load_raw_data(raw_filepath.name)
        df_clean = cleaner.clean_data(df_raw)
        
        logger.info(f"Cleaned {len(df_clean)} records")
        
        # Step 4: Save cleaned data
        logger.info("Step 4: Saving cleaned data")
        clean_filepath = cleaner.save_cleaned_data(df_clean)
        logger.info(f"Cleaned data saved to: {clean_filepath}")
        
        # Step 5: Generate quality report
        logger.info("Step 5: Generating data quality report")
        report = cleaner.generate_quality_report(df_clean)
        
        logger.info("Data Quality Summary:")
        logger.info(f"  Records: {report['total_records']}")
        logger.info(f"  Cities: {report['cities']}")
        logger.info(f"  Completeness: {report['completeness']:.1f}%")
        
        # Step 6: Check API usage
        stats = collector.get_api_call_stats()
        logger.info(f"API Usage: {stats['calls_made_today']}/{stats['max_calls_per_day']} calls today")
        
        logger.info("=" * 70)
        logger.info("DATA COLLECTION COMPLETED SUCCESSFULLY!")
        logger.info("=" * 70)
        
        return 0
        
    except Exception as e:
        logger.error("=" * 70)
        logger.error("DATA COLLECTION FAILED!")
        logger.error("=" * 70)
        logger.exception(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)