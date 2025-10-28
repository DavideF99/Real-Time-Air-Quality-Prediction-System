"""
Simple Hourly Data Collection Scheduler

This script runs continuously and collects data every hour.

Usage:
    python scripts/scheduler.py

To run in background:
    nohup python scripts/scheduler.py &

To stop:
    ps aux | grep scheduler.py
    kill [PID]

Learning Notes:
- Runs continuously until you stop it
- Collects data at the top of every hour (e.g., 1:00, 2:00, 3:00)
- Logs all operations
- Simple alternative to cron/launchd
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger, LoggerSetup

# Initialize logging
LoggerSetup.setup()
logger = get_logger(__name__)


def wait_until_next_hour():
    """Wait until the next hour starts (e.g., wait until 2:00:00)."""
    now = datetime.now()
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    wait_seconds = (next_hour - now).total_seconds()
    
    logger.info(f"Next collection at {next_hour.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Waiting {wait_seconds:.0f} seconds ({wait_seconds/60:.1f} minutes)")
    
    return wait_seconds


def collect_data():
    """Run the data collection script."""
    logger.info("=" * 70)
    logger.info("STARTING SCHEDULED DATA COLLECTION")
    logger.info("=" * 70)
    
    try:
        # Path to collection script
        script_path = project_root / "scripts" / "collect_data.py"
        python_path = sys.executable  # Use current Python interpreter
        
        # Run the collection script
        result = subprocess.run(
            [python_path, str(script_path)],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.info("✅ Data collection completed successfully")
            logger.info(f"Output: {result.stdout[:500]}")  # Log first 500 chars
        else:
            logger.error(f"❌ Data collection failed with exit code {result.returncode}")
            logger.error(f"Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Data collection timed out (>5 minutes)")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        logger.exception("Full traceback:")


def main():
    """Main scheduler loop."""
    logger.info("🚀 AQI Data Collection Scheduler Started")
    logger.info(f"Project: {project_root}")
    logger.info(f"Python: {sys.executable}")
    logger.info("Press Ctrl+C to stop")
    logger.info("")
    
    collection_count = 0
    
    try:
        # Optional: Run immediately on startup
        logger.info("Running initial data collection...")
        collect_data()
        collection_count += 1
        logger.info(f"Total collections so far: {collection_count}")
        
        # Main scheduling loop
        while True:
            # Wait until next hour
            wait_seconds = wait_until_next_hour()
            time.sleep(wait_seconds)
            
            # Collect data
            collect_data()
            collection_count += 1
            
            logger.info(f"Total collections so far: {collection_count}")
            logger.info("")
            
    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 70)
        logger.info("🛑 Scheduler stopped by user (Ctrl+C)")
        logger.info(f"Total collections completed: {collection_count}")
        logger.info("=" * 70)
        sys.exit(0)
    except Exception as e:
        logger.error("=" * 70)
        logger.error("❌ SCHEDULER CRASHED")
        logger.error("=" * 70)
        logger.exception(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()