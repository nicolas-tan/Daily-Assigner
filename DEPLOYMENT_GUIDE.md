# Bug Tracker Deployment Guide

## Overview

You now have two versions of the bug tracker:

1. **Basic Version** (`streamlit_app.py`) - Currently deployed at https://pg520-daily-new-bugs-grabbed-gl-nt-pp.streamlit.app/
2. **Enhanced Version** (`streamlit_enhanced_simple.py`) - New version with database persistence and historical tracking

## Enhanced Version Features

### 🆕 New Features Added:

1. **Database Persistence (SQLite)**
   - All imported bugs are stored in a local database
   - Remembers bugs from previous imports
   - Tracks import history

2. **Historical View**
   - View previous day's bug reports (up to 30 days)
   - Download historical HTML reports
   - Track import statistics

3. **Interactive Bug Management**
   - Mark bugs with different statuses:
     - `brand_new`
     - `existing_untouched`
     - `existing_one_comment`
     - `existing_multiple_comments`
   - Update bug status with dropdown menus

4. **Dashboard View**
   - Interactive bug cards
   - Status updates
   - Filtering and sorting

## Deployment Options

### Option 1: Deploy Enhanced Version as New App (Recommended)

**Steps:**
1. Create a new Streamlit app deployment
2. Use `streamlit_enhanced_simple.py` as the main file
3. Update requirements to include database support

**Streamlit Settings:**
- **Repository:** `nicolas-tan/Daily-Assigner`
- **Branch:** `main`
- **Main file path:** `streamlit_enhanced_simple.py`
- **App URL:** Choose a new URL like `enhanced-bug-tracker`

### Option 2: Replace Existing App

**Steps:**
1. Rename `streamlit_enhanced_simple.py` to `streamlit_app.py`
2. This will update your existing deployment
3. **⚠️ Warning:** This will replace your current working app

### Option 3: Dual Deployment

Deploy both versions:
- **Basic:** Keep current deployment for production use
- **Enhanced:** Deploy new version for testing and advanced features

## Requirements File

Create/update `requirements.txt`:

```txt
streamlit>=1.28.0
pandas>=2.0.0
openpyxl>=3.1.0
xlrd>=2.0.0
python-dotenv>=0.19.0
```

Note: SQLite3 is included with Python, so no additional dependency needed.

## Database Considerations

### Local Storage
- The enhanced version uses SQLite database (`bugs.db`)
- Data persists between sessions
- Streamlit Cloud provides persistent storage for small databases

### Data Retention
- Import history: 30 days
- Bug data: Permanent until manually cleared
- User interactions: Tracked with timestamps

## Feature Comparison

| Feature | Basic Version | Enhanced Version |
|---------|---------------|------------------|
| File Processing | ✅ | ✅ |
| Excel Download | ✅ | ✅ |
| HTML Reports | ✅ | ✅ |
| Database Storage | ❌ | ✅ |
| Historical View | ❌ | ✅ |
| Bug Status Tracking | ❌ | ✅ |
| Interactive Dashboard | ❌ | ✅ |
| Import Statistics | ❌ | ✅ |

## Recommended Deployment Strategy

### Phase 1: Test Enhanced Version
1. Deploy enhanced version as new app
2. Test all features with sample data
3. Compare results with basic version

### Phase 2: Migration
1. Once satisfied, update main app to enhanced version
2. Keep basic version as backup
3. Inform users about new features

### Phase 3: Advanced Features (Future)
- Real bug URL parsing for assignee detection
- Email notifications
- Team-specific dashboards
- Advanced reporting

## Usage Instructions

### Enhanced Version Workflow:

1. **Import Bugs**
   - Upload CQE Excel file
   - System processes and stores in database
   - View import statistics

2. **Dashboard**
   - View all active bugs
   - Update bug status using dropdowns
   - Interactive bug cards

3. **History**
   - View previous imports
   - Download historical reports
   - Track progress over time

## Database Schema

### Bugs Table
```sql
CREATE TABLE bugs (
    id INTEGER PRIMARY KEY,
    bug_id TEXT UNIQUE,
    assignment TEXT,
    priority INTEGER,
    title TEXT,
    failure_mode TEXT,
    status TEXT DEFAULT 'active',
    import_date DATE,
    bug_age TEXT DEFAULT 'brand_new'
)
```

### Import History Table
```sql
CREATE TABLE import_history (
    id INTEGER PRIMARY KEY,
    import_date DATE,
    total_bugs INTEGER,
    html_report TEXT
)
```

## Troubleshooting

### Common Issues:

1. **Database Errors**
   - Check file permissions
   - Ensure SQLite3 is available

2. **Import Failures**
   - Verify Excel file format
   - Check column mappings

3. **Performance Issues**
   - Database grows over time
   - Consider periodic cleanup

### Support

For issues or questions:
1. Check the logs in Streamlit Cloud
2. Test locally first
3. Compare with basic version behavior

## Next Steps

1. Deploy enhanced version
2. Test with real data
3. Gather feedback
4. Plan additional features based on usage

---

**Note:** The enhanced version maintains full compatibility with your existing CQE file format while adding powerful new features for bug tracking and management. 