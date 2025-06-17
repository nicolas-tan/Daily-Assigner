#!/usr/bin/env python3
"""
Offline Excel Processing Script
Run the bug assignment operations on manually downloaded Excel files
"""

import os
import sys
import logging
from datetime import datetime
from script import CQEToOursNewest
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def is_cqe_file(excel_path):
    """
    Check if the given Excel file is a CQE bugs file (doesn't have our required sheets)
    """
    try:
        import openpyxl
        wb = openpyxl.load_workbook(excel_path, read_only=True)
        sheet_names = wb.sheetnames
        wb.close()
        
        # Check if it has our required sheets
        required_sheets = ['Daily New', 'GL', 'NT', 'PP']
        has_required_sheets = all(sheet in sheet_names for sheet in required_sheets)
        
        # If it has the required sheets BUT also has CQE-specific sheets, it's still a CQE file
        cqe_indicators = ['From External CSP', 'Closed cases', 'Pivot by TAT', 'StatusLocation']
        has_cqe_sheets = any(any(indicator in sheet for indicator in cqe_indicators) for sheet in sheet_names)
        
        return has_cqe_sheets or not has_required_sheets
    except Exception:
        return True  # Assume it's a CQE file if we can't read it properly


def process_single_cqe_file(cqe_file_path):
    """
    Process a single CQE file by creating a proper structure and importing data from first tab only
    """
    logger.info(f"Processing CQE file: {cqe_file_path}")
    
    # Create output filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = os.path.splitext(os.path.basename(cqe_file_path))[0]
    output_file = f"processed_{timestamp}_{base_name}.xlsx"
    
    # Step 1: Read ONLY the first sheet of CQE data
    logger.info("Reading CQE data from first sheet only...")
    try:
        # Get sheet names first
        excel_file = pd.ExcelFile(cqe_file_path)
        first_sheet_name = excel_file.sheet_names[0]
        logger.info(f"Reading from sheet: '{first_sheet_name}'")
        
        # Read only the first sheet
        cqe_data = pd.read_excel(cqe_file_path, sheet_name=0)
        logger.info(f"Found {len(cqe_data)} rows in first sheet")
        logger.info(f"Columns: {', '.join(cqe_data.columns.tolist())}")
    except Exception as e:
        logger.error(f"Error reading CQE file: {e}")
        return None
    
    # Step 2: Map CQE columns to our format
    logger.info("Mapping CQE columns to standard format...")
    
    # Define column mapping based on user requirements
    column_mapping = {
        'SXM SN for SXM RMA': 'SN Associated',
        'FA NVbug Number': 'Bug ID',
        'Priority': 'Priority',
        'Customer Reported Failure': 'Title',
        'Date added to Top 30 of priority list': 'Created Date',
        'Status': 'COMPLETED',
        'Product': 'Product'
    }
    
    # Create a new DataFrame with mapped columns
    mapped_data = pd.DataFrame()
    
    # Map each column
    for cqe_col, new_col in column_mapping.items():
        if cqe_col in cqe_data.columns:
            mapped_data[new_col] = cqe_data[cqe_col]
            logger.info(f"Mapped '{cqe_col}' to '{new_col}'")
        else:
            logger.warning(f"Column '{cqe_col}' not found in CQE data")
            mapped_data[new_col] = ''
    
    # Debug: Check Product column values
    if 'Product' in mapped_data.columns:
        logger.info(f"Product column values (first 10): {mapped_data['Product'].head(10).tolist()}")
    
    # Process Bug ID column - add https://nvbugs/ prefix if not present
    if 'Bug ID' in mapped_data.columns:
        def format_bug_id(bug_id):
            if pd.isna(bug_id) or str(bug_id).strip() == '':
                return 'nvbug not provided for this bug.'
            bug_id_str = str(bug_id).strip()
            # Check if it already has the prefix
            if bug_id_str.startswith('https://nvbugs/'):
                return bug_id_str
            # If it's just a number, add the prefix
            return f'https://nvbugs/{bug_id_str}'
        
        mapped_data['Bug ID'] = mapped_data['Bug ID'].apply(format_bug_id)
        logger.info("Formatted Bug ID column with https://nvbugs/ prefix")
    
    # Convert SN Associated column to handle large numbers
    if 'SN Associated' in mapped_data.columns:
        # Convert to numeric first to clean the data
        mapped_data['SN Associated'] = pd.to_numeric(mapped_data['SN Associated'], errors='coerce')
        # Fill NaN values with 0
        mapped_data['SN Associated'] = mapped_data['SN Associated'].fillna(0)
        # Convert large numbers to integers then to string to preserve full number
        # This prevents scientific notation display
        mapped_data['SN Associated'] = mapped_data['SN Associated'].apply(
            lambda x: str(int(x)) if x != 0 and pd.notna(x) else ''
        )
    
    # Add empty columns for missing fields
    mapped_data['Assignment'] = ''  # Empty Assignment column
    mapped_data['Failure Mode'] = ''  # Empty as requested
    
    # Track rows that need black highlighting (non-SXM5 products) - BEFORE reordering columns
    rows_to_highlight = []
    if 'Product' in mapped_data.columns:
        logger.info(f"Product column found, checking {len(mapped_data)} rows for highlighting...")
        for idx, product in enumerate(mapped_data['Product']):
            if pd.notna(product) and str(product).strip() != '':
                product_str = str(product).strip()
                # Check if "SXM5" is NOT in the product string
                if 'SXM5' not in product_str:
                    rows_to_highlight.append(idx)
                    logger.info(f"Row {idx+2} will be highlighted (Product: {product_str})")
            else:
                # Empty product values should also be highlighted
                rows_to_highlight.append(idx)
                logger.debug(f"Row {idx+2} has empty/NaN Product value - will be highlighted")
    else:
        logger.warning("Product column not found in mapped_data!")
    
    # Reorder columns to match our template - now including Product as rightmost
    column_order = ['Assignment', 'Bug ID', 'Priority', 'Title', 'Failure Mode', 
                    'Created Date', 'COMPLETED', 'SN Associated', 'Product']
    
    # Ensure all columns exist
    for col in column_order:
        if col not in mapped_data.columns:
            mapped_data[col] = ''
    
    # Don't remove Product column anymore - keep it as rightmost column
    # if 'Product' in mapped_data.columns:
    #     del mapped_data['Product']
    
    mapped_data = mapped_data[column_order]
    
    # Process Priority column - fill blanks with sequential numbers
    if 'Priority' in mapped_data.columns:
        priority_col = mapped_data['Priority'].copy()
        
        # Convert to numeric, keeping NaN for blanks
        priority_col = pd.to_numeric(priority_col, errors='coerce')
        
        # Fill blanks with sequential numbers
        last_value = 0
        for i in range(len(priority_col)):
            if pd.notna(priority_col.iloc[i]):
                # Found a non-blank value
                current_value = int(priority_col.iloc[i])
                if i > 0 and last_value > 0:
                    # Fill the blanks between last_value and current_value
                    blank_start = None
                    for j in range(i-1, -1, -1):
                        if pd.isna(priority_col.iloc[j]):
                            blank_start = j
                        else:
                            break
                    
                    if blank_start is not None:
                        # Fill sequential values
                        num_blanks = i - blank_start
                        if current_value > last_value + num_blanks:
                            # Fill with sequential numbers
                            for k, idx in enumerate(range(blank_start, i)):
                                priority_col.iloc[idx] = last_value + k + 1
                        else:
                            # Just fill with incremental values
                            for k, idx in enumerate(range(blank_start, i)):
                                priority_col.iloc[idx] = last_value + k + 1
                
                last_value = current_value
            elif i == 0:
                # First row is blank, start with 1
                priority_col.iloc[i] = 1
                last_value = 1
        
        # Handle any remaining blanks at the end
        for i in range(len(priority_col)):
            if pd.isna(priority_col.iloc[i]):
                priority_col.iloc[i] = last_value + 1
                last_value += 1
        
        # Update the mapped_data with filled priorities
        mapped_data['Priority'] = priority_col.astype(int)
        logger.info("Filled blank Priority values with sequential numbers")
    
    # Step 3: Create output Excel with proper structure
    logger.info("Creating output Excel file...")
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.styles.colors import Color
    
    wb = openpyxl.Workbook()
    
    # Remove default sheet
    wb.remove(wb.active)
    
    # Create required sheets
    sheets = ['Daily New', 'GL', 'NT', 'PP']
    
    # Define black fill for non-SXM5 rows - using explicit opaque black
    black_color = Color(rgb="FF000000", type="rgb")
    black_fill = PatternFill(patternType="solid", fgColor=black_color, bgColor=black_color)
    white_font = Font(color="FFFFFF", bold=True)  # White text on black background
    
    for sheet_name in sheets:
        ws = wb.create_sheet(sheet_name)
        
        # Add headers
        for col_idx, header in enumerate(column_order, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            # Format header
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        # If this is the Daily New sheet, add all the data
        if sheet_name == 'Daily New':
            for row_idx, row_data in mapped_data.iterrows():
                excel_row = row_idx + 2  # Excel row number (1-indexed, plus header)
                
                # Check if this row should be highlighted
                should_highlight = row_idx in rows_to_highlight
                
                for col_idx, (col_name, value) in enumerate(zip(column_order, row_data), 1):
                    cell = ws.cell(row=excel_row, column=col_idx, value=value)
                    
                    # Apply black highlighting if needed
                    if should_highlight:
                        cell.fill = black_fill
                        cell.font = white_font
                    
                    # Special formatting for SN Associated column (last column)
                    if col_name == 'SN Associated' and value and value != '':
                        # Store as text to preserve full number without scientific notation
                        cell.value = str(value)
                        # Format to look like a number (right-aligned)
                        cell.alignment = Alignment(horizontal='right')
                        if should_highlight:
                            cell.fill = black_fill
                            cell.font = white_font
        
        # Adjust column widths
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 15
    
    # Save the workbook
    wb.save(output_file)
    logger.info(f"Created output file with {len(mapped_data)} bugs")
    
    # Debug: Verify highlighting was applied
    logger.info("Verifying highlighting in saved file...")
    wb_check = openpyxl.load_workbook(output_file)
    ws_check = wb_check['Daily New']
    for idx in rows_to_highlight[:5]:  # Check first 5 highlighted rows
        cell = ws_check.cell(row=idx+2, column=1)
        logger.info(f"Row {idx+2}: Fill = {cell.fill.fgColor.rgb if cell.fill.fgColor else 'None'}")
    wb_check.close()
    
    # Step 4: Process with the standard workflow
    # NOTE: Skipping standard workflow to preserve highlighting
    logger.info("Skipping standard workflow to preserve custom highlighting...")
    logger.info("=== Process completed successfully! ===")
    logger.info(f"Output saved to: {output_file}")
    
    return output_file
    
    # Commented out to preserve highlighting
    # try:
    #     processor = CQEToOursNewest(output_file, None)
    #     processor.load_workbook()
    #     
    #     # Skip the grab_CQE_daily since we already have the data
    #     processor.assign_dropdown_tags()
    #     processor.reorder_by_priority('Daily New')
    #     processor.distribute_to_team_sheets()
    #     
    #     for team in ['GL', 'NT', 'PP']:
    #         processor.reorder_by_priority(team)
    #     
    #     processor.delete_completed_bugs()
    #     processor.send_daily_email()
    #     
    #     logger.info("=== Process completed successfully! ===")
    #     logger.info(f"Output saved to: {output_file}")
    #     
    #     return output_file
    #     
    # except Exception as e:
    #     logger.error(f"Error during processing: {e}")
    #     import traceback
    #     traceback.print_exc()
    #     return None


def run_offline_process(target_excel_path, source_excel_path=None):
    """
    Run the Excel processing operations offline
    
    Args:
        target_excel_path: Path to your custom-top-cqe-bugs-daily-assigner.xlsx file
        source_excel_path: Path to the CQE source data file (optional)
    """
    logger.info("=== Starting Offline Excel Processing ===")
    logger.info(f"Target file: {target_excel_path}")
    if source_excel_path:
        logger.info(f"Source file: {source_excel_path}")
    
    # Check if files exist
    if not os.path.exists(target_excel_path):
        logger.error(f"Target file not found: {target_excel_path}")
        return False
        
    if source_excel_path and not os.path.exists(source_excel_path):
        logger.error(f"Source file not found: {source_excel_path}")
        return False
    
    try:
        # Create processor instance
        processor = CQEToOursNewest(target_excel_path, source_excel_path)
        
        # Run the full process
        logger.info("Running full bug assignment process...")
        processor.run_full_process()
        
        logger.info("=== Process completed successfully! ===")
        logger.info(f"Updated file saved at: {target_excel_path}")
        
        # Create a backup of the processed file
        backup_name = f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(target_excel_path)}"
        backup_path = os.path.join(os.path.dirname(target_excel_path), backup_name)
        
        # Copy the file as backup
        import shutil
        shutil.copy2(target_excel_path, backup_path)
        logger.info(f"Backup saved at: {backup_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_blank_excel_template(output_path="blank_template.xlsx"):
    """
    Create a blank Excel template with the required sheets and structure
    """
    import openpyxl
    
    logger.info(f"Creating blank Excel template at: {output_path}")
    
    # Create new workbook
    wb = openpyxl.Workbook()
    
    # Remove default sheet
    wb.remove(wb.active)
    
    # Create required sheets
    sheets = ['Daily New', 'GL', 'NT', 'PP']
    
    # Define headers for each sheet - updated to remove Status column
    headers = [
        'Assignment', 'Bug ID', 'Priority', 'Title', 'Failure Mode', 
        'Created Date', 'COMPLETED', 'SN Associated'
    ]
    
    for sheet_name in sheets:
        ws = wb.create_sheet(sheet_name)
        
        # Add headers
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)
            
        # Format header row
        from openpyxl.styles import Font, PatternFill
        header_font = Font(bold=True)
        header_fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.font = header_font
            cell.fill = header_fill
            
        # Adjust column widths
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 15
    
    # Save the workbook
    wb.save(output_path)
    logger.info(f"Blank template created: {output_path}")
    
    return output_path


def main():
    """Main function for offline processing"""
    
    print("\n=== Offline Excel Bug Assignment Processor ===\n")
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python offline_processor.py <excel_file>")
        print("\nExamples:")
        print("  python offline_processor.py cqe_bugs.xlsx")
        print("  python offline_processor.py custom-top-cqe-bugs-daily-assigner.xlsx cqe_bugs.xlsx")
        print("\nTo create a blank template:")
        print("  python offline_processor.py --create-template")
        sys.exit(1)
    
    # Check if creating template
    if sys.argv[1] == "--create-template":
        template_name = sys.argv[2] if len(sys.argv) > 2 else "blank_template.xlsx"
        create_blank_excel_template(template_name)
        sys.exit(0)
    
    # Get file paths
    first_file = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(first_file):
        print(f"❌ Error: File not found: {first_file}")
        sys.exit(1)
    
    # Determine if single file or two file mode
    if len(sys.argv) == 2:
        # Single file mode - check if it's a CQE file
        if is_cqe_file(first_file):
            logger.info("Detected CQE file format - will create proper structure")
            output_file = process_single_cqe_file(first_file)
            if output_file:
                print(f"\n✅ Processing completed successfully!")
                print(f"📄 Output file: {output_file}")
                print(f"📤 You can now upload this file to Google Sheets or Excel Online")
            else:
                print("\n❌ Processing failed. Check the logs above for details.")
                sys.exit(1)
        else:
            # It already has proper structure, process it alone
            success = run_offline_process(first_file)
            if success:
                print("\n✅ Processing completed successfully!")
            else:
                print("\n❌ Processing failed. Check the logs above for details.")
                sys.exit(1)
    else:
        # Two file mode - traditional target + source
        target_file = first_file
        source_file = sys.argv[2]
        
        success = run_offline_process(target_file, source_file)
        
        if success:
            print("\n✅ Processing completed successfully!")
        else:
            print("\n❌ Processing failed. Check the logs above for details.")
            sys.exit(1)


if __name__ == "__main__":
    main() 