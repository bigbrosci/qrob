#!/bin/bash

# Check if the folder name argument is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <local_folder_name>"
    exit 1
fi

# Assign variables
LOCAL_data=$1  # can be either folder or file
REMOTE_USER="qli9"
FINAL_HOST="login01.expanse.sdsc.edu"
REMOTE_DIR="/expanse/lustre/projects/mas138/qli9/upload"

# Check if the local folder exists
if [ ! -d "$LOCAL_data" ]; then
#    echo "Error: Local folder '$LOCAL_data' does not exist."
#    exit 1
    echo "Sending Files to Faster"
else  
    echo "Sending Folders to Faster"	
fi

# Rsync command to transfer the folder to the remote directory 
echo "Transferring '$LOCAL_data' to '$REMOTE_DIR' on Expanse..."

rsync -av -e ssh ${LOCAL_data} ${REMOTE_USER}@${FINAL_HOST}:${REMOTE_DIR}/

# Check for rsync success
if [ $? -eq 0 ]; then
    echo "Transfer completed successfully."
else
    echo "Error: Transfer failed."
    exit 1
fi

