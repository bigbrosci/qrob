#!/usr/bin/env bash
# Faster removal of common VASP/auxiliary files using a single find invocation.
# This avoids spawning many subshells and is robust to many files.

set -euo pipefail

# Patterns to delete (shell-glob style passed to find -name)
# Patterns to delete: list one-per-line for easy editing
patterns=(
    'CHG*'
    'WAVE*'
    'AE*'
    'e.*'
    'e_*'
    'o.*'
    'o_*'
    'err.*'
    'out.*'
    'REPORT*'
    'PCDAT*'
    'p4vasp.log'
)

# Build the find command arguments from the patterns array
cmd=(find . -type f)
first=true
for p in "${patterns[@]}"; do
    if $first; then
        cmd+=(-name "$p")
        first=false
    else
        cmd+=(-o -name "$p")
    fi
done
cmd+=(-print -delete)

# Execute the constructed find command
"${cmd[@]}"

