#!/bin/bash

# AQI Collection Monitoring Script
# Usage: bash scripts/monitor_collection.sh

PROJECT_DIR="$HOME/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline"
cd "$PROJECT_DIR"

echo ""
echo "========================================================================"
echo "🌍 AQI DATA COLLECTION MONITOR"
echo "========================================================================"
echo ""

# Check if service is loaded
echo "📡 SERVICE STATUS:"
echo "------------------------------------------------------------------------"
if launchctl list | grep -q "com.aqi.datacollector"; then
    echo "✅ Service is LOADED and ACTIVE"
    launchctl list | grep aqi
else
    echo "❌ Service is NOT LOADED"
    echo "   Run: launchctl load ~/Library/LaunchAgents/com.aqi.datacollector.plist"
fi
echo ""

# Check last collection time
echo "⏰ LAST COLLECTION:"
echo "------------------------------------------------------------------------"
if [ -f "data/logs/launchd_output.log" ]; then
    LAST_LINE=$(grep "DATA COLLECTION COMPLETED" data/logs/launchd_output.log | tail -1)
    if [ ! -z "$LAST_LINE" ]; then
        echo "$LAST_LINE"
    else
        echo "⚠️  No successful collections found in log"
    fi
else
    echo "⚠️  No log file found yet"
fi
echo ""

# Count collections today
echo "📊 COLLECTIONS TODAY:"
echo "------------------------------------------------------------------------"
TODAY=$(date +%Y-%m-%d)
if [ -f "data/logs/launchd_output.log" ]; then
    COUNT=$(grep "$TODAY.*DATA COLLECTION COMPLETED" data/logs/launchd_output.log | wc -l | tr -d ' ')
    echo "Total: $COUNT collections"
else
    echo "Total: 0 collections"
fi
echo ""

# Check recent errors
echo "⚠️  RECENT ERRORS:"
echo "------------------------------------------------------------------------"
if [ -f "data/logs/launchd_error.log" ] && [ -s "data/logs/launchd_error.log" ]; then
    echo "$(tail -5 data/logs/launchd_error.log)"
else
    echo "✅ No errors"
fi
echo ""

# Data files
echo "📁 DATA FILES:"
echo "------------------------------------------------------------------------"
FILE_COUNT=$(ls data/raw/aqi_data_*.csv 2>/dev/null | wc -l | tr -d ' ')
echo "Total CSV files: $FILE_COUNT"
if [ $FILE_COUNT -gt 0 ]; then
    echo "Latest 3 files:"
    ls -lt data/raw/aqi_data_*.csv | head -3 | awk '{print "   " $9 " (" $5 " bytes)"}'
fi
echo ""

# Next scheduled run
echo "⏭️  NEXT COLLECTION:"
echo "------------------------------------------------------------------------"
CURRENT_TIME=$(date "+%H:%M")
CURRENT_HOUR=$(date "+%H")
NEXT_HOUR=$(printf "%02d" $((10#$CURRENT_HOUR + 1)))
if [ "$NEXT_HOUR" == "24" ]; then
    NEXT_HOUR="00"
fi
echo "Scheduled for: ${NEXT_HOUR}:00:00"
echo "Current time:  ${CURRENT_TIME}"
echo ""

# Quick data summary
echo "📈 DATA SUMMARY:"
echo "------------------------------------------------------------------------"
source venv/bin/activate 2>/dev/null
python scripts/check_status.py 2>/dev/null | grep -A 5 "COLLECTION STATISTICS" | tail -5

echo ""
echo "========================================================================"
echo "💡 USEFUL COMMANDS:"
echo "========================================================================"
echo ""
echo "View live logs:       tail -f data/logs/launchd_output.log"
echo "View errors:          cat data/logs/launchd_error.log"
echo "Full status:          python scripts/check_status.py"
echo "Restart service:      launchctl unload ~/Library/LaunchAgents/com.aqi.datacollector.plist"
echo "                      launchctl load ~/Library/LaunchAgents/com.aqi.datacollector.plist"
echo "Stop service:         launchctl unload ~/Library/LaunchAgents/com.aqi.datacollector.plist"
echo "Force collection now: launchctl start com.aqi.datacollector"
echo ""