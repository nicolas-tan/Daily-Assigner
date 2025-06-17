# Offline Excel Processing Guide

This guide explains how to use the offline Excel processor for bug assignments without internet/Chrome.

## Quick Start

### 1. Create a blank template (if needed)
```bash
python offline_processor.py --create-template
# Or specify a custom name:
python offline_processor.py --create-template my_template.xlsx
```

### 2. Process your manually downloaded Excel file
```bash
# Process just the target file (if it already has data)
python offline_processor.py custom-top-cqe-bugs-daily-assigner.xlsx

# Process with a source file containing new CQE bugs
python offline_processor.py custom-top-cqe-bugs-daily-assigner.xlsx cqe_bugs.xlsx
```

## What the Script Does

1. **Loads your Excel file** with the bug assignment sheets
2. **Processes CQE data** (if source file provided)
3. **Assigns dropdown tags** based on failure modes
4. **Reorders bugs by priority**
5. **Distributes to team sheets** (GL, NT, PP)
6. **Deletes completed bugs** (marked with green)
7. **Creates a backup** of the processed file

## File Requirements

Your Excel file should have these sheets:
- `Daily New` - Main sheet for new bugs
- `GL` - Bugs assigned to GL team
- `NT` - Bugs assigned to NT team  
- `PP` - Bugs assigned to PP team

## Output

- **Updated Excel file** - Same file with all processing applied
- **Backup file** - `processed_YYYYMMDD_HHMMSS_filename.xlsx`
- **Console logs** - Shows progress and any issues

## Example Workflow

1. Download your Excel file from Google Sheets/Excel Online
2. Run: `python offline_processor.py <place cqe downloaded file into current directory, then call its name>`
3. Check the updated file and backup
4. Upload back to Google Sheets when ready

No internet or Chrome required! 