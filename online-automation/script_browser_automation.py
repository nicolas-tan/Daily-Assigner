#!/usr/bin/env python3
"""
Browser Automation Script for Daily Bug Assignment
Automates downloading from Google Sheets, Excel processing, and uploading back
"""

import os
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import pandas as pd
from script import CQEToOursNewest
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
import matplotlib.pyplot as plt
import openpyxl
import urllib.parse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExcelScreenshotCapture:
    """Captures screenshots of Excel sheets as images"""
    
    def __init__(self, excel_file):
        self.excel_file = excel_file
        self.workbook = openpyxl.load_workbook(excel_file)
        
    def capture_sheet_as_image(self, sheet_name, output_path):
        """Convert Excel sheet to image"""
        # Read the sheet into a dataframe
        df = pd.read_excel(self.excel_file, sheet_name=sheet_name)
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(20, 10))
        ax.axis('tight')
        ax.axis('off')
        
        # Create table
        table = ax.table(cellText=df.values,
                        colLabels=df.columns,
                        cellLoc='center',
                        loc='center')
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 1.5)
        
        # Style header row
        for i in range(len(df.columns)):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Alternate row colors
        for i in range(1, len(df) + 1):
            for j in range(len(df.columns)):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#f0f0f0')
        
        # Save the figure
        plt.savefig(output_path, bbox_inches='tight', dpi=150, pad_inches=0.1)
        plt.close()
        
        logger.info(f"Screenshot saved: {output_path}")
        return output_path
    
    def capture_tabs(self, tab_indices=[1, 2, 3]):
        """Capture specific tabs (0-indexed)"""
        screenshots = []
        sheet_names = self.workbook.sheetnames
        
        for idx in tab_indices:
            if idx < len(sheet_names):
                sheet_name = sheet_names[idx]
                output_path = f"screenshot_tab_{idx+1}_{sheet_name.replace(' ', '_')}.png"
                self.capture_sheet_as_image(sheet_name, output_path)
                screenshots.append({
                    'path': output_path,
                    'name': sheet_name,
                    'tab_number': idx + 1
                })
        
        return screenshots


class EmailSender:
    """Sends emails with attachments using SMTP"""
    
    def __init__(self):
        # Email configuration from environment or defaults
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.office365.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL', '')
        self.sender_password = os.getenv('SENDER_PASSWORD', '')
        
    def create_email_body(self, excel_file):
        """Create HTML email body with summary"""
        # Read the first sheet for summary
        df = pd.read_excel(excel_file, sheet_name=0)
        
        html_body = f"""
        <html>
            <body>
                <h2>Daily Bug Assignment Report - {datetime.now().strftime('%Y-%m-%d')}</h2>
                
                <p>Hello Team,</p>
                
                <p>Please find attached the bug assignments tasked for today. The Excel file has been processed and updated with the latest assignments.</p>
                
                <h3>Summary:</h3>
                <ul>
                    <li>Total bugs processed: {len(df)}</li>
                    <li>Excel file: {os.path.basename(excel_file)}</li>
                    <li>Processing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                </ul>
                
                <p>Screenshots showing highest priority bugs via Tabs 2, 3, and 4 (each sheet per person) are attached below for quick reference.</p>
                
                <p>Best regards,<br>
                PG520 Bug Assignment Automation Bot</p>
            </body>
        </html>
        """
        
        return html_body
    
    def send_email(self, recipients, subject, excel_file, screenshots):
        """Send email with Excel file and screenshots"""
        
        # Create message
        msg = MIMEMultipart('mixed')
        msg['From'] = self.sender_email
        msg['To'] = ', '.join(recipients) if isinstance(recipients, list) else recipients
        msg['Subject'] = subject
        
        # Add HTML body
        html_body = self.create_email_body(excel_file)
        msg.attach(MIMEText(html_body, 'html'))
        
        # Attach Excel file
        with open(excel_file, 'rb') as f:
            excel_attachment = MIMEBase('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            excel_attachment.set_payload(f.read())
            encoders.encode_base64(excel_attachment)
            excel_attachment.add_header('Content-Disposition', f'attachment; filename={os.path.basename(excel_file)}')
            msg.attach(excel_attachment)
        
        # Attach screenshots
        for screenshot in screenshots:
            with open(screenshot['path'], 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-Disposition', f'attachment; filename={os.path.basename(screenshot["path"])}')
                img.add_header('Content-ID', f'<{screenshot["name"]}>')
                msg.attach(img)
        
        # Send email
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                logger.info(f"Email sent successfully to {msg['To']}")
                return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


def send_bug_assignment_email(excel_file, recipients):
    """Main function to capture screenshots and send email"""
    
    logger.info("Starting email process...")
    
    # Capture screenshots of tabs 2, 3, 4
    screenshot_capture = ExcelScreenshotCapture(excel_file)
    screenshots = screenshot_capture.capture_tabs([1, 2, 3])  # 0-indexed, so 1,2,3 = tabs 2,3,4
    
    # Send email
    email_sender = EmailSender()
    subject = f"Bug Assignment Report - {datetime.now().strftime('%Y-%m-%d')}"
    
    success = email_sender.send_email(recipients, subject, excel_file, screenshots)
    
    # Clean up screenshot files
    if success:
        for screenshot in screenshots:
            if os.path.exists(screenshot['path']):
                os.remove(screenshot['path'])
                logger.info(f"Cleaned up: {screenshot['path']}")
    
    return success


def generate_mailto_link(excel_file, recipients):
    """Generate a mailto link that opens in default email client"""
    subject = f"Bug Assignment Report - {datetime.now().strftime('%Y-%m-%d')}"
    body = f"""Hello Team,

Please find attached the bug assignment results for today.

Excel file: {os.path.basename(excel_file)}
Processing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Best regards,
Bug Assignment Automation"""
    
    # URL encode the subject and body
    subject_encoded = urllib.parse.quote(subject)
    body_encoded = urllib.parse.quote(body)
    recipients_str = ','.join(recipients) if isinstance(recipients, list) else recipients
    
    mailto_link = f"mailto:{recipients_str}?subject={subject_encoded}&body={body_encoded}"
    
    return mailto_link


class GoogleSheetsAutomation:
    """Automates Google Sheets download/upload operations"""
    
    def __init__(self, download_dir=None, headless=False):
        """
        Initialize browser automation
        
        Args:
            download_dir: Directory for downloads (defaults to current dir)
            headless: Run browser in headless mode
        """
        self.download_dir = download_dir or os.getcwd()
        
        # Configure Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_experimental_option("prefs", {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        
        if headless:
            self.chrome_options.add_argument("--headless")
            self.chrome_options.add_argument("--no-sandbox")
            self.chrome_options.add_argument("--disable-dev-shm-usage")
            
        self.driver = None
        
    def start_browser(self):
        """Start Chrome browser"""
        logger.info("Starting Chrome browser...")
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.driver.maximize_window()
        
    def login_if_needed(self):
        """Check if login is needed and wait for user to login"""
        try:
            # Check if we're on a login page
            if "accounts.google.com" in self.driver.current_url:
                logger.info("Login required. Please login to Google account...")
                # Wait up to 5 minutes for login
                WebDriverWait(self.driver, 300).until(
                    lambda driver: "accounts.google.com" not in driver.current_url
                )
                logger.info("Login successful!")
                time.sleep(2)
        except TimeoutException:
            logger.error("Login timeout - please try again")
            raise
            
    def download_google_sheet(self, sheet_url, output_filename):
        """
        Download a Google Sheet as Excel file
        
        Args:
            sheet_url: URL of the Google Sheet
            output_filename: Name for the downloaded file
        """
        logger.info(f"Downloading Google Sheet: {sheet_url}")
        
        # Navigate to sheet
        self.driver.get(sheet_url)
        time.sleep(3)
        
        # Handle login if needed
        self.login_if_needed()
        
        # Wait for sheet to load
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.ID, "docs-file-menu"))
        )
        time.sleep(2)
        
        try:
            # Click File menu
            file_menu = self.driver.find_element(By.ID, "docs-file-menu")
            file_menu.click()
            time.sleep(1)
            
            # Click Download
            download_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Download d']"))
            )
            download_option.click()
            time.sleep(1)
            
            # Click Microsoft Excel (.xlsx)
            excel_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@aria-label, 'Microsoft Excel')]"))
            )
            excel_option.click()
            
            # Wait for download to complete
            logger.info("Waiting for download to complete...")
            time.sleep(5)  # Adjust based on file size
            
            # Rename downloaded file
            self._rename_latest_download(output_filename)
            
            logger.info(f"Downloaded successfully: {output_filename}")
            
        except Exception as e:
            logger.error(f"Error downloading sheet: {e}")
            # Take screenshot for debugging
            self.driver.save_screenshot("download_error.png")
            raise
            
    def upload_to_google_sheet(self, sheet_url, excel_file):
        """
        Upload Excel file to Google Sheet
        
        Args:
            sheet_url: URL of the target Google Sheet
            excel_file: Path to Excel file to upload
        """
        logger.info(f"Uploading to Google Sheet: {sheet_url}")
        
        # Navigate to sheet
        self.driver.get(sheet_url)
        time.sleep(3)
        
        # Handle login if needed
        self.login_if_needed()
        
        # Wait for sheet to load
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.ID, "docs-file-menu"))
        )
        time.sleep(2)
        
        try:
            # Click File menu
            file_menu = self.driver.find_element(By.ID, "docs-file-menu")
            file_menu.click()
            time.sleep(1)
            
            # Click Import
            import_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Import t']"))
            )
            import_option.click()
            time.sleep(2)
            
            # Click Upload tab
            upload_tab = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[text()='Upload']"))
            )
            upload_tab.click()
            time.sleep(1)
            
            # Find file input and upload
            file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            file_input.send_keys(os.path.abspath(excel_file))
            time.sleep(3)
            
            # Select "Replace current sheet" option
            replace_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Replace current sheet')]"))
            )
            replace_option.click()
            time.sleep(1)
            
            # Click Import data button
            import_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Import data']"))
            )
            import_button.click()
            
            # Wait for import to complete
            logger.info("Waiting for import to complete...")
            time.sleep(10)
            
            logger.info("Upload completed successfully!")
            
        except Exception as e:
            logger.error(f"Error uploading sheet: {e}")
            # Take screenshot for debugging
            self.driver.save_screenshot("upload_error.png")
            raise
            
    def _rename_latest_download(self, new_name):
        """Rename the most recently downloaded file"""
        # Get list of files in download directory
        files = os.listdir(self.download_dir)
        files = [f for f in files if f.endswith('.xlsx') and not f.startswith('~$')]
        
        if not files:
            raise Exception("No Excel files found in download directory")
            
        # Get the most recent file
        latest_file = max(
            [os.path.join(self.download_dir, f) for f in files],
            key=os.path.getctime
        )
        
        # Rename to desired name
        new_path = os.path.join(self.download_dir, new_name)
        if os.path.exists(new_path):
            os.remove(new_path)
        os.rename(latest_file, new_path)
        
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            

def run_automated_process():
    """Run the complete automated process"""
    
    # Get configuration from environment
    target_sheet_url = os.getenv('TARGET_SHEET_URL')
    source_sheet_url = os.getenv('SOURCE_SHEET_URL')
    
    if not target_sheet_url or not source_sheet_url:
        logger.error("Please set TARGET_SHEET_URL and SOURCE_SHEET_URL in .env file")
        return
        
    # File names
    target_file = "custom-top-cqe-bugs-daily-assigner.xlsx"
    source_file = "cqe_bugs.xlsx" #the source url that is being renamed with a new save in xlsx (used in CQEToOursNewest class for processing)
    
    # Initialize browser automation
    automation = GoogleSheetsAutomation()
    
    try:
        # Start browser
        automation.start_browser()
        
        # Step 1: Download Google Sheets
        logger.info("=== Step 1: Downloading Google Sheets ===")
        automation.download_google_sheet(target_sheet_url, target_file)
        automation.download_google_sheet(source_sheet_url, source_file)
        
        # Step 2: Process Excel files
        logger.info("=== Step 2: Processing Excel files ===")
        processor = CQEToOursNewest(target_file, source_file)
        processor.run_full_process()
        
        # Step 3: Upload back to Google Sheets
        logger.info("=== Step 3: Uploading to Google Sheets ===")
        automation.upload_to_google_sheet(target_sheet_url, target_file)
        
        # Step 4: Send email with results
        logger.info("=== Step 4: Sending email with results ===")
        email_recipients = os.getenv('EMAIL_RECIPIENTS', '').split(',')
        
        if email_recipients and email_recipients[0]:
            # Try to send email
            email_sent = send_bug_assignment_email(target_file, email_recipients)
            
            if not email_sent:
                # If SMTP fails, generate mailto link as fallback
                logger.info("SMTP email failed, generating mailto link...")
                mailto_link = generate_mailto_link(target_file, email_recipients)
                logger.info(f"Open this link to send email: {mailto_link}")
                
                # Open the mailto link in browser
                automation.driver.execute_script(f"window.open('{mailto_link}', '_blank');")
                time.sleep(5)  # Give time for email client to open
        else:
            logger.info("No email recipients configured. Skipping email step.")
        
        logger.info("=== Process completed successfully! ===")
        
    except Exception as e:
        logger.error(f"Process failed: {e}")
        raise
        
    finally:
        # Close browser
        automation.close()
        
        # Optional: Clean up downloaded files
        if os.getenv('CLEANUP_FILES', 'true').lower() == 'true':
            for file in [target_file, source_file]:
                if os.path.exists(file):
                    os.remove(file)
                    logger.info(f"Cleaned up: {file}")


if __name__ == "__main__":
    run_automated_process() 