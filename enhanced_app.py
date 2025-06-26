#!/usr/bin/env python3
"""
Enhanced Bug Assignment Processor with Database & Historical Tracking
Features: SQLite persistence, historical views, interactive management
"""

import streamlit as st
import pandas as pd
import sqlite3
import os
import tempfile
from datetime import datetime, timedelta
import json

# Import from existing modules
from offline_processor import (
    is_cqe_file, 
    process_single_cqe_file,
    create_team_sheets_email_html
)

# Database setup
DB_FILE = "bug_tracker.db"

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Main bugs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bugs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Import history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS import_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_date DATE,
            total_bugs INTEGER,
            new_bugs INTEGER,
            updated_bugs INTEGER,
            html_report TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # In-progress bugs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS in_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            assignee_detected TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def detect_assignee(bug_id):
    """Detect assignee from bug URL - placeholder implementation"""
    team_members = ["Nicolas Tan", "Geethalakshmi Sundaresan", "Phuong Pham", "Jack Gong"]
    # In real implementation, you'd scrape the bug URL
    # For now, return None as placeholder
    return None

def save_bugs_to_db(df, import_date=None):
    """Save bugs to database with duplicate handling"""
    if import_date is None:
        import_date = datetime.now().date()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    new_count = 0
    updated_count = 0
    
    for _, row in df.iterrows():
        bug_id = row.get('Bug ID', '')
        if not bug_id:
            continue
            
        # Check if bug exists
        cursor.execute('SELECT id, bug_age FROM bugs WHERE bug_id = ?', (bug_id,))
        existing = cursor.fetchone()
        
        assignee = detect_assignee(bug_id)
        
        if existing:
            # Update existing bug
            cursor.execute('''
                UPDATE bugs SET 
                assignment=?, priority=?, title=?, failure_mode=?, created_date=?,
                completed=?, sn_associated=?, product=?, import_date=?, 
                assignee_detected=?, last_updated=CURRENT_TIMESTAMP
                WHERE bug_id=?
            ''', (
                row.get('Assignment', ''), row.get('Priority', 0), row.get('Title', ''),
                row.get('Failure Mode', ''), row.get('Created Date', ''),
                row.get('COMPLETED', ''), row.get('SN Associated', ''),
                row.get('Product', ''), import_date, assignee, bug_id
            ))
            updated_count += 1
        else:
            # Insert new bug
            cursor.execute('''
                INSERT INTO bugs 
                (bug_id, assignment, priority, title, failure_mode, created_date,
                 completed, sn_associated, product, import_date, assignee_detected)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                bug_id, row.get('Assignment', ''), row.get('Priority', 0),
                row.get('Title', ''), row.get('Failure Mode', ''),
                row.get('Created Date', ''), row.get('COMPLETED', ''),
                row.get('SN Associated', ''), row.get('Product', ''),
                import_date, assignee
            ))
            new_count += 1
    
    conn.commit()
    conn.close()
    return new_count, updated_count

# Initialize database
init_database()

# Streamlit app
st.set_page_config(
    page_title="Enhanced Bug Tracker",
    page_icon="🐛",
    layout="wide"
)

# Sidebar navigation
st.sidebar.title("🐛 Enhanced Bug Tracker")
page = st.sidebar.radio(
    "Navigation",
    ["📥 Import Bugs", "📊 Dashboard", "📅 History", "🔄 In Progress", "✅ Completed"]
)

if page == "📥 Import Bugs":
    st.title("📥 Import CQE Bugs")
    
    uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx', 'xls'])
    
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            tmp.write(uploaded_file.getvalue())
            temp_path = tmp.name
        
        try:
            if is_cqe_file(temp_path):
                st.info("🔍 CQE file detected")
                
                if st.button("Process File", type="primary"):
                    with st.spinner("Processing..."):
                        output_file = process_single_cqe_file(temp_path)
                        
                        if output_file and os.path.exists(output_file):
                            # Read processed data
                            import openpyxl
                            wb = openpyxl.load_workbook(output_file)
                            sheet = wb['Daily New']
                            
                            # Convert to DataFrame
                            data = []
                            headers = [cell.value for cell in sheet[1]]
                            for row in sheet.iter_rows(min_row=2, values_only=True):
                                if any(row):
                                    data.append(row)
                            
                            df = pd.DataFrame(data, columns=headers)
                            wb.close()
                            
                            # Save to database
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
                            
                            st.success("✅ Import successful!")
                            st.info(f"Total: {len(df)} | New: {new_bugs} | Updated: {updated_bugs}")
                            
                            # Download options
                            col1, col2 = st.columns(2)
                            with col1:
                                with open(output_file, 'rb') as f:
                                    st.download_button(
                                        "📥 Download Excel",
                                        f.read(),
                                        file_name=f"processed_{datetime.now().strftime('%Y%m%d')}.xlsx"
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
                st.warning("File format not recognized as CQE file")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

elif page == "📊 Dashboard":
    st.title("📊 Current Bug Dashboard")
    
    # Get active bugs
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query('''
        SELECT * FROM bugs WHERE status = 'active' 
        ORDER BY priority ASC, last_updated DESC
    ''', conn)
    conn.close()
    
    if not df.empty:
        st.info(f"📋 {len(df)} active bugs")
        
        # Interactive bug management
        for idx, bug in df.iterrows():
            with st.expander(f"🐛 {bug['bug_id']} - P{bug['priority']} - {bug['title'][:60]}..."):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Team:** {bug['assignment']}")
                    st.write(f"**Failure Mode:** {bug['failure_mode']}")
                    st.write(f"**Product:** {bug['product']}")
                    st.write(f"**Age:** {bug['bug_age'].replace('_', ' ').title()}")
                
                with col2:
                    # Bug age selector
                    age_options = ['brand_new', 'existing_untouched', 
                                 'existing_one_comment', 'existing_multiple_comments']
                    current_age_idx = age_options.index(bug['bug_age']) if bug['bug_age'] in age_options else 0
                    
                    new_age = st.selectbox(
                        "Bug Age",
                        age_options,
                        index=current_age_idx,
                        key=f"age_{bug['id']}"
                    )
                    
                    if new_age != bug['bug_age']:
                        if st.button("Update Age", key=f"update_age_{bug['id']}"):
                            conn = sqlite3.connect(DB_FILE)
                            cursor = conn.cursor()
                            cursor.execute('UPDATE bugs SET bug_age = ? WHERE id = ?', (new_age, bug['id']))
                            conn.commit()
                            conn.close()
                            st.success("Updated!")
                            st.rerun()
                
                with col3:
                    # Action buttons
                    if st.button("🔄 In Progress", key=f"progress_{bug['id']}"):
                        # Move to in-progress
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        
                        # Insert into in_progress table
                        cursor.execute('''
                            INSERT INTO in_progress 
                            (bug_id, assignment, priority, title, failure_mode, created_date,
                             completed, sn_associated, product, added_date, assignee_detected)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, date('now'), ?)
                        ''', (bug['bug_id'], bug['assignment'], bug['priority'], bug['title'],
                              bug['failure_mode'], bug['created_date'], bug['completed'],
                              bug['sn_associated'], bug['product'], bug['assignee_detected']))
                        
                        # Update main table
                        cursor.execute('UPDATE bugs SET status = ? WHERE id = ?', ('in_progress', bug['id']))
                        conn.commit()
                        conn.close()
                        st.success("Moved to In Progress!")
                        st.rerun()
                    
                    if st.button("⏸️ Deprioritize", key=f"deprio_{bug['id']}"):
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute('UPDATE bugs SET status = ? WHERE id = ?', ('deprioritized', bug['id']))
                        conn.commit()
                        conn.close()
                        st.success("Deprioritized!")
                        st.rerun()
    else:
        st.info("No active bugs. Import some data to get started!")

elif page == "📅 History":
    st.title("📅 Historical Bug Reports")
    
    days_back = st.slider("Days to show", 1, 30, 7)
    
    conn = sqlite3.connect(DB_FILE)
    history_df = pd.read_sql_query('''
        SELECT * FROM import_history 
        WHERE import_date >= date('now', '-{} days')
        ORDER BY import_date DESC
    '''.format(days_back), conn)
    conn.close()
    
    if not history_df.empty:
        for _, record in history_df.iterrows():
            with st.expander(f"📅 {record['import_date']} - {record['total_bugs']} bugs"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total", record['total_bugs'])
                with col2:
                    st.metric("New", record['new_bugs'])
                with col3:
                    st.metric("Updated", record['updated_bugs'])
                
                if record['html_report']:
                    st.subheader("HTML Report")
                    st.components.v1.html(record['html_report'], height=500, scrolling=True)
                    
                    st.download_button(
                        "Download Report",
                        record['html_report'],
                        file_name=f"report_{record['import_date']}.html",
                        mime="text/html",
                        key=f"dl_{record['id']}"
                    )
    else:
        st.info("No historical data found")

elif page == "🔄 In Progress":
    st.title("🔄 In Progress Bugs")
    
    # Add new bug form
    with st.expander("➕ Add New Bug"):
        with st.form("new_bug"):
            col1, col2 = st.columns(2)
            with col1:
                bug_id = st.text_input("Bug ID")
                assignment = st.selectbox("Team", ["GL", "NT", "PP"])
                priority = st.number_input("Priority", min_value=1, value=1)
                title = st.text_area("Title")
            with col2:
                failure_mode = st.text_input("Failure Mode")
                sn = st.text_input("SN Associated")
                product = st.text_input("Product")
                notes = st.text_area("Notes")
            
            if st.form_submit_button("Add Bug"):
                if bug_id and title:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO in_progress 
                        (bug_id, assignment, priority, title, failure_mode,
                         sn_associated, product, user_notes, added_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, date('now'))
                    ''', (bug_id, assignment, priority, title, failure_mode, sn, product, notes))
                    conn.commit()
                    conn.close()
                    st.success("Bug added!")
                    st.rerun()
    
    # Show in-progress bugs
    conn = sqlite3.connect(DB_FILE)
    progress_df = pd.read_sql_query('''
        SELECT * FROM in_progress WHERE status = 'in_progress' ORDER BY priority
    ''', conn)
    conn.close()
    
    if not progress_df.empty:
        for idx, bug in progress_df.iterrows():
            with st.container():
                st.markdown(f"""
                <div style="background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <h4>🐛 {bug['bug_id']} - Priority {bug['priority']}</h4>
                    <p><strong>Title:</strong> {bug['title']}</p>
                    <p><strong>Team:</strong> {bug['assignment']} | <strong>Failure Mode:</strong> {bug['failure_mode']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    # Notes editing
                    current_notes = bug['user_notes'] or ''
                    new_notes = st.text_area("Notes", value=current_notes, key=f"notes_{bug['id']}")
                
                with col2:
                    if st.button("💾 Save Notes", key=f"save_{bug['id']}"):
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute('UPDATE in_progress SET user_notes = ? WHERE id = ?', 
                                     (new_notes, bug['id']))
                        conn.commit()
                        conn.close()
                        st.success("Saved!")
                        st.rerun()
                
                with col3:
                    if st.button("🔴 Deprioritize", key=f"deprio_p_{bug['id']}"):
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute('UPDATE in_progress SET status = ? WHERE id = ?', 
                                     ('deprioritized', bug['id']))
                        conn.commit()
                        conn.close()
                        st.rerun()
                    
                    if st.button("✅ Complete", key=f"complete_{bug['id']}"):
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute('UPDATE in_progress SET status = ? WHERE id = ?', 
                                     ('completed', bug['id']))
                        conn.commit()
                        conn.close()
                        st.success("Completed!")
                        st.rerun()
    else:
        st.info("No bugs in progress")

elif page == "✅ Completed":
    st.title("✅ Completed Bugs")
    
    conn = sqlite3.connect(DB_FILE)
    completed_df = pd.read_sql_query('''
        SELECT * FROM in_progress WHERE status = 'completed' ORDER BY id DESC
    ''', conn)
    conn.close()
    
    if not completed_df.empty:
        st.success(f"🎉 {len(completed_df)} bugs completed!")
        
        # Show completed bugs
        for idx, bug in completed_df.iterrows():
            with st.expander(f"✅ {bug['bug_id']} - {bug['title'][:50]}... (Completed)"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Team:** {bug['assignment']}")
                    st.write(f"**Priority:** {bug['priority']}")
                    st.write(f"**Failure Mode:** {bug['failure_mode']}")
                with col2:
                    if bug['assignee_detected']:
                        st.write(f"**Completed by:** {bug['assignee_detected']}")
                    st.write(f"**Added:** {bug['added_date']}")
                    if bug['user_notes']:
                        st.write(f"**Notes:** {bug['user_notes']}")
    else:
        st.info("No completed bugs yet")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("Enhanced Bug Tracker v2.0") 