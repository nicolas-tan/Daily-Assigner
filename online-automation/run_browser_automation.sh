#!/bin/bash
# Wrapper script for running browser automation in cron

# Set up display for headless operation
export DISPLAY=:99
export CHROME_BIN=/usr/bin/google-chrome

# Navigate to script directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Run the browser automation script
python script_browser_automation.py >> daily_assigner.log 2>&1
