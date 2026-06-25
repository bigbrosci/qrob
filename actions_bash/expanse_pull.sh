#!/bin/bash

# Check if the folder name argument is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <remote_folder_name>"
    exit 1
fi

# Assign variables
REMOTE_FOLDER=$1
REMOTE_USER="qli9"
FINAL_HOST="login01.expanse.sdsc.edu"
REMOTE_DIR="/expanse/lustre/projects/mas138/qli9/${REMOTE_FOLDER}"
LOCAL_DIR="$HOME/temp"

# Rsync command to download the folder from the remote server via jump host
echo "Fetching '${REMOTE_FOLDER}' from expanse to the local directory '${LOCAL_DIR}'..."

rsync -av -e ssh ${REMOTE_USER}@${FINAL_HOST}:${REMOTE_DIR} ${LOCAL_DIR}
 
# Check for rsync success
if [ $? -eq 0 ]; then
    echo "Fetch completed successfully. Folder saved to '${LOCAL_DIR}'."
else
    echo "Error: Fetch failed."
    exit 1
fi

