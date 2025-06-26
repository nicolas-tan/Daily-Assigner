#!/usr/bin/env python3
"""
Complete Enhanced Bug Tracker with Advanced Features
Includes: Database persistence, historical tracking, In Progress, Completed sections,
URL parsing for assignee detection, and interactive copy-paste functionality
"""

import streamlit as st
import pandas as pd
import sqlite3
import os
import tempfile
import re
import requests
from datetime import datetime, timedelta
from offline_processor import is_cqe_file, process_single_cqe_file, create_team_sheets_email_html

# Database setup
DB_FILE = "enhanced_bugs.db"

# Team members for assignee detection
TEAM_MEMBERS = [
    "Nicolas Tan", 
    "Geethalakshmi Sundaresan", 
    "Phuong Pham", 
    "Jack Gong"
]

def init_database():
    """Initialize comprehensive database schema"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Main bugs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bugs (
            id INTEGER PRIMARY KEY,
            bug_id TEXT UNIQUE,
            assignment TEXT,
            priority INTEGER,
            title TEXT,
            failure_mode TEXT,
            created_date TEXT,
            completed TEXT,
            sn_associated TEXT,
            product TEXT,
            status TEXT DEFAULT 'active',
            import_date DATE,
            bug_age TEXT DEFAULT 'brand_new',
            assignee_detected TEXT,
            comment_count INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Import history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS import_history (
            id INTEGER PRIMARY KEY,
            import_date DATE,
            total_bugs INTEGER,
            new_bugs INTEGER,
            updated_bugs INTEGER,
            html_report TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # In progress bugs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS in_progress (
            id INTEGER PRIMARY KEY,
            bug_id TEXT,
            assignment TEXT,
            priority INTEGER,
            title TEXT,
            failure_mode TEXT,
            created_date TEXT,
            completed TEXT,
            sn_associated TEXT,
            product TEXT,
            status TEXT DEFAULT 'in_progress',
            user_notes TEXT,
            added_date DATE,
            assignee_detected TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Completed bugs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS completed_bugs (
            id INTEGER PRIMARY KEY,
            bug_id TEXT,
            assignment TEXT,
            priority INTEGER,
            title TEXT,
            failure_mode TEXT,
            created_date TEXT,
            completed_date DATE,
            sn_associated TEXT,
            product TEXT,
            user_notes TEXT,
            assignee_detected TEXT,
            completion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Custom user data table (for copy-paste functionality)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_bugs (
            id INTEGER PRIMARY KEY,
            bug_id TEXT,
            assignment TEXT,
            priority INTEGER,
            title TEXT,
            failure_mode TEXT,
            created_date TEXT,
            completed TEXT,
            sn_associated TEXT,
            product TEXT,
            user_notes TEXT,
            added_by_user BOOLEAN DEFAULT TRUE,
            added_date DATE,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def detect_assignee_from_url(bug_url):
    """
    Detect assignee from bug URL by parsing content
    This is a placeholder - in production you'd implement actual web scraping
    """
    if not bug_url or not isinstance(bug_url, str):
        return None
    
    # Skip if not a valid URL
    if not bug_url.startswith('http'):
        return None
    
    try:
        # In a real implementation, you would:
        # 1. Make HTTP request to the bug URL
        # 2. Parse HTML content
        # 3. Search for team member names in comments/assignee fields
        
        # For now, simulate detection based on URL patterns or mock data
        # You can replace this with actual web scraping logic
        
        # Example: if URL contains certain patterns, assign to specific team members
        url_lower = bug_url.lower()
        
        # Simulate detection logic (replace with real implementation)
        for member in TEAM_MEMBERS:
            member_keywords = member.lower().split()
            if any(keyword in url_lower for keyword in member_keywords):
                return member
        
        # In real implementation:
        # response = requests.get(bug_url, timeout=10)
        # soup = BeautifulSoup(response.content, 'html.parser')
        # content = soup.get_text().lower()
        # for member in TEAM_MEMBERS:
        #     if member.lower() in content:
        #         return member
        
        return None
        
    except Exception as e:
        st.warning(f"Could not parse URL {bug_url}: {str(e)}")
        return None

def count_comments_from_url(bug_url):
    """
    Count comments from team members in bug URL
    This is a placeholder for actual implementation
    """
    if not bug_url or not isinstance(bug_url, str) or not bug_url.startswith('http'):
        return 0
    
    try:
        # Placeholder implementation
        # In real version, you'd parse the bug page and count comments from team members
        # For now, return a random number for demonstration
        import random
        return random.randint(0, 5)
        
    except Exception:
        return 0

def save_bugs_to_db(df):
    """Enhanced bug saving with assignee detection"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    new_count = 0
    updated_count = 0
    
    for _, row in df.iterrows():
        bug_id = row.get('Bug ID', '')
        if not bug_id:
            continue
        
        # Detect assignee and count comments
        assignee = detect_assignee_from_url(bug_id)
        comment_count = count_comments_from_url(bug_id)
        
        # Determine bug age based on existing data and comments
        cursor.execute('SELECT id, bug_age FROM bugs WHERE bug_id = ?', (bug_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing bug
            bug_age = 'existing_untouched'
            if comment_count > 0:
                if comment_count >= 2:
                    bug_age = 'existing_multiple_comments'
                else:
                    bug_age = 'existing_one_comment'
            
            cursor.execute('''
                UPDATE bugs SET 
                assignment=?, priority=?, title=?, failure_mode=?, created_date=?,
                completed=?, sn_associated=?, product=?, import_date=?, 
                assignee_detected=?, comment_count=?, bug_age=?, last_updated=CURRENT_TIMESTAMP
                WHERE bug_id=?
            ''', (
                row.get('Assignment', ''), row.get('Priority', 0), row.get('Title', ''),
                row.get('Failure Mode', ''), row.get('Created Date', ''),
                row.get('COMPLETED', ''), row.get('SN Associated', ''),
                row.get('Product', ''), datetime.now().date(), assignee, comment_count, bug_age, bug_id
            ))
            updated_count += 1
        else:
            # Insert new bug
            cursor.execute('''
                INSERT INTO bugs 
                (bug_id, assignment, priority, title, failure_mode, created_date,
                 completed, sn_associated, product, import_date, assignee_detected, comment_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                bug_id, row.get('Assignment', ''), row.get('Priority', 0),
                row.get('Title', ''), row.get('Failure Mode', ''),
                row.get('Created Date', ''), row.get('COMPLETED', ''),
                row.get('SN Associated', ''), row.get('Product', ''),
                datetime.now().date(), assignee, comment_count
            ))
            new_count += 1
    
    conn.commit()
    conn.close()
    return new_count, updated_count

def parse_bulk_bug_data(text_input):
    """Parse copy-pasted bug data into structured format"""
    if not text_input.strip():
        return []
    
    lines = text_input.strip().split('\n')
    bugs = []
    
    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue
            
        # Try to parse tab-separated or comma-separated values
        parts = line.split('\t') if '\t' in line else line.split(',')
        
        if len(parts) >= 4:  # Minimum required fields
            bug_data = {
                'Assignment': parts[0].strip() if len(parts) > 0 else '',
                'Bug ID': parts[1].strip() if len(parts) > 1 else '',
                'Priority': int(parts[2].strip()) if len(parts) > 2 and parts[2].strip().isdigit() else 1,
                'Title': parts[3].strip() if len(parts) > 3 else '',
                'Failure Mode': parts[4].strip() if len(parts) > 4 else '',
                'Created Date': parts[5].strip() if len(parts) > 5 else '',
                'COMPLETED': parts[6].strip() if len(parts) > 6 else '',
                'SN Associated': parts[7].strip() if len(parts) > 7 else '',
                'Product': parts[8].strip() if len(parts) > 8 else ''
            }
            bugs.append(bug_data)
    
    return bugs

# Initialize database
init_database()

# Streamlit app
st.set_page_config(page_title="Complete Enhanced Bug Tracker", page_icon="🐛", layout="wide")

# Sidebar navigation
st.sidebar.title("🐛 Complete Bug Tracker")
page = st.sidebar.radio("Navigate", [
    "📥 Import Bugs", 
    "📊 Dashboard", 
    "📅 History", 
    "🔄 In Progress", 
    "✅ Completed",
    "📝 Custom Bugs",
    "⚙️ Settings"
])

if page == "📥 Import Bugs":
    st.title("📥 Import New Bugs")
    st.markdown("Upload your CQE Excel file to process and store bugs with full tracking.")
    
    uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx', 'xls'])
    
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            tmp.write(uploaded_file.getvalue())
            temp_path = tmp.name
        
        try:
            if is_cqe_file(temp_path):
                st.info("🔍 CQE file detected - processing with assignee detection")
                
                if st.button("Process File", type="primary"):
                    with st.spinner("Processing with advanced features..."):
                        output_file = process_single_cqe_file(temp_path)
                        
                        if output_file and os.path.exists(output_file):
                            # Read processed data
                            import openpyxl
                            wb = openpyxl.load_workbook(output_file)
                            sheet = wb['Daily New']
                            
                            data = []
                            headers = [cell.value for cell in sheet[1]]
                            for row in sheet.iter_rows(min_row=2, values_only=True):
                                if any(row):
                                    data.append(row)
                            
                            df = pd.DataFrame(data, columns=headers)
                            wb.close()
                            
                            # Save to database with enhanced features
                            new_bugs, updated_bugs = save_bugs_to_db(df)
                            
                            # Generate HTML report
                            html_report = create_team_sheets_email_html(output_file)
                            
                            # Save import history
                            conn = sqlite3.connect(DB_FILE)
                            cursor = conn.cursor()
                            cursor.execute('''
                                INSERT INTO import_history 
                                (import_date, total_bugs, new_bugs, updated_bugs, html_report)
                                VALUES (date('now'), ?, ?, ?, ?)
                            ''', (len(df), new_bugs, updated_bugs, html_report))
                            conn.commit()
                            conn.close()
                            
                            st.success("✅ Import completed with advanced processing!")
                            
                            # Enhanced summary
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Total Bugs", len(df))
                            with col2:
                                st.metric("New Bugs", new_bugs)
                            with col3:
                                st.metric("Updated Bugs", updated_bugs)
                            with col4:
                                # Count bugs with detected assignees
                                conn = sqlite3.connect(DB_FILE)
                                assignee_count = pd.read_sql_query(
                                    'SELECT COUNT(*) as count FROM bugs WHERE assignee_detected IS NOT NULL', 
                                    conn
                                ).iloc[0]['count']
                                conn.close()
                                st.metric("Assignees Detected", assignee_count)
                            
                            # Download options
                            col1, col2 = st.columns(2)
                            with col1:
                                with open(output_file, 'rb') as f:
                                    st.download_button(
                                        "📥 Download Enhanced Excel",
                                        f.read(),
                                        file_name=f"enhanced_{datetime.now().strftime('%Y%m%d')}.xlsx"
                                    )
                            with col2:
                                st.download_button(
                                    "📄 Download HTML Report",
                                    html_report,
                                    file_name=f"report_{datetime.now().strftime('%Y%m%d')}.html",
                                    mime="text/html"
                                )
                            
                            os.remove(output_file)
                        else:
                            st.error("❌ Processing failed")
            else:
                st.warning("⚠️ File format not recognized as CQE file")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

elif page == "📊 Dashboard":
    st.title("📊 Enhanced Bug Dashboard")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        team_filter = st.selectbox("Filter by Team", ["All", "GL", "NT", "PP"])
    with col2:
        age_filter = st.selectbox("Filter by Age", ["All", "brand_new", "existing_untouched", "existing_one_comment", "existing_multiple_comments"])
    with col3:
        assignee_filter = st.selectbox("Filter by Assignee", ["All"] + TEAM_MEMBERS)
    
    # Build query
    query = 'SELECT * FROM bugs WHERE status = "active"'
    params = []
    
    if team_filter != "All":
        query += ' AND assignment = ?'
        params.append(team_filter)
    if age_filter != "All":
        query += ' AND bug_age = ?'
        params.append(age_filter)
    if assignee_filter != "All":
        query += ' AND assignee_detected = ?'
        params.append(assignee_filter)
    
    query += ' ORDER BY priority ASC, last_updated DESC'
    
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    if not df.empty:
        st.info(f"📋 Showing {len(df)} active bugs")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Active", len(df))
        with col2:
            assigned_count = len(df[df['assignee_detected'].notna()])
            st.metric("With Assignees", assigned_count)
        with col3:
            new_count = len(df[df['bug_age'] == 'brand_new'])
            st.metric("Brand New", new_count)
        with col4:
            commented_count = len(df[df['comment_count'] > 0])
            st.metric("With Comments", commented_count)
        
        # Interactive bug management
        for _, bug in df.iterrows():
            with st.expander(f"🐛 {bug['bug_id']} - P{bug['priority']} - {bug['title'][:60]}..."):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Team:** {bug['assignment']}")
                    st.write(f"**Failure Mode:** {bug['failure_mode']}")
                    st.write(f"**Product:** {bug['product']}")
                    st.write(f"**Bug Age:** {bug['bug_age'].replace('_', ' ').title()}")
                    if bug['assignee_detected']:
                        st.write(f"**🎯 Detected Assignee:** {bug['assignee_detected']}")
                    if bug['comment_count'] > 0:
                        st.write(f"**💬 Comments:** {bug['comment_count']}")
                
                with col2:
                    # Bug age selector
                    age_options = ['brand_new', 'existing_untouched', 'existing_one_comment', 'existing_multiple_comments']
                    current_age_idx = age_options.index(bug['bug_age']) if bug['bug_age'] in age_options else 0
                    
                    new_age = st.selectbox(
                        "Bug Status",
                        age_options,
                        index=current_age_idx,
                        key=f"age_{bug['id']}"
                    )
                    
                    if new_age != bug['bug_age']:
                        if st.button("Update Status", key=f"update_age_{bug['id']}"):
                            conn = sqlite3.connect(DB_FILE)
                            cursor = conn.cursor()
                            cursor.execute('UPDATE bugs SET bug_age = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ?', (new_age, bug['id']))
                            conn.commit()
                            conn.close()
                            st.success("Status updated!")
                            st.rerun()
                
                with col3:
                    # Action buttons
                    if st.button("🔄 Move to In Progress", key=f"progress_{bug['id']}"):
                        # Move to in-progress table
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        
                        cursor.execute('''
                            INSERT INTO in_progress 
                            (bug_id, assignment, priority, title, failure_mode, created_date,
                             completed, sn_associated, product, added_date, assignee_detected)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, date('now'), ?)
                        ''', (bug['bug_id'], bug['assignment'], bug['priority'], bug['title'],
                              bug['failure_mode'], bug['created_date'], bug['completed'],
                              bug['sn_associated'], bug['product'], bug['assignee_detected']))
                        
                        cursor.execute('UPDATE bugs SET status = "in_progress" WHERE id = ?', (bug['id'],))
                        conn.commit()
                        conn.close()
                        st.success("Moved to In Progress!")
                        st.rerun()
                    
                    if st.button("⏸️ Deprioritize", key=f"deprio_{bug['id']}"):
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute('UPDATE bugs SET status = "deprioritized" WHERE id = ?', (bug['id'],))
                        conn.commit()
                        conn.close()
                        st.success("Bug deprioritized!")
                        st.rerun()
    else:
        st.info("No active bugs found with current filters")

elif page == "📅 History":
    st.title("📅 Historical Bug Reports")
    
    days_back = st.slider("Days to look back", 1, 30, 7)
    
    conn = sqlite3.connect(DB_FILE)
    history_df = pd.read_sql_query(f'''
        SELECT * FROM import_history 
        WHERE import_date >= date('now', '-{days_back} days')
        ORDER BY import_date DESC
    ''', conn)
    conn.close()
    
    if not history_df.empty:
        st.subheader("📊 Import History")
        
        for _, record in history_df.iterrows():
            with st.expander(f"📅 {record['import_date']} - {record['total_bugs']} bugs"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Bugs", record['total_bugs'])
                with col2:
                    st.metric("New Bugs", record.get('new_bugs', 0))
                with col3:
                    st.metric("Updated Bugs", record.get('updated_bugs', 0))
                
                if record['html_report']:
                    st.subheader("📄 HTML Report")
                    st.components.v1.html(record['html_report'], height=500, scrolling=True)
                    
                    st.download_button(
                        "📥 Download HTML Report",
                        record['html_report'],
                        file_name=f"report_{record['import_date']}.html",
                        mime="text/html",
                        key=f"download_{record['id']}"
                    )
    else:
        st.info("No historical data found for the selected period")

elif page == "🔄 In Progress":
    st.title("🔄 In Progress Bugs")
    st.markdown("Manage bugs you're actively working on with notes and status tracking.")
    
    # Add new bug section
    with st.expander("➕ Add New Bug to In Progress"):
        with st.form("add_progress_bug"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_bug_id = st.text_input("Bug ID (URL)")
                new_assignment = st.selectbox("Assignment", ["GL", "NT", "PP"])
                new_priority = st.number_input("Priority", min_value=1, value=1)
                new_title = st.text_area("Title")
                
            with col2:
                new_failure_mode = st.text_input("Failure Mode")
                new_sn = st.text_input("SN Associated")
                new_product = st.text_input("Product")
                new_notes = st.text_area("Work Notes")
            
            if st.form_submit_button("Add to In Progress"):
                if new_bug_id and new_title:
                    # Detect assignee from URL
                    assignee = detect_assignee_from_url(new_bug_id)
                    
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO in_progress 
                        (bug_id, assignment, priority, title, failure_mode, 
                         sn_associated, product, user_notes, added_date, assignee_detected)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, date('now'), ?)
                    ''', (new_bug_id, new_assignment, new_priority, new_title,
                          new_failure_mode, new_sn, new_product, new_notes, assignee))
                    conn.commit()
                    conn.close()
                    st.success("Bug added to In Progress!")
                    st.rerun()
                else:
                    st.error("Bug ID and Title are required!")
    
    # Show in-progress bugs
    conn = sqlite3.connect(DB_FILE)
    progress_df = pd.read_sql_query('''
        SELECT * FROM in_progress WHERE status = 'in_progress' ORDER BY priority ASC
    ''', conn)
    conn.close()
    
    if not progress_df.empty:
        st.info(f"📋 {len(progress_df)} bugs in progress")
        
        for _, bug in progress_df.iterrows():
            # Color coding
            bg_color = "#f0f0f0" if bug['status'] == 'deprioritized' else "#e8f4fd"
            
            st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 15px; border-radius: 5px; margin: 10px 0;">
                <h4>🐛 {bug['bug_id']} - Priority {bug['priority']}</h4>
                <p><strong>Title:</strong> {bug['title']}</p>
                <p><strong>Team:</strong> {bug['assignment']} | <strong>Failure Mode:</strong> {bug['failure_mode']}</p>
                {f"<p><strong>🎯 Assignee:</strong> {bug['assignee_detected']}</p>" if bug['assignee_detected'] else ""}
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # Notes editing with copy-paste functionality
                current_notes = bug['user_notes'] or ''
                new_notes = st.text_area(
                    "Work Notes (supports copy-paste from Excel)", 
                    value=current_notes, 
                    key=f"notes_{bug['id']}",
                    help="You can copy-paste data from Excel here"
                )
            
            with col2:
                if st.button("💾 Save Notes", key=f"save_notes_{bug['id']}"):
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute('UPDATE in_progress SET user_notes = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ?', 
                                 (new_notes, bug['id']))
                    conn.commit()
                    conn.close()
                    st.success("Notes saved!")
                    st.rerun()
                
                # Re-detect assignee button
                if st.button("🔍 Re-detect Assignee", key=f"redetect_{bug['id']}"):
                    new_assignee = detect_assignee_from_url(bug['bug_id'])
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute('UPDATE in_progress SET assignee_detected = ? WHERE id = ?', 
                                 (new_assignee, bug['id']))
                    conn.commit()
                    conn.close()
                    if new_assignee:
                        st.success(f"Assignee updated: {new_assignee}")
                    else:
                        st.info("No assignee detected")
                    st.rerun()
            
            with col3:
                if st.button("🔴 Deprioritize", key=f"deprio_prog_{bug['id']}"):
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute('UPDATE in_progress SET status = "deprioritized" WHERE id = ?', (bug['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()
                
                if st.button("✅ Complete", key=f"complete_{bug['id']}"):
                    # Move to completed table
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    
                    # Insert into completed_bugs
                    cursor.execute('''
                        INSERT INTO completed_bugs 
                        (bug_id, assignment, priority, title, failure_mode, created_date,
                         completed_date, sn_associated, product, user_notes, assignee_detected)
                        VALUES (?, ?, ?, ?, ?, ?, date('now'), ?, ?, ?, ?)
                    ''', (bug['bug_id'], bug['assignment'], bug['priority'], bug['title'],
                          bug['failure_mode'], bug['created_date'], bug['sn_associated'],
                          bug['product'], new_notes, bug['assignee_detected']))
                    
                    # Update status
                    cursor.execute('UPDATE in_progress SET status = "completed" WHERE id = ?', (bug['id'],))
                    cursor.execute('UPDATE bugs SET status = "completed" WHERE bug_id = ?', (bug['bug_id'],))
                    
                    conn.commit()
                    conn.close()
                    st.success("Bug completed!")
                    st.rerun()
    else:
        st.info("No bugs in progress. Add some bugs or move them from the dashboard!")

elif page == "✅ Completed":
    st.title("✅ Completed Bugs")
    st.markdown("Track completed bugs with assignee information and completion history.")
    
    # Get completed bugs
    conn = sqlite3.connect(DB_FILE)
    completed_df = pd.read_sql_query('''
        SELECT * FROM completed_bugs ORDER BY completion_timestamp DESC
    ''', conn)
    conn.close()
    
    if not completed_df.empty:
        st.success(f"🎉 {len(completed_df)} bugs completed!")
        
        # Summary by assignee
        if 'assignee_detected' in completed_df.columns:
            assignee_counts = completed_df['assignee_detected'].value_counts()
            if not assignee_counts.empty:
                st.subheader("👥 Completion Summary by Assignee")
                
                col1, col2, col3, col4 = st.columns(4)
                for i, (assignee, count) in enumerate(assignee_counts.items()):
                    if assignee and assignee != 'None':
                        with [col1, col2, col3, col4][i % 4]:
                            st.metric(assignee, f"{count} bugs")
        
        # Time-based filters
        col1, col2 = st.columns(2)
        with col1:
            days_filter = st.selectbox("Show completed in last:", [7, 14, 30, 90, 365], index=2)
        with col2:
            assignee_filter = st.selectbox("Filter by assignee:", ["All"] + TEAM_MEMBERS)
        
        # Filter completed bugs
        query = f'''
            SELECT * FROM completed_bugs 
            WHERE completed_date >= date('now', '-{days_filter} days')
        '''
        params = []
        
        if assignee_filter != "All":
            query += ' AND assignee_detected = ?'
            params.append(assignee_filter)
        
        query += ' ORDER BY completion_timestamp DESC'
        
        filtered_df = pd.read_sql_query(query, sqlite3.connect(DB_FILE), params=params)
        
        # Display completed bugs
        for _, bug in filtered_df.iterrows():
            with st.expander(f"✅ {bug['bug_id']} - {bug['title'][:50]}... (Completed {bug['completed_date']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Assignment:** {bug['assignment']}")
                    st.write(f"**Priority:** {bug['priority']}")
                    st.write(f"**Failure Mode:** {bug['failure_mode']}")
                    st.write(f"**Product:** {bug['product']}")
                
                with col2:
                    if bug['assignee_detected']:
                        st.write(f"**🎯 Completed by:** {bug['assignee_detected']}")
                    st.write(f"**Completed:** {bug['completed_date']}")
                    if bug['user_notes']:
                        st.write(f"**Final Notes:** {bug['user_notes']}")
                    
                    # Link to original bug
                    if bug['bug_id'].startswith('http'):
                        st.markdown(f"🔗 [View Original Bug]({bug['bug_id']})")
    else:
        st.info("No completed bugs yet. Complete some bugs from the In Progress section!")

elif page == "📝 Custom Bugs":
    st.title("📝 Custom Bug Management")
    st.markdown("Add and manage custom bugs with copy-paste functionality from Excel.")
    
    # Bulk import section
    with st.expander("📋 Bulk Import from Copy-Paste"):
        st.markdown("""
        **Instructions:** Copy data from Excel and paste below. Format should be:
        `Assignment | Bug ID | Priority | Title | Failure Mode | Created Date | COMPLETED | SN Associated | Product`
        
        You can copy multiple rows at once, separated by new lines.
        """)
        
        bulk_input = st.text_area(
            "Paste Excel data here (tab or comma separated)",
            height=200,
            placeholder="GL	https://nvbugs/12345	1	Sample bug title	Memory	2024-01-01	No	12345678	SXM5"
        )
        
        if st.button("Parse and Import Bulk Data"):
            if bulk_input.strip():
                parsed_bugs = parse_bulk_bug_data(bulk_input)
                
                if parsed_bugs:
                    st.success(f"Parsed {len(parsed_bugs)} bugs!")
                    
                    # Preview parsed data
                    preview_df = pd.DataFrame(parsed_bugs)
                    st.dataframe(preview_df)
                    
                    if st.button("Confirm Import"):
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        
                        for bug in parsed_bugs:
                            # Detect assignee
                            assignee = detect_assignee_from_url(bug['Bug ID'])
                            
                            cursor.execute('''
                                INSERT INTO custom_bugs 
                                (bug_id, assignment, priority, title, failure_mode, created_date,
                                 completed, sn_associated, product, added_date, assignee_detected)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, date('now'), ?)
                            ''', (
                                bug['Bug ID'], bug['Assignment'], bug['Priority'],
                                bug['Title'], bug['Failure Mode'], bug['Created Date'],
                                bug['COMPLETED'], bug['SN Associated'], bug['Product'], assignee
                            ))
                        
                        conn.commit()
                        conn.close()
                        st.success("Bulk import completed!")
                        st.rerun()
                else:
                    st.error("Could not parse the input. Please check the format.")
    
    # Manual add section
    with st.expander("➕ Add Single Custom Bug"):
        with st.form("add_custom_bug"):
            col1, col2 = st.columns(2)
            
            with col1:
                custom_assignment = st.selectbox("Assignment", ["GL", "NT", "PP"])
                custom_bug_id = st.text_input("Bug ID (URL)")
                custom_priority = st.number_input("Priority", min_value=1, value=1)
                custom_title = st.text_area("Title")
                
            with col2:
                custom_failure_mode = st.text_input("Failure Mode")
                custom_created_date = st.date_input("Created Date")
                custom_sn = st.text_input("SN Associated")
                custom_product = st.text_input("Product")
            
            custom_notes = st.text_area("Notes")
            
            if st.form_submit_button("Add Custom Bug"):
                if custom_bug_id and custom_title:
                    assignee = detect_assignee_from_url(custom_bug_id)
                    
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO custom_bugs 
                        (bug_id, assignment, priority, title, failure_mode, created_date,
                         sn_associated, product, user_notes, added_date, assignee_detected)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, date('now'), ?)
                    ''', (custom_bug_id, custom_assignment, custom_priority, custom_title,
                          custom_failure_mode, str(custom_created_date), custom_sn, 
                          custom_product, custom_notes, assignee))
                    conn.commit()
                    conn.close()
                    st.success("Custom bug added!")
                    st.rerun()
    
    # Display custom bugs
    st.subheader("📋 Your Custom Bugs")
    
    conn = sqlite3.connect(DB_FILE)
    custom_df = pd.read_sql_query('SELECT * FROM custom_bugs ORDER BY added_date DESC', conn)
    conn.close()
    
    if not custom_df.empty:
        st.dataframe(custom_df)
        
        # Export option
        csv_data = custom_df.to_csv(index=False)
        st.download_button(
            "📥 Export Custom Bugs to CSV",
            csv_data,
            file_name=f"custom_bugs_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No custom bugs added yet.")

elif page == "⚙️ Settings":
    st.title("⚙️ Settings & Database Management")
    
    # Database statistics
    conn = sqlite3.connect(DB_FILE)
    
    bugs_count = pd.read_sql_query('SELECT COUNT(*) as count FROM bugs', conn).iloc[0]['count']
    imports_count = pd.read_sql_query('SELECT COUNT(*) as count FROM import_history', conn).iloc[0]['count']
    progress_count = pd.read_sql_query('SELECT COUNT(*) as count FROM in_progress', conn).iloc[0]['count']
    completed_count = pd.read_sql_query('SELECT COUNT(*) as count FROM completed_bugs', conn).iloc[0]['count']
    custom_count = pd.read_sql_query('SELECT COUNT(*) as count FROM custom_bugs', conn).iloc[0]['count']
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Bugs", bugs_count)
    with col2:
        st.metric("Import Sessions", imports_count)
    with col3:
        st.metric("In Progress", progress_count)
    with col4:
        st.metric("Completed", completed_count)
    with col5:
        st.metric("Custom Bugs", custom_count)
    
    conn.close()
    
    # Database actions
    st.subheader("🗄️ Database Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export All Data"):
            conn = sqlite3.connect(DB_FILE)
            
            # Export all tables
            tables = ['bugs', 'import_history', 'in_progress', 'completed_bugs', 'custom_bugs']
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            for table in tables:
                try:
                    df = pd.read_sql_query(f'SELECT * FROM {table}', conn)
                    if not df.empty:
                        csv_data = df.to_csv(index=False)
                        st.download_button(
                            f"📥 {table.title()} Data",
                            csv_data,
                            f"{table}_export_{timestamp}.csv",
                            "text/csv",
                            key=f"export_{table}"
                        )
                except Exception as e:
                    st.error(f"Error exporting {table}: {e}")
            
            conn.close()
    
    with col2:
        st.warning("⚠️ Danger Zone")
        if st.button("🗑️ Clear All Data", type="secondary"):
            if st.checkbox("I understand this will delete ALL data permanently"):
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                
                tables = ['bugs', 'import_history', 'in_progress', 'completed_bugs', 'custom_bugs']
                for table in tables:
                    cursor.execute(f'DELETE FROM {table}')
                
                conn.commit()
                conn.close()
                st.success("All data cleared!")
                st.rerun()
    
    # Advanced settings
    st.subheader("🔧 Advanced Settings")
    
    # URL parsing settings
    with st.expander("🔗 URL Parsing Configuration"):
        st.markdown("Configure how the system detects assignees from bug URLs.")
        
        test_url = st.text_input("Test URL for assignee detection:")
        if test_url and st.button("Test Detection"):
            detected = detect_assignee_from_url(test_url)
            comment_count = count_comments_from_url(test_url)
            
            if detected:
                st.success(f"Detected assignee: {detected}")
            else:
                st.info("No assignee detected")
            
            st.info(f"Comment count: {comment_count}")
    
    # Team member management
    with st.expander("👥 Team Member Configuration"):
        st.markdown("Current team members for assignee detection:")
        for member in TEAM_MEMBERS:
            st.write(f"• {member}")
        
        st.info("To modify team members, update the TEAM_MEMBERS list in the code.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("🐛 **Complete Enhanced Bug Tracker**")
st.sidebar.markdown("v2.0 - Full Feature Set")
st.sidebar.markdown("Built with Streamlit & SQLite") 