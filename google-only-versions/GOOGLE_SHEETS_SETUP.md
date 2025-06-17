# Google Sheets Integration Setup Guide

This guide explains how to use the Daily Bug Assignment automation with Google Sheets instead of local Excel files.

## Overview

We provide three approaches:

1. **Original Script** (`script.py`) - Works with local Excel files only
2. **Google Sheets Native** (`script_google_sheets.py`) - Works directly with Google Sheets API
3. **Hybrid Approach** (`script_hybrid.py`) - Downloads from Google Sheets, processes locally, uploads back

## Prerequisites

1. Google account with access to the spreadsheets
2. Google Cloud Project with Sheets API enabled
3. Service Account credentials

## Setup Steps

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Sheets API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click and Enable it

### 2. Create Service Account Credentials

1. In Google Cloud Console, go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in service account details
4. Click "Create and Continue"
5. Skip optional permissions (click "Continue")
6. Click "Done"
7. Click on the created service account
8. Go to "Keys" tab
9. Click "Add Key" > "Create new key"
10. Choose JSON format
11. Save the downloaded file as `credentials.json` in your project directory

### 3. Share Your Google Sheets

1. Open your Google Sheets (both source and target)
2. Click "Share" button
3. Share with the service account email (found in credentials.json)
4. Give "Editor" permission

### 4. Get Spreadsheet IDs

From your Google Sheets URLs:
```
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
```

Extract the `SPREADSHEET_ID` part.

### 5. Configure Environment

Update your `.env` file:
```bash
# Google Sheets Configuration
TARGET_SPREADSHEET_ID=1234567890abcdef...  # Your target sheet ID
SOURCE_SPREADSHEET_ID=0987654321fedcba...  # Your source sheet ID
GOOGLE_CREDENTIALS_FILE=credentials.json

# Email settings (same as before)
SENDER_EMAIL=your-email@company.com
SENDER_PASSWORD=your-app-password

# Team emails
GL_EMAIL=geetha@company.com
NT_EMAIL=nicolas@company.com
PP_EMAIL=phuong@company.com
```

## Usage

### Option 1: Google Sheets Native (Recommended for full automation)

```bash
# Install Google dependencies
pip install -r requirements_google.txt

# Run the Google Sheets version
python script_google_sheets.py
```

**Pros:**
- Works directly with Google Sheets
- No file downloads needed
- Real-time updates

**Cons:**
- Slower for large datasets
- Requires good internet connection

### Option 2: Hybrid Approach (Recommended for complex processing)

```bash
# Install both sets of dependencies
pip install -r requirements.txt
pip install -r requirements_google.txt

# Run the hybrid version
python script_hybrid.py
```

**Pros:**
- Faster processing (local Excel)
- All original features work
- Automatic upload back to Google Sheets

**Cons:**
- Requires temporary disk space
- More complex setup

### Option 3: Manual Download/Upload

1. Download Google Sheets as Excel:
   - File > Download > Microsoft Excel (.xlsx)
   
2. Run original script:
   ```bash
   python script.py
   ```
   
3. Upload results back to Google Sheets:
   - Open Google Sheets
   - File > Import > Upload
   - Replace current sheet

## Scheduling with Cron

For Google Sheets versions, update the cron command:

```bash
# Edit crontab
crontab -e

# Add for Google Sheets native version:
0 9 * * * cd /path/to/project && /path/to/venv/bin/python script_google_sheets.py >> daily_assigner.log 2>&1

# Or for hybrid version:
0 9 * * * cd /path/to/project && /path/to/venv/bin/python script_hybrid.py >> daily_assigner.log 2>&1
```

## Troubleshooting

### Authentication Errors
- Ensure credentials.json is in the correct location
- Verify service account has access to sheets
- Check API is enabled in Google Cloud Console

### Permission Errors
- Make sure service account has "Editor" access to sheets
- Verify spreadsheet IDs are correct

### API Quota Errors
- Google Sheets API has usage limits
- Consider using hybrid approach for large datasets
- Add delays between operations if needed

## Performance Tips

1. **For small datasets (<1000 rows)**: Use Google Sheets native
2. **For large datasets**: Use hybrid approach
3. **For fastest processing**: Download manually, process, upload manually

## Security Notes

- Keep credentials.json secure and never commit to version control
- Add `credentials.json` to `.gitignore`
- Use environment variables for sensitive data
- Regularly rotate service account keys 