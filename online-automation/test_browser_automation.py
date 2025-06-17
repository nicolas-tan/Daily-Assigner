#!/usr/bin/env python3
"""
Test script for Browser Automation
Tests the automated download, process, and upload workflow
"""

import os
import sys
from script_browser_automation import GoogleSheetsAutomation
from test_script import create_test_excel, create_sample_bug_data, test_assignment_logic
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_browser_automation():
    """Test browser automation functionality"""
    print("\n" + "="*50)
    print("Testing Browser Automation")
    print("="*50 + "\n")
    
    # First test the assignment logic
    test_assignment_logic()
    
    print("\nDo you want to test browser automation? (y/n): ", end="")
    if input().strip().lower() != 'y':
        return
        
    print("\nStarting browser automation test...")
    print("NOTE: This will open a Chrome browser window")
    print("You may need to login to your Google account if not already logged in")
    
    # Get test URLs
    print("\nEnter your test Google Sheet URLs (or press Enter to skip):")
    target_url = input("Target sheet URL: ").strip()
    source_url = input("Source sheet URL: ").strip()
    
    if not target_url or not source_url:
        print("Skipping browser test - no URLs provided")
        return
        
    # Create test Excel files
    print("\nCreating test Excel files...")
    test_excel = create_test_excel()
    test_csv, _ = create_sample_bug_data()
    
    # Convert CSV to Excel
    import pandas as pd
    df = pd.read_csv(test_csv)
    test_source = "test_source.xlsx"
    df.to_excel(test_source, index=False)
    
    # Initialize browser automation
    automation = GoogleSheetsAutomation()
    
    try:
        automation.start_browser()
        
        print("\nTesting download functionality...")
        # Test downloading (this will overwrite our test files)
        automation.download_google_sheet(target_url, "downloaded_target.xlsx")
        print("✓ Download test successful")
        
        print("\nTesting upload functionality...")
        # Test uploading our test file
        automation.upload_to_google_sheet(target_url, test_excel)
        print("✓ Upload test successful")
        
        print("\n" + "="*50)
        print("Browser automation tests passed!")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Browser automation test failed: {e}")
        
    finally:
        automation.close()
        
        # Cleanup
        for file in [test_excel, test_source, test_csv, "downloaded_target.xlsx"]:
            if os.path.exists(file):
                os.remove(file)


def test_full_automation():
    """Test the complete automated workflow"""
    print("\n" + "="*50)
    print("Testing Full Automated Workflow")
    print("="*50 + "\n")
    
    print("This test will:")
    print("1. Download sheets from Google")
    print("2. Process them with Excel logic")
    print("3. Upload back to Google")
    print("\nMake sure you have set up your .env file with:")
    print("- TARGET_SHEET_URL")
    print("- SOURCE_SHEET_URL")
    print("- Email credentials")
    
    print("\nContinue? (y/n): ", end="")
    if input().strip().lower() != 'y':
        return
        
    # Import and run the main automation
    from script_browser_automation import run_automated_process
    
    try:
        run_automated_process()
        print("\n✅ Full automation test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Full automation test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Browser Automation Test Suite")
    print("1. Test browser automation components")
    print("2. Test full automated workflow")
    print("\nSelect option (1 or 2): ", end="")
    
    choice = input().strip()
    
    if choice == "1":
        test_browser_automation()
    elif choice == "2":
        test_full_automation()
    else:
        print("Invalid choice") 