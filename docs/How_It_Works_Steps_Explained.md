# Daily Bug Assignment Automation - Complete Breakdown

## 🔄 Order of Operations & Process Flow

### One-Time Setup (You only do this ONCE):
1. Run `./setup_cron_browser.sh`
   - Creates virtual environment
   - Installs all dependencies
   - Sets up Chrome driver
   - **Creates a cron job that runs forever**
   - Creates `run_browser_automation.sh` wrapper script

### Daily Automatic Process (Runs by itself at 9:30 AM PST):
1. **Cron triggers** → `run_browser_automation.sh`
2. **Wrapper script** → Activates venv & runs `script_browser_automation.py`
3. **Browser automation** → Downloads sheets, processes, uploads, sends email
4. **Logs results** → `daily_assigner.log`

## 📁 File-by-File Breakdown

### 1. `setup_cron_browser.sh` - The Setup Script
**Purpose**: One-time setup that creates the automation infrastructure

```bash
Line 1-6: Header and description
Line 8-9: Get script directory (finds where script is located)
Line 11-15: Create Python virtual environment if needed
Line 17-20: Install Python dependencies from requirements_browser.txt
Line 22-24: Install Chrome driver manager
Line 26-44: Create run_browser_automation.sh wrapper script
  - Sets up display for headless Chrome
  - Activates virtual environment
  - Runs the main Python script
  - Logs output to daily_assigner.log
Line 46: Make wrapper script executable
Line 48-72: Set up cron timing
  - Asks for timezone
  - Calculates correct time for 9:30 AM PST
  - Creates cron command string
Line 74-83: Install/update cron job
  - Checks if job exists
  - Removes old job if exists
  - Adds new job
Line 85-109: Display success message and instructions
```

### 2. `script_browser_automation.py` - The Main Automation
**Purpose**: Downloads sheets, processes bugs, uploads results, sends email

```python
Line 1-29: Imports and setup
  - Selenium for browser automation
  - Pandas for Excel processing
  - Email libraries for sending results
  - Matplotlib for screenshots

Line 41-101: ExcelScreenshotCapture class
  - capture_sheet_as_image(): Converts Excel sheet to PNG image
  - capture_tabs(): Takes screenshots of tabs 2, 3, 4

Line 104-183: EmailSender class
  - create_email_body(): Creates HTML email with summary
  - send_email(): Sends email with attachments via SMTP

Line 186-217: Email helper functions
  - send_bug_assignment_email(): Main email function
  - generate_mailto_link(): Fallback that opens Outlook

Line 220-232: GoogleSheetsAutomation class
  - __init__(): Sets up Chrome with download preferences
  - start_browser(): Launches Chrome browser
  - login_if_needed(): Handles Google login if required
  - download_google_sheet(): Downloads sheet as Excel
  - upload_to_google_sheet(): Uploads Excel back to Google
  - _rename_latest_download(): Renames downloaded files

Line 235-317: run_automated_process() - Main workflow
  Step 1: Download both Google Sheets as Excel files
  Step 2: Process Excel files using script.py
  Step 3: Upload processed file back to Google Sheets
  Step 4: Send email with results and screenshots
```

### 3. `script.py` - The Excel Processing Logic
**Purpose**: Processes bug data, assigns to teams, manages priorities

```python
Line 1-27: Setup and imports

Line 30-62: CQEToOursNewest class initialization
  - Sets up workbook paths
  - Defines team sheets (GL, NT, PP)
  - Maps team emails

Line 64-85: load_workbook()
  - Opens Excel file
  - Verifies all required sheets exist
  - Creates missing sheets if needed

Line 87-125: grab_CQE_daily()
  - Reads new bug data from source
  - Checks for existing bugs
  - Updates priorities or adds new bugs

Line 127-165: assign_dropdown_tags()
  - Creates dropdown validation for team assignment
  - Auto-assigns based on failure mode patterns

Line 167-199: _determine_assignment()
  - Pattern matching for team assignment
  - GL: graphics, display, render, gpu
  - NT: network, connectivity, wifi
  - PP: power, performance, battery

Line 201-225: reorder_by_priority()
  - Sorts bugs by priority (ascending)
  - Rewrites sheet with sorted data

Line 227-246: distribute_to_team_sheets()
  - Copies assigned bugs to respective team sheets
  - GL bugs → GL sheet, etc.

Line 248-273: delete_completed_bugs()
  - Looks for green-highlighted cells
  - Removes completed bugs from all sheets

Line 275-356: send_daily_email()
  - Creates HTML email with top 25 bugs per team
  - Formats as tables
  - Sends via SMTP

Line 358-398: run_full_process()
  - Orchestrates entire workflow
  - Runs all steps in sequence
```

## 🔄 How Cron Works (The Magic Behind Automation)

### What is Cron?
- A time-based job scheduler in Unix/Linux
- Runs commands at specified times/dates
- Works in the background as a system service

### Your Cron Job:
```bash
30 9 * * * cd /home/nitan/Daily-Assigner && ./run_browser_automation.sh
```

**Translation**:
- `30 9` = At 9:30 AM
- `* * *` = Every day, every month, every day of week
- `cd /home/nitan/Daily-Assigner` = Go to your project folder
- `./run_browser_automation.sh` = Run the automation

### Important Cron Behavior:
1. **Runs only when computer is ON**
   - If computer is off at 9:30 AM → Job doesn't run
   - If computer is sleeping → Job doesn't run
   - If computer is on → Job runs ✅

2. **Persists across reboots**
   - Cron jobs are saved permanently
   - Survive computer restarts
   - No need to set up again

3. **Missed jobs**
   - Standard cron does NOT run missed jobs
   - If computer was off at 9:30 AM, job is skipped
   - Consider `anacron` for catch-up functionality

## 🚀 Complete Setup Process (Do This Once)

1. **Initial Setup**:
   ```bash
   cd /home/nitan/Daily-Assigner
   ./setup_cron_browser.sh
   # Choose option 1 (PST/PDT)
   ```

2. **Configure Environment**:
   ```bash
   # Create .env file
   nano .env
   ```
   Add:
   ```
   TARGET_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_TARGET_ID
   SOURCE_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_SOURCE_ID
   EMAIL_RECIPIENTS=team@nvidia.com,manager@nvidia.com
   ```

3. **Test It Works**:
   ```bash
   # Activate virtual environment
   source venv/bin/activate
   
   # Test the automation
   python script_browser_automation.py
   ```

4. **Verify Cron Job**:
   ```bash
   # See your cron jobs
   crontab -l
   
   # Should show:
   # 30 9 * * * cd /home/nitan/Daily-Assigner && ./run_browser_automation.sh
   ```

## 📊 Daily Operation (Automatic)

Every day at 9:30 AM PST (when computer is on):

1. **9:30:00** - Cron wakes up
2. **9:30:01** - Launches Chrome browser
3. **9:30:05** - Downloads Target Google Sheet
4. **9:30:10** - Downloads Source Google Sheet  
5. **9:30:15** - Processes bugs (script.py):
   - Merges new bugs
   - Assigns to teams
   - Sorts by priority
   - Distributes to team sheets
6. **9:30:20** - Uploads updated sheet back
7. **9:30:25** - Takes screenshots of tabs 2,3,4
8. **9:30:30** - Opens Outlook with email ready
9. **9:30:35** - Logs completion

## 🔧 Maintenance & Monitoring

### Check if it's running:
```bash
# View recent logs
tail -f daily_assigner.log

# Check cron job exists
crontab -l

# See if process is running (at 9:30 AM)
ps aux | grep script_browser_automation
```

### If computer was off:
```bash
# Run manually
cd /home/nitan/Daily-Assigner
source venv/bin/activate
python script_browser_automation.py
```

### To stop automation:
```bash
# Remove cron job
crontab -l | grep -v 'run_browser_automation.sh' | crontab -
```

### To change time:
```bash
# Edit cron job
crontab -e
# Change 30 9 to whatever you want (e.g., 0 10 for 10:00 AM)
```

## 🎯 Key Points

1. **You run setup ONCE** - The cron job persists forever
2. **Computer must be ON** - Not sleeping, not shut down
3. **Automatic every day** - No manual intervention needed
4. **Email opens in Outlook** - Just attach files and send
5. **Logs everything** - Check daily_assigner.log for issues

The beauty is: after initial setup, you never touch it again. It just runs every morning at 9:30 AM automatically! 