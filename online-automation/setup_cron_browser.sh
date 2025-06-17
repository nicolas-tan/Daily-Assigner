#!/bin/bash 

# Setup script for Browser Automated Daily Bug Assignment
# This script sets up a cron job to run the browser automation script daily at 9:30am PST

echo "Setting up Browser Automated Daily Bug Assignment..."

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
fi

# Activate virtual environment and install dependencies
echo "Installing dependencies..."
source "$SCRIPT_DIR/venv/bin/activate"
pip install -r "$SCRIPT_DIR/requirements_browser.txt"

# Install Chrome driver
echo "Setting up Chrome driver..."
pip install webdriver-manager

# Create a wrapper script for cron that handles display
cat > "$SCRIPT_DIR/run_browser_automation.sh" << 'EOF'
#!/bin/bash
# Wrapper script for running browser automation in cron

# Set up display for headless operation
export DISPLAY=:99
export CHROME_BIN=/usr/bin/google-chrome

# Navigate to script directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Run the browser automation script
python3 script_browser_automation.py >> daily_assigner.log 2>&1
EOF

chmod +x "$SCRIPT_DIR/run_browser_automation.sh"

# Create the cron job entry for 9:30 AM PST
# Note: Adjust the hour based on your server's timezone
# If server is in UTC, 9:30 AM PST = 5:30 PM UTC (17:30)
# If server is in PST, use 9:30
echo "Setting up cron job for 9:30 AM PST..."
echo "What timezone is your server in?"
echo "1) PST/PDT (Pacific Time)"
echo "2) UTC"
echo "3) Other"
read -p "Select option (1-3): " tz_choice

case $tz_choice in
    1)
        CRON_TIME="30 9"  # 9:30 AM
        ;;
    2)
        CRON_TIME="30 17"  # 9:30 AM PST = 5:30 PM UTC
        ;;
    3)
        read -p "Enter the hour (0-23) that corresponds to 9:30 AM PST in your timezone: " CRON_HOUR
        CRON_TIME="30 $CRON_HOUR"
        ;;
    *)
        echo "Invalid choice, defaulting to 9:30 AM PST"
        CRON_TIME="30 9"
        ;;
esac

CRON_CMD="$CRON_TIME * * * cd $SCRIPT_DIR && $SCRIPT_DIR/run_browser_automation.sh"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "run_browser_automation.sh"; then
    echo "Cron job already exists. Updating..."
    # Remove existing job
    crontab -l | grep -v "run_browser_automation.sh" | crontab -
fi

# Add the cron job
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo ""
echo "✅ Cron job set up successfully!"
echo "The script will run daily at 9:30 AM PST when your computer is on"
echo ""
echo "📋 Next steps:"
echo "1. Copy env_example.txt to .env and update with your values:"
echo "   cp env_example.txt .env"
echo "   nano .env"
echo ""
echo "2. Make sure Chrome is installed:"
echo "   google-chrome --version"
echo ""
echo "3. Test the automation:"
echo "   python test_browser_automation.py"
echo ""
echo "4. View cron jobs:"
echo "   crontab -l"
echo ""
echo "5. Monitor logs:"
echo "   tail -f daily_assigner.log"
echo ""
echo "To remove the cron job later:"
echo "   crontab -l | grep -v 'run_browser_automation.sh' | crontab -" 