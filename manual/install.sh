#!/usr/bin/env bash
set -euo pipefail

# Simple installer for q-robot (moved to manual/)
# Usage: ./install.sh [target_dir]
# Default target_dir: $HOME/bin/qrob

REPO_URL="https://github.com/bigbrosci/qrob.git"
TARGET_DIR="${1:-$HOME/bin/qrob}"
SYMLINK="$HOME/bin/qrob"

# Detect OS and choose appropriate shell/profile file
OS_TYPE="unknown"
RC_FILE="$HOME/.bashrc"
PS_PROFILE_WIN="$HOME/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1"
PS_PROFILE_CORE="$HOME/.config/powershell/profile.ps1"
if [[ "${OSTYPE:-}" == darwin* ]]; then
    OS_TYPE="macos"
    SHELL_NAME=$(basename "${SHELL:-}")
    if [ "${SHELL_NAME}" = "zsh" ]; then
        RC_FILE="$HOME/.zshrc"
    else
        RC_FILE="$HOME/.bash_profile"
    fi
elif [[ "${OSTYPE:-}" == linux* ]]; then
    OS_TYPE="linux"
    RC_FILE="$HOME/.bashrc"
elif [[ "${OSTYPE:-}" == msys* || "${OSTYPE:-}" == cygwin* || "${OSTYPE:-}" == win32* || "${OSTYPE:-}" == mingw* ]]; then
    OS_TYPE="windows"
    # Prefer PowerShell profile when possible; fall back to bashrc for Git Bash
    if [ -f "$PS_PROFILE_WIN" ] || [ -d "$(dirname "$PS_PROFILE_WIN")" ]; then
        RC_FILE="$PS_PROFILE_WIN"
    else
        RC_FILE="$PS_PROFILE_CORE"
    fi
    # If neither exists, still write to bashrc for Git Bash compatibility
    if [ -z "$RC_FILE" ]; then
        RC_FILE="$HOME/.bashrc"
    fi
else
    OS_TYPE="unknown"
    RC_FILE="$HOME/.bashrc"
fi

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

# Ensure profile file exists (create parent dirs for PowerShell profiles)
if [[ "$OS_TYPE" == "windows" && ("$RC_FILE" == "$PS_PROFILE_WIN" || "$RC_FILE" == "$PS_PROFILE_CORE") ]]; then
    mkdir -p "$(dirname "$RC_FILE")"
    touch "$RC_FILE"
else
    touch "$RC_FILE"
fi

# Build new block appropriate to the detected profile type
if [[ "$OS_TYPE" == "windows" ]]; then
    # PowerShell block
    read -r -d '' NEW_BLOCK <<'PS_EOF' || true
# >>> q-robot settings >>>
$env:ROBOT = "__TARGET_DIR__"
$env:Path = "$env:Path;${env:ROBOT}\actions;${env:ROBOT}\friends\vtstscripts-1040"
# Note: to extend PYTHONPATH in PowerShell, set it in your Python launcher or activate a conda env.
# <<< q-robot settings <<<
PS_EOF
    NEW_BLOCK="${NEW_BLOCK//__TARGET_DIR__/$TARGET_DIR}"
else
    # POSIX shell block (bash/zsh)
    read -r -d '' NEW_BLOCK <<'SH_EOF' || true
# >>> q-robot settings >>>
export ROBOT="__TARGET_DIR__"
export PATH=\$PATH:\$ROBOT/actions:\$ROBOT/friends/vtstscripts-1040
export PYTHONPATH=\$PYTHONPATH:\$ROBOT/brain
# <<< q-robot settings <<<
SH_EOF
    NEW_BLOCK="${NEW_BLOCK//__TARGET_DIR__/$TARGET_DIR}"
fi

# Remove any existing block between markers, then append the new block
# Remove any existing block between markers, then append the new block
TMPFILE=$(mktemp)
sed "/^$MARKER_START\$/, /^$MARKER_END\$/d" "$RC_FILE" > "$TMPFILE" || true
echo >> "$TMPFILE"
echo "$NEW_BLOCK" >> "$TMPFILE"

# Backup and replace
cp "$RC_FILE" "${RC_FILE}.qrobot.bak" || true
mv "$TMPFILE" "$RC_FILE"
echo "Updated $RC_FILE (backup saved to ${RC_FILE}.qrobot.bak)"

echo "Installation complete. To apply the new environment variables run:"
if [[ "$OS_TYPE" == "windows" ]]; then
    if [[ "$RC_FILE" == "$PS_PROFILE_WIN" || "$RC_FILE" == "$PS_PROFILE_CORE" ]]; then
        echo "  Restart PowerShell (or run: . $RC_FILE) to load the new settings"
    else
        echo "  source $RC_FILE"
    fi
else
    echo "  source $RC_FILE"
fi
echo
ENV_FILE="$TARGET_DIR/manual/qrob_env.yml"
if [ -f "$ENV_FILE" ]; then
    # Detect mamba or conda
    if command -v mamba >/dev/null 2>&1; then
        TOOL=mamba
    elif command -v conda >/dev/null 2>&1; then
        TOOL=conda
    else
        TOOL=""
    fi

    if [ -n "$TOOL" ]; then
        echo
        read -r -p "Found environment file at $ENV_FILE and '$TOOL'. Create conda env 'qrob' now? [y/N] " REPLY || REPLY=n
        case "$REPLY" in
            [Yy]* )
                echo "Creating environment with $TOOL..."
                if $TOOL env create -f "$ENV_FILE"; then
                    echo "Environment 'qrob' created successfully."
                else
                    echo "Environment creation failed. You can run: $TOOL env create -f \"$ENV_FILE\""
                fi
                ;;
            * )
                echo "Skipping environment creation. To create later run: $TOOL env create -f \"$ENV_FILE\""
                ;;
        esac
    else
        echo
        echo "Note: $ENV_FILE exists but neither 'mamba' nor 'conda' found. To create the environment manually run:" 
        echo "  mamba env create -f \"$ENV_FILE\"  # or conda env create -f \"$ENV_FILE\""
    fi
fi

echo "Notes:"
echo "- Default install target is '$TARGET_DIR'. To choose a different location, run: ./install.sh /some/path"
echo "- A compatibility symlink was created at '$SYMLINK' pointing to the installed directory."
echo "- The installer replaces any previous q-robot env block in $RC_FILE between the marker comments."
