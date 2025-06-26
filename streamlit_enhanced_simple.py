import streamlit as st
import pandas as pd
import sqlite3
import os
import tempfile
from datetime import datetime
from offline_processor import is_cqe_file, process_single_cqe_file, create_team_sheets_email_html

# Database setup
DB_FILE = "bugs.db"

def init_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bugs (
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
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS import_history (
            id INTEGER PRIMARY KEY,
            import_date DATE,
            total_bugs INTEGER,
            html_report TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def save_bugs_to_db(df):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    for _, row in df.iterrows():
        bug_id = row.get('Bug ID', '')
        if bug_id:
            cursor.execute('''
                INSERT OR REPLACE INTO bugs 
                (bug_id, assignment, priority, title, failure_mode, import_date)
                VALUES (?, ?, ?, ?, ?, date('now'))
            ''', (bug_id, row.get('Assignment', ''), row.get('Priority', 0),
                  row.get('Title', ''), row.get('Failure Mode', '')))
    
    conn.commit()
    conn.close()

init_database()

st.set_page_config(page_title="Enhanced Bug Tracker", layout="wide")

st.sidebar.title("🐛 Enhanced Bug Tracker")
page = st.sidebar.radio("Navigate", ["Import", "Dashboard", "History"])

if page == "Import":
    st.title("Import Bugs")
    
    uploaded_file = st.file_uploader("Upload Excel", type=['xlsx'])
    
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            tmp.write(uploaded_file.getvalue())
            temp_path = tmp.name
        
        if st.button("Process"):
            with st.spinner("Processing..."):
                output_file = process_single_cqe_file(temp_path)
                
                if output_file:
                    # Read data
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
                    
                    # Save to database
                    save_bugs_to_db(df)
                    
                    # Generate HTML
                    html_report = create_team_sheets_email_html(output_file)
                    
                    # Save history
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO import_history (import_date, total_bugs, html_report)
                        VALUES (date('now'), ?, ?)
                    ''', (len(df), html_report))
                    conn.commit()
                    conn.close()
                    
                    st.success(f"Imported {len(df)} bugs!")
                    
                    # Downloads
                    with open(output_file, 'rb') as f:
                        st.download_button("Download Excel", f.read(), "processed.xlsx")
                    
                    st.download_button("Download HTML", html_report, "report.html", mime="text/html")
                    
                    os.remove(output_file)
        
        os.remove(temp_path)

elif page == "Dashboard":
    st.title("Bug Dashboard")
    
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query('SELECT * FROM bugs WHERE status = "active" ORDER BY priority', conn)
    conn.close()
    
    if not df.empty:
        st.dataframe(df)
        
        for _, bug in df.iterrows():
            with st.expander(f"{bug['bug_id']} - {bug['title'][:50]}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"Team: {bug['assignment']}")
                    st.write(f"Priority: {bug['priority']}")
                
                with col2:
                    age_options = ['brand_new', 'existing_untouched', 'existing_one_comment', 'existing_multiple_comments']
                    new_age = st.selectbox("Bug Age", age_options, key=f"age_{bug['id']}")
                    
                    if st.button("Update", key=f"update_{bug['id']}"):
                        conn = sqlite3.connect(DB_FILE)
                        cursor = conn.cursor()
                        cursor.execute('UPDATE bugs SET bug_age = ? WHERE id = ?', (new_age, bug['id']))
                        conn.commit()
                        conn.close()
                        st.success("Updated!")
                        st.rerun()
    else:
        st.info("No bugs found")

elif page == "History":
    st.title("Import History")
    
    conn = sqlite3.connect(DB_FILE)
    history = pd.read_sql_query('SELECT * FROM import_history ORDER BY import_date DESC', conn)
    conn.close()
    
    if not history.empty:
        for _, record in history.iterrows():
            with st.expander(f"{record['import_date']} - {record['total_bugs']} bugs"):
                if record['html_report']:
                    st.components.v1.html(record['html_report'], height=400, scrolling=True)
                    st.download_button("Download", record['html_report'], 
                                     f"report_{record['import_date']}.html", 
                                     mime="text/html", key=f"dl_{record['id']}")
    else:
        st.info("No history") 