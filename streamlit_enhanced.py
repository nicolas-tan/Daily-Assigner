#!/usr/bin/env python3
"""
Enhanced Streamlit App for Bug Assignment Processor with Database Persistence
Features: Historical tracking, interactive bug management, status updates
"""

import streamlit as st
import pandas as pd
import sqlite3
import os
import tempfile
from datetime import datetime, timedelta
import json
import requests
from urllib.parse import urlparse, parse_qs
import re
from offline_processor import (
    is_cqe_file, 
    process_single_cqe_file,
    create_blank_excel_template,
    create_team_sheets_email_html
)

# Database setup
DB_FILE = "bug_tracker.db"

def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Bugs table - stores all processed bugs with history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bugs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bug_id TEXT NOT NULL,
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
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            assignee_detected TEXT,
            comment_count INTEGER DEFAULT 0,
            bug_age TEXT DEFAULT 'brand_new'
        )
    ''')
    
    # Daily imports table - tracks each import session
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_imports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_date DATE,
            import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_bugs INTEGER,
            new_bugs INTEGER,
            updated_bugs INTEGER,
            html_report TEXT,
            excel_data BLOB
        )
    ''')
    
    # User interactions table - tracks manual status changes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bug_id TEXT,
            action TEXT,
            old_status TEXT,
            new_status TEXT,
            user_notes TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # In progress bugs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS in_progress_bugs (
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
            added_date DATE,
            user_notes TEXT,
            assignee_detected TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def detect_assignee_from_bug_url(bug_id):
    """Detect assignee from bug URL content by checking for team member names"""
    team_members = [
        "Nicolas Tan", "Geethalakshmi Sundaresan", "Phuong Pham", "Jack Gong"
    ]
    
    if not bug_id or not isinstance(bug_id, str) or not bug_id.startswith('https://'):
        return None
    
    try:
        # This is a placeholder - in real implementation you'd need to:
        # 1. Make HTTP request to the bug URL
        # 2. Parse the HTML content
        # 3. Search for team member names
        # For now, we'll simulate this
        
        # Simulate checking URL content (replace with actual implementation)
        # response = requests.get(bug_id, timeout=10)
        # content = response.text.lower()
        
        # For demonstration, we'll use a simple heuristic
        for member in team_members:
            # In real implementation, search in the actual bug page content
            # if member.lower() in content:
            #     return member
            pass
            
        return None
    except Exception:
        return None

def count_comments_from_bug_url(bug_id):
    """Count comments from team members in bug URL"""
    # Placeholder implementation
    # In real version, you'd parse the bug page and count comments
    return 0

def save_bugs_to_database(bugs_df, import_date=None):
    """Save processed bugs to database with duplicate handling"""
    if import_date is None:
        import_date = datetime.now().date()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    new_bugs = 0
    updated_bugs = 0
    
    for _, bug in bugs_df.iterrows():
        bug_id = bug.get('Bug ID', '')
        
        # Check if bug already exists
        cursor.execute('SELECT id, bug_age FROM bugs WHERE bug_id = ?', (bug_id,))
        existing = cursor.fetchone()
        
        # Detect assignee and comment count
        assignee = detect_assignee_from_bug_url(bug_id)
        comment_count = count_comments_from_bug_url(bug_id)
        
        # Determine bug age
        if existing:
            bug_age = existing[1]  # Keep existing age
            if comment_count > 0:
                if comment_count >= 2:
                    bug_age = 'existing_multiple_comments'
                else:
                    bug_age = 'existing_one_comment'
            else:
                bug_age = 'existing_untouched'
            updated_bugs += 1
        else:
            bug_age = 'brand_new'
            new_bugs += 1
        
        # Insert or update bug
        cursor.execute('''
            INSERT OR REPLACE INTO bugs 
            (bug_id, assignment, priority, title, failure_mode, created_date, 
             completed, sn_associated, product, import_date, assignee_detected, 
             comment_count, bug_age, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            bug_id,
            bug.get('Assignment', ''),
            bug.get('Priority', 0),
            bug.get('Title', ''),
            bug.get('Failure Mode', ''),
            bug.get('Created Date', ''),
            bug.get('COMPLETED', ''),
            bug.get('SN Associated', ''),
            bug.get('Product', ''),
            import_date,
            assignee,
            comment_count,
            bug_age
        ))
    
    conn.commit()
    conn.close()
    
    return new_bugs, updated_bugs

def get_historical_data(days_back=30):
    """Get historical bug data"""
    conn = sqlite3.connect(DB_FILE)
    
    # Get daily imports
    imports_df = pd.read_sql_query('''
        SELECT import_date, total_bugs, new_bugs, updated_bugs, html_report
        FROM daily_imports 
        WHERE import_date >= date('now', '-{} days')
        ORDER BY import_date DESC
    '''.format(days_back), conn)
    
    conn.close()
    return imports_df

def get_bugs_by_status(status='active'):
    """Get bugs by status"""
    conn = sqlite3.connect(DB_FILE)
    
    df = pd.read_sql_query('''
        SELECT * FROM bugs 
        WHERE status = ? 
        ORDER BY priority ASC, last_updated DESC
    ''', conn, params=(status,))
    
    conn.close()
    return df

def update_bug_status(bug_id, new_status, user_notes=''):
    """Update bug status with user interaction tracking"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Get current status
    cursor.execute('SELECT status FROM bugs WHERE bug_id = ?', (bug_id,))
    result = cursor.fetchone()
    old_status = result[0] if result else 'unknown'
    
    # Update bug status
    cursor.execute('''
        UPDATE bugs 
        SET status = ?, last_updated = CURRENT_TIMESTAMP 
        WHERE bug_id = ?
    ''', (new_status, bug_id))
    
    # Log user interaction
    cursor.execute('''
        INSERT INTO user_interactions 
        (bug_id, action, old_status, new_status, user_notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (bug_id, 'status_change', old_status, new_status, user_notes))
    
    conn.commit()
    conn.close()

# Initialize database
init_database()

# Set page config
st.set_page_config(
    page_title="Enhanced Bug Assignment Processor",
    page_icon="🐛",
    layout="wide"
)

# Sidebar navigation
st.sidebar.title("🐛 Bug Tracker")
page = st.sidebar.selectbox(
    "Navigate",
    ["📥 Import New Bugs", "📊 Current Dashboard", "📅 Historical View", 
     "🔄 In Progress", "✅ Completed", "⚙️ Settings"]
)

if page == "📥 Import New Bugs":
    st.title("📥 Import New CQE Bugs")
    st.markdown("Upload your CQE Excel file to process and store bugs with historical tracking.")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose an Excel file",
        type=['xlsx', 'xls'],
        help="Upload either a CQE bugs file or a properly formatted bug assignment file"
    )
    
    if uploaded_file is not None:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            temp_path = tmp_file.name
        
        try:
            # Check if it's a CQE file
            if is_cqe_file(temp_path):
                st.info("📊 Detected CQE file format - will create proper structure and process")
                
                if st.button("Process CQE File", type="primary"):
                    with st.spinner("Processing CQE file..."):
                        # Process the file
                        output_file = process_single_cqe_file(temp_path)
                        
                        if output_file and os.path.exists(output_file):
                            # Read processed data
                            import openpyxl
                            wb = openpyxl.load_workbook(output_file)
                            daily_sheet = wb['Daily New']
                            
                            # Convert to DataFrame
                            data = []
                            headers = [cell.value for cell in daily_sheet[1]]
                            for row in daily_sheet.iter_rows(min_row=2, values_only=True):
                                if any(row):  # Skip empty rows
                                    data.append(row)
                            
                            bugs_df = pd.DataFrame(data, columns=headers)
                            wb.close()
                            
                            # Save to database
                            new_bugs, updated_bugs = save_bugs_to_database(bugs_df)
                            
                            # Generate HTML report
                            html_content = create_team_sheets_email_html(output_file)
                            
                            # Save import session
                            conn = sqlite3.connect(DB_FILE)
                            cursor = conn.cursor()
                            cursor.execute('''
                                INSERT INTO daily_imports 
                                (import_date, total_bugs, new_bugs, updated_bugs, html_report)
                                VALUES (date('now'), ?, ?, ?, ?)
                            ''', (len(bugs_df), new_bugs, updated_bugs, html_content))
                            conn.commit()
                            conn.close()
                            
                            st.success("✅ Processing completed successfully!")
                            st.info(f"📊 **Import Summary:**\n- Total bugs: {len(bugs_df)}\n- New bugs: {new_bugs}\n- Updated bugs: {updated_bugs}")
                            
                            # Download options
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                with open(output_file, 'rb') as f:
                                    processed_data = f.read()
                                st.download_button(
                                    label="📥 Download Processed Excel File",
                                    data=processed_data,
                                    file_name=os.path.basename(output_file),
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                            
                            with col2:
                                st.download_button(
                                    label="📄 Download HTML Report",
                                    data=html_content,
                                    file_name=f"bug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                                    mime="text/html"
                                )
                            
                            # Clean up
                            os.remove(output_file)
                        else:
                            st.error("❌ Processing failed. Please check your file format.")
            
            else:
                st.info("📋 Detected properly formatted bug assignment file")
                st.warning("⚠️ Note: Processing files with existing structure is not yet implemented")
                
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

elif page == "📊 Current Dashboard":
    st.title("📊 Current Bug Dashboard")
    
    # Get current active bugs
    active_bugs = get_bugs_by_status('active')
    
    if not active_bugs.empty:
        st.info(f"📋 Showing {len(active_bugs)} active bugs")
        
        # Display bugs with interactive controls
        for idx, bug in active_bugs.iterrows():
            with st.expander(f"🐛 {bug['bug_id']} - Priority {bug['priority']} - {bug['title'][:50]}..."):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Assignment:** {bug['assignment']}")
                    st.write(f"**Failure Mode:** {bug['failure_mode']}")
                    st.write(f"**Product:** {bug['product']}")
                    st.write(f"**Bug Age:** {bug['bug_age'].replace('_', ' ').title()}")
                    if bug['assignee_detected']:
                        st.write(f"**Detected Assignee:** {bug['assignee_detected']}")
                
                with col2:
                    # Bug age dropdown
                    current_age = bug['bug_age']
                    new_age = st.selectbox(
                        "Bug Status",
                        ['brand_new', 'existing_untouched', 'existing_one_comment', 'existing_multiple_comments'],
                        index=['brand_new', 'existing_untouched', 'existing_one_comment', 'existing_multiple_comments'].index(current_age),
                        key=f"age_{bug['id']}"
                    )
                    
                    if new_age != current_age:
                        if st.button(f"Update Status", key=f"update_{bug['id']}"):
                            conn = sqlite3.connect(DB_FILE)
                            cursor = conn.cursor()
                            cursor.execute('UPDATE bugs SET bug_age = ? WHERE id = ?', (new_age, bug['id']))
                            conn.commit()
                            conn.close()
                            st.success("Status updated!")
                            st.rerun()
                
                with col3:
                    # Action buttons
                    if st.button("🔄 Move to In Progress", key=f"progress_{bug['id']}"):
                        # Move to in_progress_bugs table
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO in_progress_bugs 
                            (bug_id, assignment, priority, title, failure_mode, created_date, 
                             completed, sn_associated, product, added_date, assignee_detected)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, date('now'), ?)
                        ''', (bug['bug_id'], bug['assignment'], bug['priority'], bug['title'],
                              bug['failure_mode'], bug['created_date'], bug['completed'],
                              bug['sn_associated'], bug['product'], bug['assignee_detected']))
                        
                        # Update main bugs table
                        cursor.execute('UPDATE bugs SET status = ? WHERE id = ?', ('in_progress', bug['id']))
                        conn.commit()
                        conn.close()
                        
                        st.success("Moved to In Progress!")
                        st.rerun()
                    
                    if st.button("⏸️ Deprioritize", key=f"deprio_{bug['id']}"):
                        update_bug_status(bug['bug_id'], 'deprioritized')
                        st.success("Bug deprioritized!")
                        st.rerun()
    else:
        st.info("No active bugs found. Import some bugs to get started!")

elif page == "📅 Historical View":
    st.title("📅 Historical Bug Reports")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        days_back = st.slider("Days to look back", 1, 30, 7)
    
    # Get historical data
    historical_data = get_historical_data(days_back)
    
    if not historical_data.empty:
        st.subheader("📊 Import History")
        
        for _, import_record in historical_data.iterrows():
            with st.expander(f"📅 {import_record['import_date']} - {import_record['total_bugs']} bugs"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Bugs", import_record['total_bugs'])
                with col2:
                    st.metric("New Bugs", import_record['new_bugs'])
                with col3:
                    st.metric("Updated Bugs", import_record['updated_bugs'])
                
                # Show HTML report if available
                if import_record['html_report']:
                    st.subheader("📄 HTML Report")
                    st.components.v1.html(import_record['html_report'], height=600, scrolling=True)
                    
                    # Download option
                    st.download_button(
                        label="📥 Download HTML Report",
                        data=import_record['html_report'],
                        file_name=f"bug_report_{import_record['import_date']}.html",
                        mime="text/html",
                        key=f"download_{import_record['import_date']}"
                    )
    else:
        st.info("No historical data found.")

elif page == "🔄 In Progress":
    st.title("🔄 In Progress Bugs")
    
    # Get in-progress bugs
    conn = sqlite3.connect(DB_FILE)
    in_progress_df = pd.read_sql_query('''
        SELECT * FROM in_progress_bugs 
        WHERE status = 'in_progress'
        ORDER BY priority ASC
    ''', conn)
    conn.close()
    
    # Add new bug section
    with st.expander("➕ Add New Bug to In Progress"):
        with st.form("add_bug_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_bug_id = st.text_input("Bug ID")
                new_assignment = st.selectbox("Assignment", ["GL", "NT", "PP"])
                new_priority = st.number_input("Priority", min_value=1, value=1)
                new_title = st.text_area("Title")
                
            with col2:
                new_failure_mode = st.text_input("Failure Mode")
                new_sn = st.text_input("SN Associated")
                new_product = st.text_input("Product")
                new_notes = st.text_area("Notes")
            
            if st.form_submit_button("Add Bug"):
                if new_bug_id and new_title:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO in_progress_bugs 
                        (bug_id, assignment, priority, title, failure_mode, 
                         sn_associated, product, added_date, user_notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, date('now'), ?)
                    ''', (new_bug_id, new_assignment, new_priority, new_title,
                          new_failure_mode, new_sn, new_product, new_notes))
                    conn.commit()
                    conn.close()
                    st.success("Bug added to In Progress!")
                    st.rerun()
                else:
                    st.error("Bug ID and Title are required!")
    
    # Display in-progress bugs
    if not in_progress_df.empty:
        st.info(f"📋 Showing {len(in_progress_df)} in-progress bugs")
        
        for idx, bug in in_progress_df.iterrows():
            # Color coding based on status
            if bug['status'] == 'deprioritized':
                st.markdown(f'<div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin: 5px 0;">', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="background-color: #e8f4fd; padding: 10px; border-radius: 5px; margin: 5px 0;">', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**🐛 {bug['bug_id']}** - Priority {bug['priority']}")
                st.write(f"**Title:** {bug['title']}")
                st.write(f"**Assignment:** {bug['assignment']} | **Failure Mode:** {bug['failure_mode']}")
                if bug['user_notes']:
                    st.write(f"**Notes:** {bug['user_notes']}")
            
            with col2:
                # Edit notes
                new_notes = st.text_area("Update Notes", value=bug['user_notes'] or '', key=f"notes_{bug['id']}")
                if st.button("💾 Save Notes", key=f"save_notes_{bug['id']}"):
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute('UPDATE in_progress_bugs SET user_notes = ? WHERE id = ?', (new_notes, bug['id']))
                    conn.commit()
                    conn.close()
                    st.success("Notes updated!")
                    st.rerun()
            
            with col3:
                # Action buttons
                if st.button("🔴 Deprioritize", key=f"deprio_prog_{bug['id']}"):
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute('UPDATE in_progress_bugs SET status = ? WHERE id = ?', ('deprioritized', bug['id']))
                    conn.commit()
                    conn.close()
                    st.rerun()
                
                if st.button("✅ Complete", key=f"complete_{bug['id']}"):
                    # Move to completed
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute('UPDATE in_progress_bugs SET status = ? WHERE id = ?', ('completed', bug['id']))
                    
                    # Also update main bugs table if exists
                    cursor.execute('UPDATE bugs SET status = ? WHERE bug_id = ?', ('completed', bug['bug_id']))
                    conn.commit()
                    conn.close()
                    st.success("Bug completed!")
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No bugs in progress. Add some bugs or move them from the dashboard!")

elif page == "✅ Completed":
    st.title("✅ Completed Bugs")
    
    # Get completed bugs
    conn = sqlite3.connect(DB_FILE)
    completed_df = pd.read_sql_query('''
        SELECT * FROM in_progress_bugs 
        WHERE status = 'completed'
        ORDER BY id DESC
    ''', conn)
    conn.close()
    
    if not completed_df.empty:
        st.success(f"🎉 {len(completed_df)} bugs completed!")
        
        # Summary by assignee
        if 'assignee_detected' in completed_df.columns:
            assignee_counts = completed_df['assignee_detected'].value_counts()
            if not assignee_counts.empty:
                st.subheader("👥 Completion Summary by Assignee")
                for assignee, count in assignee_counts.items():
                    if assignee and assignee != 'None':
                        st.write(f"**{assignee}:** {count} bugs")
        
        # Display completed bugs
        for idx, bug in completed_df.iterrows():
            with st.expander(f"✅ {bug['bug_id']} - {bug['title'][:50]}... (Completed)"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Assignment:** {bug['assignment']}")
                    st.write(f"**Priority:** {bug['priority']}")
                    st.write(f"**Failure Mode:** {bug['failure_mode']}")
                    st.write(f"**Product:** {bug['product']}")
                
                with col2:
                    if bug['assignee_detected']:
                        st.write(f"**Completed by:** {bug['assignee_detected']}")
                    st.write(f"**Added to Progress:** {bug['added_date']}")
                    if bug['user_notes']:
                        st.write(f"**Final Notes:** {bug['user_notes']}")
    else:
        st.info("No completed bugs yet. Complete some bugs from the In Progress section!")

elif page == "⚙️ Settings":
    st.title("⚙️ Settings & Database Management")
    
    # Database statistics
    conn = sqlite3.connect(DB_FILE)
    
    bugs_count = pd.read_sql_query('SELECT COUNT(*) as count FROM bugs', conn).iloc[0]['count']
    imports_count = pd.read_sql_query('SELECT COUNT(*) as count FROM daily_imports', conn).iloc[0]['count']
    interactions_count = pd.read_sql_query('SELECT COUNT(*) as count FROM user_interactions', conn).iloc[0]['count']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Bugs", bugs_count)
    with col2:
        st.metric("Import Sessions", imports_count)
    with col3:
        st.metric("User Interactions", interactions_count)
    
    conn.close()
    
    # Database actions
    st.subheader("🗄️ Database Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export All Data"):
            # Export all tables to CSV
            conn = sqlite3.connect(DB_FILE)
            
            bugs_df = pd.read_sql_query('SELECT * FROM bugs', conn)
            imports_df = pd.read_sql_query('SELECT * FROM daily_imports', conn)
            interactions_df = pd.read_sql_query('SELECT * FROM user_interactions', conn)
            
            conn.close()
            
            # Create downloadable files
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            st.download_button(
                "📥 Download Bugs Data",
                bugs_df.to_csv(index=False),
                f"bugs_export_{timestamp}.csv",
                "text/csv"
            )
            
            st.download_button(
                "📥 Download Import History",
                imports_df.to_csv(index=False),
                f"imports_export_{timestamp}.csv",
                "text/csv"
            )
    
    with col2:
        st.warning("⚠️ Danger Zone")
        if st.button("🗑️ Clear All Data", type="secondary"):
            if st.checkbox("I understand this will delete all data"):
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM bugs')
                cursor.execute('DELETE FROM daily_imports')
                cursor.execute('DELETE FROM user_interactions')
                cursor.execute('DELETE FROM in_progress_bugs')
                conn.commit()
                conn.close()
                st.success("All data cleared!")
                st.rerun()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("🐛 **Enhanced Bug Tracker**")
st.sidebar.markdown("Built with Streamlit & SQLite") 