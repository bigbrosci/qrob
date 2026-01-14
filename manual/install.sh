#!/usr/bin/env bash
set -euo pipefail

# Simple installer for q-robot (moved to manual/)
# Usage: ./install.sh [target_dir]
# Default target_dir: $HOME/bin/qrob

REPO_URL="https://github.com/bigbrosci/qrob.git"
TARGET_DIR="${1:-$HOME/bin/qrob}"
SYMLINK="$HOME/bin/q-robot"
BASHRC="$HOME/.bashrc"

MARKER_START="# >>> q-robot settings >>>"
MARKER_END="# <<< q-robot settings <<<"

echo "Installing q-robot into: $TARGET_DIR"

mkdir -p "$(dirname "$TARGET_DIR")"

if [ -d "$TARGET_DIR/.git" ]; then
    echo "Repository already exists at $TARGET_DIR — pulling latest changes"
    git -C "$TARGET_DIR" pull --ff-only || git -C "$TARGET_DIR" pull
else
    git clone "$REPO_URL" "$TARGET_DIR"
fi

# Create or update compatibility symlink ~/bin/q-robot -> target
if [ -L "$SYMLINK" ]; then
    ln -sfn "$TARGET_DIR" "$SYMLINK"
    echo "Updated symlink: $SYMLINK -> $TARGET_DIR"
elif [ -e "$SYMLINK" ]; then
    echo "Warning: $SYMLINK exists and is not a symlink. Backing up to ${SYMLINK}.bak"
    mv "$SYMLINK" "${SYMLINK}.bak"
    ln -s "$TARGET_DIR" "$SYMLINK"
    echo "Created symlink: $SYMLINK -> $TARGET_DIR (previous file moved to ${SYMLINK}.bak)"
else
    ln -s "$TARGET_DIR" "$SYMLINK"
    echo "Created symlink: $SYMLINK -> $TARGET_DIR"
fi

# Ensure .bashrc exists
touch "$BASHRC"

# Build new block
read -r -d '' NEW_BLOCK <<'EOF' || true
# >>> q-robot settings >>>
export ROBOT=$HOME/bin/qrob
export PATH=$PATH:$ROBOT/actions:$ROBOT/friends/vtst/vtstscripts-1040
export PYTHONPATH=$PYTHONPATH:$ROBOT/brain
# <<< q-robot settings <<<
EOF

# Remove any existing block between markers, then append the new block
TMPFILE=$(mktemp)
sed "/^$MARKER_START\$/, /^$MARKER_END\$/d" "$BASHRC" > "$TMPFILE" || true
echo >> "$TMPFILE"
echo "$NEW_BLOCK" >> "$TMPFILE"

# Backup and replace
cp "$BASHRC" "${BASHRC}.qrobot.bak" || true
mv "$TMPFILE" "$BASHRC"
echo "Updated $BASHRC (backup saved to ${BASHRC}.qrobot.bak)"

echo "Installation complete. To apply the new environment variables run:"
echo "  source $BASHRC"
echo
echo "Notes:"
echo "- Default install target is '$TARGET_DIR'. To choose a different location, run: ./install.sh /some/path"
echo "- A compatibility symlink was created at '$SYMLINK' pointing to the installed directory."
echo "- The installer replaces any previous q-robot env block in $BASHRC between the marker comments."
git clone https://github.com/bigbrosci/q-robot.git ~/bin/q-robot 
