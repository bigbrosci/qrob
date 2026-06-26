#!/bin/bash

# Setup script to install daily auto-update cron job for qrob
# Run this once on each device where you want daily updates

REPO_DIR="/home/qli/bin/qrob"
UPDATE_SCRIPT="$REPO_DIR/update-qrob.sh"
CRON_FILE="/tmp/qrob-cron-$USER.tmp"

echo "========== qrob Auto-Update Setup =========="
echo "Repository: $REPO_DIR"
echo ""

# Check if repository exists
if [ ! -d "$REPO_DIR/.git" ]; then
    echo "ERROR: Repository not found at $REPO_DIR"
    exit 1
fi

# Check if update script exists
if [ ! -f "$UPDATE_SCRIPT" ]; then
    echo "ERROR: Update script not found at $UPDATE_SCRIPT"
    exit 1
fi

# Make update script executable
chmod +x "$UPDATE_SCRIPT"
echo "✓ Update script is executable"

# Create cron job entry
# Run daily at 2:00 AM (adjust time as needed)
CRON_ENTRY="0 2 * * * $UPDATE_SCRIPT >> /home/qli/.qrob-updates.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "update-qrob.sh"; then
    echo "✓ Cron job already exists"
    echo ""
    echo "Current cron entry:"
    crontab -l | grep update-qrob.sh
else
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "✓ Cron job installed"
    echo ""
    echo "Cron entry: $CRON_ENTRY"
fi

echo ""
echo "========== Setup Complete =========="
echo ""
echo "Update log location: /home/qli/.qrob-updates.log"
echo ""
echo "To view the log:"
echo "  tail -f /home/qli/.qrob-updates.log"
echo ""
echo "To modify the cron schedule:"
echo "  crontab -e"
echo ""
echo "To remove the cron job:"
echo "  crontab -r"
echo ""
