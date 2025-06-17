# Hybrid Approach: Google Sheets + Local Excel Processing

This approach gives you the best of both worlds:
- **Google Sheets** for collaboration and cloud storage
- **Local Excel processing** for complex operations and full control

## How It Works

1. **Downloads** your Google Sheets as Excel files
2. **Processes** them locally using all the Excel-specific features:
   - Complex sorting and reordering by priority
   - Dropdown data validation
   - Failure mode bucketing and team assignment
   - Cell formatting and highlighting detection
3. **Uploads** the processed results back to Google Sheets

## Setup

### 1. Install Dependencies
```bash
source venv/bin/activate
pip install -r requirements_hybrid.txt
```

### 2. Configure Environment
```bash
cp env_hybrid.txt .env
# Edit .env with your actual values
```

### 3. Set Up Google Credentials
Follow the instructions in `GOOGLE_SHEETS_SETUP.md` to:
- Create a Google Cloud project
- Enable Sheets API
- Create service account credentials
- Share your sheets with the service account

### 4. Run the Hybrid Script
```bash
python script_hybrid.py
```

## What Happens During Processing

1. **Download Phase**:
   - Downloads your target Google Sheet (custom-top-cqe-bugs-daily-assigner)
   - Downloads your source CQE Google Sheet
   - Saves them as temporary Excel files

2. **Excel Processing Phase** (using `script.py` logic):
   - Grabs CQE data and updates Daily New sheet
   - Assigns GL/NT/PP tags based on failure mode patterns
   - Creates Excel dropdown validations
   - Reorders all bugs by priority (1-100)
   - Distributes bugs to team sheets
   - Detects and removes completed bugs (green highlighting)
   - All Excel-specific features work perfectly!

3. **Upload Phase**:
   - Uploads the fully processed Excel file back to Google Sheets
   - Preserves all data and structure
   - Sends email with link to the Google Sheet

## Advantages

✅ **Full Excel functionality**: All complex operations work as designed
✅ **Google Sheets integration**: Automatic sync with cloud
✅ **No manual download/upload**: Fully automated
✅ **Preserves formatting**: Priority ordering, team assignments, etc.
✅ **Debug-friendly**: Option to keep local Excel files

## Configuration Options

In your `.env` file:
- `KEEP_LOCAL_FILES=true` - Keep downloaded Excel files for inspection
- `KEEP_LOCAL_FILES=false` - Auto-cleanup temporary files (default)

## Scheduling

To run daily at 9 AM:
```bash
crontab -e
# Add this line:
0 9 * * * cd /home/nitan/Daily-Assigner && /home/nitan/Daily-Assigner/venv/bin/python script_hybrid.py >> daily_assigner.log 2>&1
```

## Troubleshooting

If you encounter issues:
1. Set `KEEP_LOCAL_FILES=true` to inspect the Excel files
2. Check `daily_assigner.log` for detailed logs
3. Verify Google Sheets permissions
4. Ensure all required sheets exist in your Google Spreadsheet 