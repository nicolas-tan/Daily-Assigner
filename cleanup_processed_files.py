#!/usr/bin/env python3
"""
Cleanup Script for Processed Files
Removes backup files created by offline_processor.py
"""

import os
import glob
import sys
from datetime import datetime

def cleanup_processed_files(directory="."):
    """
    Remove all processed_* backup files created by offline processor
    
    Args:
        directory: Directory to clean (default: current directory)
    """
    # Pattern to match processed files
    pattern = os.path.join(directory, "processed_*_*.xlsx")
    
    # Find all matching files
    processed_files = glob.glob(pattern)
    
    if not processed_files:
        print("✅ No processed backup files found to clean.")
        return 0
    
    # Show files that will be deleted
    print(f"Found {len(processed_files)} processed backup file(s):")
    for file in processed_files:
        file_size = os.path.getsize(file) / 1024  # Size in KB
        print(f"  - {os.path.basename(file)} ({file_size:.1f} KB)")
    
    # Ask for confirmation
    print("\n⚠️  These files will be permanently deleted!")
    response = input("Continue? (y/N): ").strip().lower()
    
    if response != 'y':
        print("❌ Cleanup cancelled.")
        return 1
    
    # Delete files
    deleted_count = 0
    for file in processed_files:
        try:
            os.remove(file)
            print(f"🗑️  Deleted: {os.path.basename(file)}")
            deleted_count += 1
        except Exception as e:
            print(f"❌ Error deleting {file}: {e}")
    
    print(f"\n✅ Cleanup complete! Deleted {deleted_count} file(s).")
    return 0

def cleanup_specific_pattern(pattern):
    """
    Clean up files matching a specific pattern
    
    Args:
        pattern: File pattern to match (e.g., "*cqe_bugs*.xlsx")
    """
    matching_files = glob.glob(pattern)
    
    if not matching_files:
        print(f"✅ No files matching '{pattern}' found.")
        return 0
    
    print(f"Found {len(matching_files)} file(s) matching '{pattern}':")
    for file in matching_files:
        print(f"  - {file}")
    
    response = input("\nDelete these files? (y/N): ").strip().lower()
    
    if response == 'y':
        for file in matching_files:
            try:
                os.remove(file)
                print(f"🗑️  Deleted: {file}")
            except Exception as e:
                print(f"❌ Error deleting {file}: {e}")
    else:
        print("❌ Cleanup cancelled.")
    
    return 0

def main():
    """Main function to handle command line arguments"""
    
    print("🧹 Processed Files Cleanup Tool\n")
    
    if len(sys.argv) > 1:
        # Custom pattern provided
        pattern = sys.argv[1]
        print(f"Cleaning files matching pattern: {pattern}")
        cleanup_specific_pattern(pattern)
    else:
        # Default: clean processed_* files
        cleanup_processed_files()
    
    # Also clean up any Zone.Identifier files (Windows WSL artifacts)
    zone_files = glob.glob("*.xlsx:Zone.Identifier") + glob.glob("*.xlsx:sec.endpointdlp")
    if zone_files:
        print(f"\nFound {len(zone_files)} Windows metadata file(s):")
        for zf in zone_files:
            print(f"  - {zf}")
        
        response = input("Also delete these metadata files? (y/N): ").strip().lower()
        if response == 'y':
            for zf in zone_files:
                try:
                    os.remove(zf)
                    print(f"🗑️  Deleted: {zf}")
                except Exception as e:
                    print(f"❌ Error deleting {zf}: {e}")

if __name__ == "__main__":
    main() 