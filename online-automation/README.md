# Online/Browser Automation Scripts

This folder contains all scripts related to automated browser operations for Google Sheets integration.

## Files in this folder:

- **script_browser_automation.py** - Main browser automation script that downloads from Google Sheets, processes Excel files, and uploads back
- **test_browser_automation.py** - Test script for browser automation functionality
- **run_browser_automation.sh** - Shell script to run the browser automation
- **setup_cron_browser.sh** - Sets up cron job for scheduled automation
- **requirements_browser.txt** - Python dependencies for browser automation
- **google-chrome-stable_current_amd64.deb** - Chrome browser installation package

## Usage

These scripts require internet connection and Chrome browser. They automate the full workflow:
1. Download from Google Sheets
2. Process Excel files
3. Upload back to Google Sheets
4. Send email notifications

For offline processing, use the scripts in the parent directory instead. 