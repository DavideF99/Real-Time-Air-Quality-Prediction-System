# 🌍 AQI Data Collection - Complete Command Reference

This file contains ALL commands you need to monitor and manage your data collection system.

---

## 📋 TABLE OF CONTENTS

1. [Daily Monitoring](#daily-monitoring)
2. [Service Management](#service-management)
3. [Viewing Logs](#viewing-logs)
4. [Data Verification](#data-verification)
5. [Testing & Debugging](#testing--debugging)
6. [Troubleshooting](#troubleshooting)
7. [What to Look For](#what-to-look-for)

---

## 🔍 DAILY MONITORING

### Quick Status Check (30 seconds)

```bash
cd ~/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline
bash scripts/monitor_collection.sh
```

**EXPECTED OUTPUT:**

```
✅ Service is LOADED and ACTIVE
✅ No errors
Collections today: X collections
Latest: aqi_data_20251027_XXXXXX.csv
```

**WHAT TO LOOK FOR:**

- ✅ Green checkmarks
- ✅ "Service is LOADED and ACTIVE"
- ✅ "Collections today" matches hours passed (e.g., at 3pm should show ~15 collections)
- ✅ "No errors" message
- ❌ Any red X marks mean something needs attention

---

### Detailed Status Report (1 minute)

```bash
cd ~/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline
source venv/bin/activate
python scripts/check_status.py
```

**EXPECTED OUTPUT:**

```
======================================================================
📊 AIR QUALITY DATA COLLECTION STATUS
======================================================================

📁 Raw Data Files: 50+
Total Records: 300+
Unique Cities: 6
Overall Completeness: 98.5%+

🎯 PROGRESS TOWARDS MODELING
Current: XXX records
Target: 1000 records
Progress: XX%
```

**WHAT TO LOOK FOR:**

- ✅ Records increasing each time you check
- ✅ All 6 cities listed
- ✅ Completeness above 95%
- ✅ Progress percentage growing
- ❌ Records not increasing = collection stopped
- ❌ Missing cities = API issues

---

## ⚙️ SERVICE MANAGEMENT

### Check if Service is Running

```bash
launchctl list | grep aqi
```

**EXPECTED OUTPUT:**

```
-	0	com.aqi.datacollector
```

**WHAT TO LOOK FOR:**

- ✅ Line appears = service is loaded
- ✅ Second number is `0` = last run was successful
- ❌ Nothing appears = service not loaded (see troubleshooting)
- ❌ Second number not `0` = last run failed

---

### Force Collection Now (Don't Wait for Next Hour)

```bash
launchctl start com.aqi.datacollector
```

**EXPECTED OUTPUT:**

```
(no output is normal)
```

**THEN CHECK IF IT WORKED:**

```bash
sleep 15
tail -20 data/logs/launchd_output.log
```

**WHAT TO LOOK FOR:**

- ✅ New timestamp in logs
- ✅ "DATA COLLECTION COMPLETED SUCCESSFULLY!"
- ❌ Error messages = see troubleshooting

---

### Stop Collection

```bash
launchctl unload ~/Library/LaunchAgents/com.aqi.datacollector.plist
```

**EXPECTED OUTPUT:**

```
(no output is normal)
```

**VERIFY IT STOPPED:**

```bash
launchctl list | grep aqi
```

**WHAT TO LOOK FOR:**

- ✅ Nothing appears = stopped successfully
- ❌ Still shows = didn't stop (try again)

---

### Start Collection

```bash
launchctl load ~/Library/LaunchAgents/com.aqi.datacollector.plist
```

**EXPECTED OUTPUT:**

```
(no output is normal)
```

**VERIFY IT STARTED:**

```bash
launchctl list | grep aqi
```

**WHAT TO LOOK FOR:**

- ✅ Line appears = started successfully

---

### Restart Collection (Fix Issues)

```bash
launchctl unload ~/Library/LaunchAgents/com.aqi.datacollector.plist
sleep 2
launchctl load ~/Library/LaunchAgents/com.aqi.datacollector.plist
launchctl list | grep aqi
```

**EXPECTED OUTPUT:**

```
-	0	com.aqi.datacollector
```

---

## 📄 VIEWING LOGS

### View Last 20 Lines of Output Log

```bash
tail -20 data/logs/launchd_output.log
```

**EXPECTED OUTPUT:**

```
2025-10-27 14:00:00 | INFO | Logging system initialized
2025-10-27 14:00:00 | INFO | Step 1: Collecting raw data from API
2025-10-27 14:00:05 | INFO | Successfully collected data for 6 cities
...
2025-10-27 14:00:08 | INFO | DATA COLLECTION COMPLETED SUCCESSFULLY!
```

**WHAT TO LOOK FOR:**

- ✅ Recent timestamps
- ✅ "COMPLETED SUCCESSFULLY" messages
- ✅ "6 cities" collected
- ❌ Old timestamps = collection not running
- ❌ Error messages

---

### Watch Logs in Real-Time

```bash
tail -f data/logs/launchd_output.log
```

**HOW TO USE:**

- Leave this running
- Wait for next hour (e.g., if it's 2:45pm, wait until 3:00pm)
- You'll see collection happen live
- Press `Ctrl+C` to stop watching

**WHAT TO LOOK FOR:**

- ✅ New logs appear at :00 every hour
- ✅ Collection completes in 10-15 seconds

---

### View Error Log

```bash
cat data/logs/launchd_error.log
```

**EXPECTED OUTPUT:**

```
(empty file or minor warnings)
```

**WHAT TO LOOK FOR:**

- ✅ Empty = perfect!
- ✅ Only warnings = okay
- ❌ Error messages = needs attention

---

### Count Today's Collections

```bash
grep "$(date +%Y-%m-%d).*COMPLETED SUCCESSFULLY" data/logs/launchd_output.log | wc -l
```

**EXPECTED OUTPUT:**

```
15
```

**WHAT TO LOOK FOR:**

- ✅ Number roughly matches hours passed today
- Example: If it's 3pm (15:00), should show ~15 collections
- ❌ Much lower = collection stopped at some point

---

### View All Collections Ever

```bash
grep "COMPLETED SUCCESSFULLY" data/logs/launchd_output.log | wc -l
```

**EXPECTED OUTPUT:**

```
50+
```

**WHAT TO LOOK FOR:**

- ✅ Number keeps increasing
- ✅ After 3 days should be ~72 (24 hours × 3 days)

---

## 📊 DATA VERIFICATION

### List Recent Data Files

```bash
ls -lht data/raw/ | head -10
```

**EXPECTED OUTPUT:**

```
-rw-r--r--  1 user  staff   820B Oct 27 14:00 aqi_data_20251027_140005.csv
-rw-r--r--  1 user  staff   820B Oct 27 13:00 aqi_data_20251027_130005.csv
-rw-r--r--  1 user  staff   820B Oct 27 12:00 aqi_data_20251027_120005.csv
...
```

**WHAT TO LOOK FOR:**

- ✅ Files with recent timestamps (hourly)
- ✅ Files are ~800 bytes each
- ❌ No recent files = collection stopped
- ❌ 0 byte files = collection failed

---

### Count Total Data Files

```bash
ls data/raw/aqi_data_*.csv | wc -l
```

**EXPECTED OUTPUT:**

```
50+
```

**WHAT TO LOOK FOR:**

- ✅ Number increases by 1 every hour
- ❌ Not increasing = collection stopped

---

### View Latest Data File Content

```bash
cat $(ls -t data/raw/aqi_data_*.csv | head -1)
```

**EXPECTED OUTPUT:**

```
timestamp,city_key,city_name,country,aqi,pm2_5,pm10,no2,o3,co,...
2025-10-27T14:00:00,bangkok,Bangkok,Thailand,2,15.23,22.45,...
2025-10-27T14:00:00,durban,Durban,South Africa,1,0.91,1.62,...
...
(6 rows total - one per city)
```

**WHAT TO LOOK FOR:**

- ✅ 6 data rows (one per city)
- ✅ Recent timestamps
- ✅ Reasonable values (AQI 1-5, PM2.5 < 500)
- ❌ Less than 6 rows = some cities failed
- ❌ Missing data = API issues

---

### Check Total Records Collected

```bash
cd ~/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline
source venv/bin/activate
python -c "
from src.data.cleaners import DataCleaner
dc = DataCleaner()
df = dc.load_all_raw_data()
print(f'Total Records: {len(df)}')
print(f'Cities: {df.city_name.nunique()}')
print(f'Date Range: {df.timestamp.min()} to {df.timestamp.max()}')
"
```

**EXPECTED OUTPUT:**

```
Total Records: 300+
Cities: 6
Date Range: 2025-10-27 12:00:00 to 2025-10-27 14:00:00
```

**WHAT TO LOOK FOR:**

- ✅ Records increasing daily
- ✅ 6 cities
- ✅ Expanding date range

---

## 🧪 TESTING & DEBUGGING

### Complete System Test (5 minutes)

```bash
cd ~/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline

echo "=== SYSTEM TEST START ==="
echo ""

echo "1. Checking service status..."
launchctl list | grep aqi && echo "✅ Service loaded" || echo "❌ Service NOT loaded"
echo ""

echo "2. Checking virtual environment..."
source venv/bin/activate && echo "✅ Venv activated" || echo "❌ Venv failed"
echo ""

echo "3. Testing API key..."
python -c "from src.utils.config import get_config; c = get_config(); print('✅ API Key found:', c.get_api_key()[:8] + '...')" 2>&1 | grep -q "✅" && echo "✅ API key valid" || echo "❌ API key issue"
echo ""

echo "4. Testing manual collection..."
python scripts/collect_data.py > /tmp/test_collection.log 2>&1
if grep -q "COMPLETED SUCCESSFULLY" /tmp/test_collection.log; then
    echo "✅ Manual collection works"
else
    echo "❌ Manual collection failed"
    cat /tmp/test_collection.log
fi
echo ""

echo "5. Testing launchd collection..."
launchctl start com.aqi.datacollector
sleep 15
if grep -q "$(date +%Y-%m-%d)" data/logs/launchd_output.log; then
    echo "✅ Launchd collection works"
else
    echo "❌ Launchd collection failed"
fi
echo ""

echo "6. Checking data files..."
FILE_COUNT=$(ls data/raw/aqi_data_*.csv 2>/dev/null | wc -l | tr -d ' ')
echo "Data files: $FILE_COUNT"
if [ $FILE_COUNT -gt 0 ]; then
    echo "✅ Data files exist"
else
    echo "❌ No data files"
fi
echo ""

echo "=== SYSTEM TEST COMPLETE ==="
```

**EXPECTED OUTPUT:**

```
=== SYSTEM TEST START ===

1. Checking service status...
✅ Service loaded

2. Checking virtual environment...
✅ Venv activated

3. Testing API key...
✅ API key valid

4. Testing manual collection...
✅ Manual collection works

5. Testing launchd collection...
✅ Launchd collection works

6. Checking data files...
Data files: 50+
✅ Data files exist

=== SYSTEM TEST COMPLETE ===
```

**WHAT TO LOOK FOR:**

- ✅ All green checkmarks = everything working
- ❌ Any red X = follow troubleshooting for that component

---

### Test Sleep/Wake Behavior (10 minutes)

```bash
# 1. Note current time
date

# 2. Force a collection now
launchctl start com.aqi.datacollector

# 3. Wait for it to complete
sleep 15

# 4. Check it worked
tail -5 data/logs/launchd_output.log | grep "COMPLETED"

# 5. Close laptop (put to sleep) for 5 minutes

# 6. Wake laptop and immediately check:
tail -10 data/logs/launchd_output.log

# 7. Verify new collection happened while asleep
ls -lt data/raw/ | head -3
```

**WHAT TO LOOK FOR:**

- ✅ Collection completed before sleep
- ✅ New collection happened after wake (if hour changed)
- ✅ No errors in log

---

## 🔧 TROUBLESHOOTING

### Problem: Service Not Loaded

**Check if file exists:**

```bash
ls -l ~/Library/LaunchAgents/com.aqi.datacollector.plist
```

**Expected:** File should exist

**Fix 1: Create the file**

```bash
cat > ~/Library/LaunchAgents/com.aqi.datacollector.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aqi.datacollector</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/davideferreri/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline/venv/bin/python</string>
        <string>/Users/davideferreri/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline/scripts/collect_data.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/davideferreri/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/davideferreri/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline/data/logs/launchd_output.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/davideferreri/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline/data/logs/launchd_error.log</string>
</dict>
</plist>
EOF

chmod 644 ~/Library/LaunchAgents/com.aqi.datacollector.plist
launchctl load ~/Library/LaunchAgents/com.aqi.datacollector.plist
```

**Verify fix:**

```bash
launchctl list | grep aqi
```

---

### Problem: No Data Being Collected

**Step 1: Check if service is running**

```bash
launchctl list | grep aqi
```

**Step 2: Check error log**

```bash
cat data/logs/launchd_error.log
```

**Step 3: Test manual collection**

```bash
cd ~/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline
source venv/bin/activate
python scripts/collect_data.py
```

**Step 4: Check API key**

```bash
grep OPENWEATHER_API_KEY .env
```

**Fix: Restart service**

```bash
launchctl unload ~/Library/LaunchAgents/com.aqi.datacollector.plist
launchctl load ~/Library/LaunchAgents/com.aqi.datacollector.plist
launchctl start com.aqi.datacollector
```

---

### Problem: Collections Happen But No Files

**Check directory permissions:**

```bash
ls -ld data/raw/
ls -ld data/processed/
```

**Expected:** `drwxr-xr-x`

**Fix:**

```bash
chmod 755 data/raw/
chmod 755 data/processed/
chmod 755 data/logs/
```

---

### Problem: API Errors

**Check API key is valid:**

```bash
source venv/bin/activate
python -c "
from src.data.collectors import AirQualityCollector
collector = AirQualityCollector()
print('API Key:', collector.api_key[:10] + '...')
"
```

**Test API connection:**

```bash
curl "http://api.openweathermap.org/data/2.5/air_pollution?lat=13.7563&lon=100.5018&appid=$(grep OPENWEATHER_API_KEY .env | cut -d '=' -f2)"
```

**Expected:** JSON response with air quality data

**If error "Invalid API key":**

1. Check API key at https://home.openweathermap.org/api_keys
2. Update `.env` file with correct key
3. Restart service

---

### Problem: Collections Are Delayed

**This is NORMAL if Mac was asleep!**

**Check if Mac went to sleep:**

```bash
pmset -g log | grep -i sleep | tail -5
```

**Solution:** Use launchd (you already are!) - it handles sleep automatically

**Verify launchd is running:**

```bash
launchctl list | grep aqi
```

---

## ✅ WHAT TO LOOK FOR

### Healthy System Indicators

**Service Status:**

- ✅ `launchctl list | grep aqi` shows one line
- ✅ Second number is `0`

**Logs:**

- ✅ New entries every hour in `launchd_output.log`
- ✅ "COMPLETED SUCCESSFULLY" messages
- ✅ Empty or minimal `launchd_error.log`

**Data Files:**

- ✅ New CSV file every hour
- ✅ Each file is ~800 bytes
- ✅ Files contain 6 rows (one per city)

**Data Quality:**

- ✅ `check_status.py` shows increasing records
- ✅ All 6 cities present
- ✅ Completeness > 95%
- ✅ No gaps in timestamps

---

### Warning Signs

**Service Issues:**

- ⚠️ Second number not `0` in `launchctl list`
- ⚠️ No output when running `launchctl list | grep aqi`

**Collection Issues:**

- ⚠️ No new files in past hour
- ⚠️ File sizes are 0 bytes
- ⚠️ Error messages in logs
- ⚠️ "FAILED" instead of "COMPLETED"

**Data Issues:**

- ⚠️ Less than 6 cities in data
- ⚠️ Records not increasing
- ⚠️ Completeness below 95%
- ⚠️ Large gaps in timestamps

**API Issues:**

- ⚠️ "Invalid API key" errors
- ⚠️ "Rate limit exceeded" errors
- ⚠️ Network timeout errors

---

## 📅 RECOMMENDED SCHEDULE

### Daily (30 seconds)

```bash
bash scripts/monitor_collection.sh
```

### Every 3 Days (2 minutes)

```bash
python scripts/check_status.py
```

### Weekly (5 minutes)

```bash
# Full system test
cd ~/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline
bash scripts/monitor_collection.sh
python scripts/check_status.py

# Check disk usage
du -sh data/raw/
du -sh data/logs/

# Commit to git
git add .
git commit -m "Week X data collection progress"
```

---

## 🎯 COLLECTION MILESTONES

### After 1 Day

- ✅ Should have ~24 files
- ✅ Should have ~144 records (24 hours × 6 cities)
- Run: `python scripts/check_status.py`

### After 3 Days

- ✅ Should have ~72 files
- ✅ Should have ~432 records
- Status: "Ready for basic EDA!"

### After 7 Days

- ✅ Should have ~168 files
- ✅ Should have ~1,000+ records
- Status: "Ready for full modeling!"
- **YOU CAN START PHASE 2!** 🎉

---

## 💾 BACKUP COMMANDS

### Backup Data Files

```bash
cd ~/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline
tar -czf ~/Desktop/aqi_backup_$(date +%Y%m%d).tar.gz data/
```

### Restore from Backup

```bash
cd ~/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline
tar -xzf ~/Desktop/aqi_backup_YYYYMMDD.tar.gz
```

---

## 🆘 EMERGENCY COMMANDS

### Complete Reset (Use if everything is broken)

```bash
# Stop service
launchctl unload ~/Library/LaunchAgents/com.aqi.datacollector.plist

# Backup data
cd ~/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline
cp -r data/ data_backup_$(date +%Y%m%d)/

# Recreate service
cat > ~/Library/LaunchAgents/com.aqi.datacollector.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aqi.datacollector</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/davideferreri/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline/venv/bin/python</string>
        <string>/Users/davideferreri/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline/scripts/collect_data.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/davideferreri/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/davideferreri/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline/data/logs/launchd_output.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/davideferreri/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline/data/logs/launchd_error.log</string>
</dict>
</plist>
EOF

# Fix permissions
chmod 644 ~/Library/LaunchAgents/com.aqi.datacollector.plist

# Restart service
launchctl load ~/Library/LaunchAgents/com.aqi.datacollector.plist

# Test it
launchctl start com.aqi.datacollector
sleep 15
tail -20 data/logs/launchd_output.log
```

---

## 📞 QUICK REFERENCE

**Most Used Commands:**

```bash
# Status check
bash scripts/monitor_collection.sh

# Force collection now
launchctl start com.aqi.datacollector

# View recent logs
tail -20 data/logs/launchd_output.log

# Check data
python scripts/check_status.py

# Restart service
launchctl unload ~/Library/LaunchAgents/com.aqi.datacollector.plist && launchctl load ~/Library/LaunchAgents/com.aqi.datacollector.plist
```

---

## ✅ FINAL CHECKLIST

Before considering collection "stable", verify:

- [ ] `launchctl list | grep aqi` shows service
- [ ] `bash scripts/monitor_collection.sh` shows no errors
- [ ] New files appear in `data/raw/` every hour
- [ ] `launchd_output.log` has hourly "COMPLETED" messages
- [ ] `python scripts/check_status.py` shows increasing records
- [ ] All 6 cities present in data
- [ ] Data completeness > 95%
- [ ] Service survives Mac sleep/wake

**If all checked:** You're good to go! 🎉

---

**Last Updated:** 2025-10-27  
**For Phase:** 1 - Data Collection  
**Next Phase:** Phase 2 - Exploratory Data Analysis (after 500+ records)
