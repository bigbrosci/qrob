#!/bin/bash

# Download one file or folder, given its full path on Turing, to $HOME/temp.
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <full_remote_path>" >&2
    echo "Example: $0 /home/qli7/scratch/test" >&2
    exit 1
fi

REMOTE_PATH=$1
REMOTE_USER="qli7"
FINAL_HOST="turing.wpi.edu"
LOCAL_DIR="$HOME/temp"

case "$REMOTE_PATH" in
    /*) ;;
    *)
        echo "Error: Please provide the full remote path, starting with '/'." >&2
        exit 1
        ;;
esac

mkdir -p "$LOCAL_DIR" || {
    echo "Error: Could not create local directory '$LOCAL_DIR'." >&2
    exit 1
}

echo "Fetching '$REMOTE_PATH' from Turing to '$LOCAL_DIR'..."

if rsync -av -e ssh -- "${REMOTE_USER}@${FINAL_HOST}:${REMOTE_PATH}" "$LOCAL_DIR/"; then
    echo "Fetch completed successfully. Item saved under '$LOCAL_DIR'."
else
    echo "Error: Fetch failed." >&2
    exit 1
fi
