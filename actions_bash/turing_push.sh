#!/bin/bash

# Upload one local file or folder to the Turing scratch directory.
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <local_file_or_folder>" >&2
    exit 1
fi

LOCAL_DATA=$1
REMOTE_USER="qli7"
FINAL_HOST="turing.wpi.edu"
REMOTE_DIR="/home/qli7/scratch/"

if [ ! -e "$LOCAL_DATA" ]; then
    echo "Error: Local file or folder '$LOCAL_DATA' does not exist." >&2
    exit 1
fi

echo "Transferring '$LOCAL_DATA' to '$REMOTE_DIR' on Turing..."

if rsync -av -e ssh -- "$LOCAL_DATA" "${REMOTE_USER}@${FINAL_HOST}:${REMOTE_DIR}"; then
    echo "Transfer completed successfully."
else
    echo "Error: Transfer failed." >&2
    exit 1
fi
