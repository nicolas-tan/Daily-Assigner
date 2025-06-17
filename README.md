# Daily Bug Assignment Automation

Excel-based bug assignment automation system with both offline and online processing capabilities.

## Directory Structure

```
Daily-Assigner/
├── offline_processor.py      # Offline Excel processing script
├── script.py                # Core bug assignment logic
├── test_script.py           # Test script for core functionality
├── OFFLINE_USAGE.md         # Guide for offline processing
├── test_template.xlsx       # Example template file
├── docs/                    # Documentation
│   └── How_It_Works_Steps_Explained.md
├── online-automation/       # Browser automation scripts (online)
│   ├── script_browser_automation.py
│   ├── test_browser_automation.py
│   ├── run_browser_automation.sh
│   ├── setup_cron_browser.sh
│   ├── requirements_browser.txt
│   ├── README_BROWSER_AUTOMATION.md
│   └── google-chrome-stable_current_amd64.deb
├── excel-only/             # Excel-specific utilities
├── google-only-versions/   # Google Sheets specific versions
├── google-xlsx-google/     # Google to Excel to Google workflow
└── pseudo-code/           # Planning and pseudo-code

```

## Quick Start - Offline Processing

1. **Create a blank template:**
   ```bash
   python offline_processor.py --create-template
   ```

2. **Process your Excel file:**
   ```bash
   python offline_processor.py your_file.xlsx
   ```

See `OFFLINE_USAGE.md` for detailed instructions.

## Core Features

- **Bug Assignment**: Automatically assigns bugs to teams (GL, NT, PP) based on failure modes
- **Priority Sorting**: Reorders bugs by priority in all sheets
- **Team Distribution**: Distributes bugs to respective team sheets
- **Completion Tracking**: Removes completed bugs marked with green
- **Backup Creation**: Automatically creates timestamped backups

## Requirements

For offline processing:
- Python 3.x
- pandas
- openpyxl

For online automation (see `online-automation/` folder):
- All of the above plus selenium, Chrome browser, internet connection

## Installation

```bash
# For offline processing only
pip install pandas openpyxl

# For full functionality including browser automation
pip install -r online-automation/requirements_browser.txt
```

## Usage Modes

### Offline Mode (Recommended for manual workflows)
Use when you manually download/upload Excel files from Google Sheets or Excel Online.
No internet or browser automation required.

### Online Mode (For full automation)
Use the scripts in `online-automation/` for automated Google Sheets integration.
Requires Chrome browser and internet connection. 