#!/bin/bash

# Setup script for Daily Bug Assignment Automation
# This script sets up a cron job to run the bug assignment script daily at 9am

echo "Setting up Daily Bug Assignment Automation..."

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Create a virtual environment if it doesn't exist
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
fi

# Activate virtual environment and install dependencies
echo "Installing dependencies..."
source "$SCRIPT_DIR/venv/bin/activate"
pip install -r "$SCRIPT_DIR/requirements.txt"

# Create the cron job entry
CRON_CMD="0 9 * * * cd $SCRIPT_DIR && $SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/script.py >> $SCRIPT_DIR/daily_assigner.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "script.py"; then
    echo "Cron job already exists. Updating..."
    # Remove existing job
    crontab -l | grep -v "script.py" | crontab -
fi

# Add the cron job
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "Cron job set up successfully!"
echo "The script will run daily at 9:00 AM"
echo ""
echo "To view your cron jobs, run: crontab -l"
echo "To remove the cron job, run: crontab -l | grep -v 'script.py' | crontab -"
echo ""
echo "Make sure to set up your email credentials as environment variables:"
echo "export SENDER_EMAIL='your-email@company.com'"
echo "export SENDER_PASSWORD='your-app-password'" 