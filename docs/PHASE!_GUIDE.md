# Phase 1 Quick Reference Guide

## 🚀 Daily Operations

### Collect Data Manually

```bash
source venv/bin/activate
python scripts/collect_data.py
```

### View Logs

```bash
# Today's logs
tail -f data/logs/aqi_predictor_$(date +%Y-%m-%d).log

# Errors only
tail -f data/logs/errors_$(date +%Y-%m-%d).log
```

### Check Data Files

```bash
# Count collected files
ls data/raw/aqi_data_*.csv | wc -l

# View latest raw data
ls -lt data/raw/ | head -5

# View latest cleaned data
ls -lt data/processed/ | head -5
```

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Test Specific Module

```bash
python src/utils/config.py
python src/data/collectors.py
python src/data/cleaners.py
```

## 🔧 Troubleshooting

### API Key Issues

1. Check `.env` file exists
2. Verify API key is correct
3. Wait 2 hours after registration for activation

### No Data Collected

1. Check internet connection
2. Verify API quota not exceeded
3. Check logs: `data/logs/aqi_predictor_*.log`

### Import Errors

1. Ensure virtual environment is activated: `source venv/bin/activate`
2. Reinstall requirements: `pip install -r requirements.txt`

## 📊 Data Collection Progress

Track your data collection:

- **Target:** 7-14 days of hourly data
- **Records needed:** ~1,000-2,000 (6 cities × 24 hours × 7-14 days)
- **Check progress:**

```bash
  python -c "import pandas as pd; from src.data.cleaners import DataCleaner; dc = DataCleaner(); df = dc.load_all_raw_data(); print(f'Total records: {len(df)}'); print(f'Date range: {df.timestamp.min()} to {df.timestamp.max()}')"
```

## 🎯 Next Steps

Once you have 500+ records:

- ✅ Ready for Phase 2: Exploratory Data Analysis
