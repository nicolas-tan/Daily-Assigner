#!/usr/bin/env python3
"""
Deploy HTML report to public hosting services
"""

import os
import sys
import glob
import subprocess
import requests
import zipfile
import tempfile

def get_latest_report():
    """Find the most recent bug report HTML file"""
    html_files = glob.glob('bug_report_*.html')
    if not html_files:
        print("❌ No bug report HTML files found!")
        return None
    latest = max(html_files, key=os.path.getmtime)
    return latest

def deploy_to_netlify_drop(report_file):
    """Deploy to Netlify Drop - no account needed"""
    print("🚀 Deploying to Netlify Drop (free, 24-hour hosting)...")
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create index.html
        index_path = os.path.join(tmpdir, 'index.html')
        os.system(f'cp "{report_file}" "{index_path}"')
        
        # Create a zip file
        zip_path = os.path.join(tmpdir, 'site.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(index_path, 'index.html')
        
        # Upload to Netlify
        try:
            with open(zip_path, 'rb') as f:
                response = requests.post(
                    'https://api.netlify.com/api/v1/sites',
                    files={'zip': ('site.zip', f, 'application/zip')},
                    headers={'Content-Type': 'application/zip'}
                )
            
            if response.status_code == 201:
                data = response.json()
                url = data.get('url', '')
                print(f"\n✅ Deployment successful!")
                print(f"🌐 Public URL: {url}")
                print(f"⏰ Valid for: 24 hours")
                print(f"\n📱 Anyone can access this URL from anywhere!")
                return url
            else:
                print(f"❌ Deployment failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

def deploy_to_surge():
    """Deploy to Surge.sh - free static hosting"""
    print("\n🚀 Deploying to Surge.sh (free, permanent hosting)...")
    
    report_file = get_latest_report()
    if not report_file:
        return None
    
    # Check if surge is installed
    try:
        subprocess.run(['surge', '--version'], capture_output=True, check=True)
    except:
        print("📦 Installing Surge CLI...")
        subprocess.run(['npm', 'install', '-g', 'surge'], check=True)
    
    # Create deployment directory
    deploy_dir = 'surge-deploy'
    os.makedirs(deploy_dir, exist_ok=True)
    
    # Copy report as index.html
    subprocess.run(['cp', report_file, f'{deploy_dir}/index.html'])
    
    # Deploy with surge
    print("\n📝 Follow the prompts to deploy:")
    print("   - Press Enter to accept the directory")
    print("   - Choose a unique domain like: bug-report-[yourname].surge.sh")
    
    result = subprocess.run(['surge', deploy_dir])
    
    if result.returncode == 0:
        print("\n✅ Deployment successful!")
        print("📱 Your report is now publicly accessible!")
        return True
    
    return False

def main():
    print("🌐 Public Deployment Options")
    print("="*50)
    
    report_file = get_latest_report()
    if not report_file:
        sys.exit(1)
    
    print(f"📄 Report to deploy: {report_file}")
    print("\nChoose deployment method:")
    print("1. Netlify Drop (instant, no account, 24-hour hosting)")
    print("2. Surge.sh (free account, permanent hosting)")
    print("3. Transfer.sh (command line, 14-day hosting)")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == '1':
        deploy_to_netlify_drop(report_file)
    elif choice == '2':
        deploy_to_surge()
    elif choice == '3':
        # Use curl to upload to transfer.sh
        print("\n🚀 Uploading to Transfer.sh...")
        result = subprocess.run(
            ['curl', '--upload-file', report_file, f'https://transfer.sh/{report_file}'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            print(f"\n✅ Upload successful!")
            print(f"🌐 Public URL: {url}")
            print(f"⏰ Valid for: 14 days")
            print(f"\n📱 Anyone can access this URL from anywhere!")
        else:
            print(f"❌ Upload failed: {result.stderr}")
    else:
        print("❌ Invalid option")

if __name__ == "__main__":
    main() 