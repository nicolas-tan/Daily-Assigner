# Browser Automation for Daily Bug Assignment

This solution automates the entire daily bug assignment process by controlling a Chrome browser to download from Google Sheets, process with Excel logic, and upload back - no Google API credentials needed!

## 🚀 Features

- **Automated Browser Control**: Opens Chrome and clicks through Google Sheets menus
- **Full Excel Processing**: All 8 steps from your requirements are implemented
- **Daily Scheduling**: Runs automatically at 9 AM PST every day
- **No API Setup**: Works just like manual clicking - no Google Cloud Console needed

## 📋 Prerequisites

1. **Python 3.7+** installed
2. **Google Chrome** browser installed
3. **Google account** with access to your sheets
4. **Virtual environment** (created by setup script)

## 🛠️ Installation

### Step 1: Clone/Download this folder
```bash
cd /home/nitan/Daily-Assigner
```

### Step 2: Run the setup script
```bash
chmod +x setup_cron_browser.sh
./setup_cron_browser.sh
```

This will:
- Create a virtual environment
- Install all dependencies from `requirements_browser.txt`:
  - `pandas>=1.3.0` - For Excel data processing
  - `openpyxl>=3.0.9` - For Excel file operations
  - `selenium>=4.0.0` - For browser automation
  - `webdriver-manager>=3.8.0` - For Chrome driver management
  - `python-dotenv>=0.19.0` - For environment configuration
- Set up Chrome driver
- Configure cron job for 9 AM PST daily execution

### Step 3: Configure environment
```bash
# Create .env file
cat > .env << 'EOF'
# Google Sheets URLs (get these from your browser)
TARGET_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_TARGET_SHEET_ID/edit
SOURCE_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_SOURCE_SHEET_ID/edit

# Email Configuration
SENDER_EMAIL=your-email@company.com
SENDER_PASSWORD=your-app-password

# Team Emails
GL_EMAIL=geetha@company.com
NT_EMAIL=nicolas@company.com
PP_EMAIL=phuong@company.com

# Options
CLEANUP_FILES=true
HEADLESS_MODE=false
EOF

# Edit with your actual values
nano .env
```

## 📁 File Structure

```
Daily-Assigner/
├── script_browser_automation.py  # Main automation script
├── script.py                     # Excel processing logic (all 8 steps)
├── test_script.py               # Test utilities
├── test_browser_automation.py   # Test the automation
├── requirements_browser.txt     # Python dependencies
├── setup_cron_browser.sh       # Setup & scheduling script
├── .env                        # Your configuration (create this)
└── venv/                       # Virtual environment (auto-created)
```

## 🧪 Testing

### Test the automation components:
```bash
source venv/bin/activate
python test_browser_automation.py
```

Choose option 1 to test browser control, or option 2 to test the full workflow.

### Manual test run:
```bash
source venv/bin/activate
python script_browser_automation.py
```

## 🔄 How It Works

1. **Browser Opens**: Chrome launches and navigates to your Google Sheets
2. **Download Phase**: 
   - Clicks File → Download → Microsoft Excel (.xlsx)
   - Downloads both source and target sheets
3. **Excel Processing** (all 8 steps from your requirements):
   - Data scraping and pasting
   - Dropdown tag assignment (GL/NT/PP based on failure mode)
   - Priority reordering (1-100)
   - Team distribution
   - Completed bug deletion (green cells)
   - Email notifications (top 25 bugs per team)
4. **Upload Phase**:
   - Clicks File → Import → Upload
   - Replaces the Google Sheet with processed data

## ⏰ Daily Schedule

The cron job runs daily at 9:30 AM PST. To check:
```bash
# View scheduled jobs
crontab -l

# Monitor logs
tail -f daily_assigner.log
```

## 🔧 Troubleshooting

### Chrome not found
```bash
# Install Chrome on Ubuntu/WSL
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
sudo apt-get update
sudo apt-get install google-chrome-stable
```

### Login required
- On first run, you'll need to login to Google
- The script waits up to 5 minutes for login
- Once logged in, Chrome remembers your session

### Import errors
If you get import errors for `script` or `test_script`:
```bash
# Make sure the files are in the main directory
cp "excel only/script.py" .
cp "excel only/test_script.py" .
```

### Debugging
- Screenshots are saved on errors: `download_error.png`, `upload_error.png`
- Check logs: `tail -f daily_assigner.log`
- Run with visible browser: Set `HEADLESS_MODE=false` in `.env`

## 📊 What Gets Processed

All 8 steps from your original requirements:
1. ✅ Data scraping from CQE source
2. ✅ Pasting with priority updates
3. ✅ Dropdown tag assignment (GL/NT/PP)
4. ✅ Priority reordering in Daily New
5. ✅ Distribution to team sheets
6. ✅ Priority reordering in team sheets
7. ✅ Deletion of completed bugs (green cells)
8. ✅ Email with top 25 bugs per team

## 🛡️ Security Notes

- Your Google login is handled by Chrome (not the script)
- Email passwords should use app-specific passwords
- The `.env` file contains sensitive data - don't share it
- Add `.env` to `.gitignore` if using version control

## 📞 Support

For issues:
1. Check the logs: `tail -f daily_assigner.log`
2. Run test script: `python test_browser_automation.py`
3. Verify Chrome is installed: `google-chrome --version`
4. Ensure all files are present (see File Structure above) 