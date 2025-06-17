#!/usr/bin/env python3
"""
Daily Bug Assignment Automation Script - Google Sheets Version
Automates the process using Google Sheets instead of local Excel files
"""

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
from gspread_dataframe import set_with_dataframe, get_as_dataframe
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import logging
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CQEToOursGoogleSheets:
    """Google Sheets version of the bug assignment automation"""
    
    def __init__(self, target_spreadsheet_id: str, source_spreadsheet_id: str = None, 
                 credentials_file: str = 'credentials.json'):
        """
        Initialize with Google Sheets
        
        Args:
            target_spreadsheet_id: ID of the custom-top-cqe-bugs-daily-assigner spreadsheet
            source_spreadsheet_id: ID of the CQE source spreadsheet
            credentials_file: Path to Google service account credentials JSON
        """
        self.target_spreadsheet_id = target_spreadsheet_id
        self.source_spreadsheet_id = source_spreadsheet_id
        
        # Initialize Google Sheets client
        self.creds = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/spreadsheets',
                   'https://www.googleapis.com/auth/drive']
        )
        self.client = gspread.authorize(self.creds)
        
        # Open target spreadsheet
        self.spreadsheet = self.client.open_by_key(target_spreadsheet_id)
        
        # Sheet names
        self.sheet_names = {
            'daily': 'Daily New',
            'GL': 'GL',
            'NT': 'NT',
            'PP': 'PP'
        }
        
        self.team_emails = {
            'GL': os.getenv('GL_EMAIL', 'geetha@company.com'),
            'NT': os.getenv('NT_EMAIL', 'nicolas@company.com'),
            'PP': os.getenv('PP_EMAIL', 'phuong@company.com')
        }
        
    def ensure_sheets_exist(self):
        """Ensure all required sheets exist in the spreadsheet"""
        existing_sheets = [sheet.title for sheet in self.spreadsheet.worksheets()]
        
        for sheet_name in self.sheet_names.values():
            if sheet_name not in existing_sheets:
                logger.info(f"Creating sheet: {sheet_name}")
                self.spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
                
    def grab_CQE_daily(self):
        """
        Step 1 & 2: Grab CQE data from source Google Sheet and paste into Daily New
        """
        logger.info("Grabbing CQE data from Google Sheets...")
        
        if not self.source_spreadsheet_id:
            logger.warning("No source spreadsheet ID provided")
            return
            
        try:
            # Open source spreadsheet
            source_spreadsheet = self.client.open_by_key(self.source_spreadsheet_id)
            source_sheet = source_spreadsheet.sheet1  # Assuming data is in first sheet
            
            # Get source data as DataFrame
            source_data = get_as_dataframe(source_sheet, evaluate_formulas=True)
            source_data = source_data.dropna(how='all').dropna(axis=1, how='all')
            
            # Get existing data from Daily New
            daily_sheet = self.spreadsheet.worksheet(self.sheet_names['daily'])
            existing_data = get_as_dataframe(daily_sheet, evaluate_formulas=True)
            existing_data = existing_data.dropna(how='all').dropna(axis=1, how='all')
            
            # Process new bugs
            for _, new_bug in source_data.iterrows():
                bug_id = new_bug.get('Bug ID', new_bug.get('ID', ''))
                priority = new_bug.get('Priority', 100)
                
                if bug_id and bug_id in existing_data.get('Bug ID', []).values:
                    # Update priority if bug exists
                    row_idx = existing_data[existing_data['Bug ID'] == bug_id].index[0]
                    daily_sheet.update_cell(row_idx + 2, 
                                          existing_data.columns.get_loc('Priority') + 1, 
                                          priority)
                    logger.info(f"Updated priority for existing bug {bug_id}")
                else:
                    # Append new bug
                    new_row = [
                        '',  # Assignment column
                        bug_id,
                        priority,
                        new_bug.get('Title', ''),
                        new_bug.get('Failure Mode', ''),
                        new_bug.get('Status', 'Open'),
                        new_bug.get('Assignee', '')
                    ]
                    daily_sheet.append_row(new_row)
                    logger.info(f"Added new bug {bug_id}")
                    
        except Exception as e:
            logger.error(f"Error grabbing CQE data: {e}")
            raise
            
    def assign_dropdown_tags(self):
        """
        Step 3: Assign dropdown tags based on failure mode
        Note: Google Sheets data validation is set differently than Excel
        """
        logger.info("Assigning team tags...")
        
        daily_sheet = self.spreadsheet.worksheet(self.sheet_names['daily'])
        
        # Get all data
        data = daily_sheet.get_all_values()
        if len(data) <= 1:  # Only header or empty
            return
            
        # Update assignments based on failure mode
        for row_idx in range(2, len(data) + 1):  # Skip header
            assignment_cell = daily_sheet.cell(row_idx, 1)
            
            if not assignment_cell.value:
                # Get failure mode (assuming it's in column 5)
                failure_mode = daily_sheet.cell(row_idx, 5).value
                assignment = self._determine_assignment(failure_mode)
                daily_sheet.update_cell(row_idx, 1, assignment)
                
        # Set data validation for assignment column
        # Note: This requires using batchUpdate which is more complex
        # For simplicity, we'll skip the dropdown creation in Google Sheets
        
    def _determine_assignment(self, failure_mode: str) -> str:
        """Determine team assignment based on failure mode"""
        if not failure_mode:
            return ""
            
        failure_mode = str(failure_mode).lower()
        
        # Assignment rules
        gl_patterns = ['graphics', 'display', 'render', 'gpu']
        nt_patterns = ['network', 'connectivity', 'wifi', 'ethernet']
        pp_patterns = ['power', 'performance', 'battery', 'thermal']
        
        for pattern in gl_patterns:
            if pattern in failure_mode:
                return "GL"
                
        for pattern in nt_patterns:
            if pattern in failure_mode:
                return "NT"
                
        for pattern in pp_patterns:
            if pattern in failure_mode:
                return "PP"
                
        return "GL"  # Default
        
    def reorder_by_priority(self, sheet_name: str = 'daily'):
        """
        Step 4 & 6: Reorder bugs by priority in Google Sheets
        """
        logger.info(f"Reordering by priority in {sheet_name}...")
        
        sheet = self.spreadsheet.worksheet(self.sheet_names[sheet_name])
        
        # Get data as DataFrame
        df = get_as_dataframe(sheet, evaluate_formulas=True)
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        if df.empty:
            return
            
        # Sort by priority
        df_sorted = df.sort_values('Priority', ascending=True)
        
        # Clear sheet and rewrite
        sheet.clear()
        set_with_dataframe(sheet, df_sorted, include_index=False, include_column_header=True)
        
    def distribute_to_team_sheets(self):
        """
        Step 5: Distribute bugs to team sheets
        """
        logger.info("Distributing bugs to team sheets...")
        
        daily_sheet = self.spreadsheet.worksheet(self.sheet_names['daily'])
        daily_data = get_as_dataframe(daily_sheet, evaluate_formulas=True)
        daily_data = daily_data.dropna(how='all').dropna(axis=1, how='all')
        
        for team in ['GL', 'NT', 'PP']:
            # Filter bugs for this team
            team_bugs = daily_data[daily_data.iloc[:, 0] == team]  # Assignment is first column
            
            if not team_bugs.empty:
                team_sheet = self.spreadsheet.worksheet(self.sheet_names[team])
                
                # Append to existing data
                existing_data = get_as_dataframe(team_sheet, evaluate_formulas=True)
                existing_data = existing_data.dropna(how='all').dropna(axis=1, how='all')
                
                # Combine and remove duplicates based on Bug ID
                combined = pd.concat([existing_data, team_bugs], ignore_index=True)
                if 'Bug ID' in combined.columns:
                    combined = combined.drop_duplicates(subset=['Bug ID'], keep='last')
                
                # Write back
                team_sheet.clear()
                set_with_dataframe(team_sheet, combined, include_index=False, include_column_header=True)
                
    def delete_completed_bugs(self):
        """
        Step 7: Delete completed bugs
        Note: In Google Sheets, we'll check for a "COMPLETED" column with "Yes" values
        """
        logger.info("Deleting completed bugs...")
        
        for sheet_name in self.sheet_names.values():
            sheet = self.spreadsheet.worksheet(sheet_name)
            data = sheet.get_all_values()
            
            if len(data) <= 1:
                continue
                
            # Find or create COMPLETED column
            headers = data[0]
            if 'COMPLETED' not in headers:
                # Add COMPLETED column
                sheet.update_cell(1, len(headers) + 1, 'COMPLETED')
                completed_col = len(headers) + 1
            else:
                completed_col = headers.index('COMPLETED') + 1
                
            # Find completed rows (from bottom to top to maintain indices)
            rows_to_delete = []
            for row_idx in range(len(data) - 1, 0, -1):  # Skip header
                if row_idx + 1 <= sheet.row_count:
                    cell_value = sheet.cell(row_idx + 1, completed_col).value
                    # Check for "Yes" or green background (would need additional API calls)
                    if cell_value and cell_value.lower() in ['yes', 'y', 'true', 'completed']:
                        rows_to_delete.append(row_idx + 1)
                        
            # Delete rows
            for row in rows_to_delete:
                sheet.delete_rows(row)
                logger.info(f"Deleted completed bug in row {row} from {sheet_name}")
                
    def send_daily_email(self):
        """
        Step 8: Send daily email with top 25 bugs per team
        """
        logger.info("Preparing daily email...")
        
        subject = f"Daily Top Bugs Ready For You to Start - {datetime.now().strftime('%Y-%m-%d')}"
        
        body = """
        <html>
        <body>
        <h2>Daily Top Bugs Assignment</h2>
        <p>Please review your assigned bugs below. You can access the full spreadsheet 
        <a href="https://docs.google.com/spreadsheets/d/{}/edit">here</a>.</p>
        """.format(self.target_spreadsheet_id)
        
        # Get top 25 bugs for each team
        for team in ['GL', 'NT', 'PP']:
            sheet = self.spreadsheet.worksheet(self.sheet_names[team])
            df = get_as_dataframe(sheet, evaluate_formulas=True)
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            if not df.empty and 'Priority' in df.columns:
                # Get top 25 by priority
                top_bugs = df.nsmallest(25, 'Priority')
                
                body += f"<h3>{team} Team Bugs:</h3>"
                body += "<table border='1' style='border-collapse: collapse;'>"
                body += "<tr><th>Bug ID</th><th>Priority</th><th>Title</th><th>Failure Mode</th></tr>"
                
                for _, bug in top_bugs.iterrows():
                    body += f"<tr>"
                    body += f"<td>{bug.get('Bug ID', '')}</td>"
                    body += f"<td>{bug.get('Priority', '')}</td>"
                    body += f"<td>{bug.get('Title', '')}</td>"
                    body += f"<td>{bug.get('Failure Mode', '')}</td>"
                    body += f"</tr>"
                    
                body += "</table><br>"
                
        body += """
        </body>
        </html>
        """
        
        # Send email (same as original script)
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        
        if sender_email and sender_password:
            try:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = sender_email
                msg['To'] = ', '.join(self.team_emails.values())
                
                msg.attach(MIMEText(body, 'html'))
                
                smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
                smtp_port = int(os.getenv('SMTP_PORT', '587'))
                
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.send_message(msg)
                    
                logger.info("Email sent successfully")
                
            except Exception as e:
                logger.error(f"Error sending email: {e}")
        else:
            logger.warning("Email credentials not provided")
            
    def run_full_process(self):
        """Run the complete daily process"""
        logger.info("Starting full daily bug assignment process...")
        
        try:
            self.ensure_sheets_exist()
            self.grab_CQE_daily()
            self.assign_dropdown_tags()
            self.reorder_by_priority('daily')
            self.distribute_to_team_sheets()
            
            for team in ['GL', 'NT', 'PP']:
                self.reorder_by_priority(team)
                
            self.delete_completed_bugs()
            self.send_daily_email()
            
            logger.info("Daily bug assignment process completed successfully!")
            
        except Exception as e:
            logger.error(f"Error in daily process: {e}")
            raise


def main():
    """Main function"""
    # Get spreadsheet IDs from environment or config
    TARGET_SPREADSHEET_ID = os.getenv('TARGET_SPREADSHEET_ID')
    SOURCE_SPREADSHEET_ID = os.getenv('SOURCE_SPREADSHEET_ID')
    CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    
    if not TARGET_SPREADSHEET_ID:
        logger.error("TARGET_SPREADSHEET_ID not set in environment")
        return
        
    assigner = CQEToOursGoogleSheets(
        TARGET_SPREADSHEET_ID,
        SOURCE_SPREADSHEET_ID,
        CREDENTIALS_FILE
    )
    
    assigner.run_full_process()


if __name__ == "__main__":
    main() 