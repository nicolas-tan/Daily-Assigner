# Manual Download/Upload with Automated Excel Processing

This approach requires NO Google Cloud credentials! You manually download/upload but the Excel processing is fully automated.

## How It Works

1. **Manual Download**: You download Google Sheets as Excel files
2. **Automated Processing**: Script handles all Excel operations
3. **Manual Upload**: You upload the processed Excel back to Google Sheets

## Setup

### 1. Install Dependencies
```bash
source venv/bin/activate
pip install pandas openpyxl python-dotenv
```

### 2. Create Environment File
```bash
# Create .env file with these contents:
EXCEL_PATH=custom-top-cqe-bugs-daily-assigner.xlsx
CQE_SOURCE_PATH=cqe_bugs.xlsx

# Email settings
SENDER_EMAIL=your-email@company.com
SENDER_PASSWORD=your-app-password

# Team emails
GL_EMAIL=geetha@company.com
NT_EMAIL=nicolas@company.com
PP_EMAIL=phuong@company.com
```

## Daily Workflow

### Step 1: Download Your Google Sheets
1. Open your **target** Google Sheet (custom-top-cqe-bugs-daily-assigner)
2. File → Download → Microsoft Excel (.xlsx)
3. Save as: `custom-top-cqe-bugs-daily-assigner.xlsx`

4. Open your **source** CQE Google Sheet
5. File → Download → Microsoft Excel (.xlsx)
6. Save as: `cqe_bugs.xlsx`

### Step 2: Run the Script
```bash
python script.py
```

The script will:
- ✅ Import new bugs from CQE source
- ✅ Assign teams (GL/NT/PP) based on failure modes
- ✅ Create dropdown validations
- ✅ Reorder by priority (1-100)
- ✅ Distribute to team sheets
- ✅ Remove completed bugs (green cells)
- ✅ Send email notifications

### Step 3: Upload Back to Google Sheets
1. Open your target Google Sheet
2. File → Import → Upload
3. Select the processed `custom-top-cqe-bugs-daily-assigner.xlsx`
4. Choose "Replace current sheet"

## Automation Options

### Semi-Automated Download (using browser automation)
You could use tools like:
- **Selenium**: Automate the download process
- **AutoHotkey** (Windows): Create macros for download/upload
- **Automator** (Mac): Create workflows

### Example Selenium Script (optional)
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def download_google_sheet(sheet_url, filename):
    driver = webdriver.Chrome()
    driver.get(sheet_url)
    
    # Wait for login if needed
    time.sleep(5)
    
    # File menu
    driver.find_element(By.XPATH, "//div[text()='File']").click()
    time.sleep(1)
    
    # Download
    driver.find_element(By.XPATH, "//div[text()='Download']").click()
    time.sleep(1)
    
    # Excel format
    driver.find_element(By.XPATH, "//div[contains(text(),'Microsoft Excel')]").click()
    
    # Wait for download
    time.sleep(5)
    driver.quit()
```

## Benefits of This Approach

✅ **No Google Cloud setup required**
✅ **Full Excel functionality preserved**
✅ **Simple and straightforward**
✅ **You control when to sync**
✅ **Can review changes before uploading**

## File Structure
```
Daily-Assigner/
├── script.py                 # Main processing script
├── .env                      # Your configuration
├── custom-top-cqe-bugs-daily-assigner.xlsx  # Downloaded target
├── cqe_bugs.xlsx            # Downloaded source
└── daily_assigner.log       # Execution logs
```

## Tips

1. **Create shortcuts**: Save your Google Sheets URLs for quick access
2. **Use consistent filenames**: Always save with the same names
3. **Review before upload**: Check the processed Excel file if needed
4. **Keep backups**: Google Sheets has version history

This approach gives you full control while still automating the complex Excel processing! 