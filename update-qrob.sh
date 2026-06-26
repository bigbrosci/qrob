#!/bin/bash

# Auto-update script for qrob repository
# Designed to run daily via cron

set -e

# Configuration
REPO_DIR="$HOME/bin/qrob"
LOG_FILE="${REPO_DIR}/.update-log.txt"
REMOTE="origin"
BRANCH="main"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Function to log messages
log_message() {
    echo "[${TIMESTAMP}] $1" >> "$LOG_FILE"
    echo "[${TIMESTAMP}] $1"
}

# Ensure we're in the repo directory
if [ ! -d "$REPO_DIR/.git" ]; then
    log_message "ERROR: Not a git repository at $REPO_DIR"
    exit 1
fi

cd "$REPO_DIR"

log_message "========== Starting qrob update =========="

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    log_message "WARNING: Uncommitted local changes detected. Stashing changes..."
    git stash push -m "Auto-stash before update on $TIMESTAMP"
fi

# Fetch the latest changes from remote
log_message "Fetching latest changes from $REMOTE/$BRANCH..."
if ! git fetch "$REMOTE" "$BRANCH" 2>&1 | tee -a "$LOG_FILE"; then
    log_message "ERROR: Failed to fetch from remote"
    exit 1
fi

# Check if local branch is behind remote
LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse "$REMOTE/$BRANCH")

if [ "$LOCAL_COMMIT" = "$REMOTE_COMMIT" ]; then
    log_message "Repository is up to date (no changes)"
else
    log_message "Updating from $LOCAL_COMMIT to $REMOTE_COMMIT..."
    
    # Fast-forward merge (safest option)
    if git merge --ff-only "$REMOTE/$BRANCH" 2>&1 | tee -a "$LOG_FILE"; then
        log_message "SUCCESS: Repository updated successfully"
    else
        log_message "ERROR: Failed to merge. Local changes conflict with remote."
        # Attempt to recover
        git merge --abort 2>/dev/null || true
        log_message "Merge aborted. Manual intervention may be needed."
        exit 1
    fi
fi

log_message "========== Update completed =========="
exit 0
