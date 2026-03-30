#!/usr/bin/env bash
# Modify the NCORE parameter in INCAR file.
# If INCAR contains IBRION = 5,6,7 or 8, remove any NCORE line (NCORE unsupported for these IBRION values).

set -euo pipefail

num="${1:-}"
incar_file="INCAR"

if [ ! -f "$incar_file" ]; then
	echo "Error: $incar_file not found in current directory" >&2
	exit 2
fi

# Read IBRION line (case-insensitive) and extract numeric tokens
ibrion_line=$(grep -i "^ *IBRION" "$incar_file" || true)
if [ -n "$ibrion_line" ]; then
	# extract digits from the line
	# e.g. "IBRION = 5" or "IBRION= -1" -> tokens: -1, 5, etc.
	ibrion_vals=$(echo "$ibrion_line" | sed 's/[^0-9 \-]/ /g')
	# check if any of 5,6,7,8 present
	for v in $ibrion_vals; do
		if [ "$v" = "5" ] || [ "$v" = "6" ] || [ "$v" = "7" ] || [ "$v" = "8" ]; then
			# remove NCORE line (case-insensitive match of NCORE) and exit
			sed -i.bak '/^[[:space:]]*NCORE\>/I d' "$incar_file"
			echo "Removed NCORE from $incar_file because IBRION=${v} is set."
			exit 0
		fi
	done
fi

# No disallowed IBRION found: update or append NCORE
if [ -z "$num" ]; then
	echo "Usage: $(basename "$0") NCORE_VALUE" >&2
	exit 3
fi

# Remove existing NCORE line (case-insensitive) then append new value
sed -i.bak '/^[[:space:]]*NCORE\>/I d' "$incar_file"
echo "NCORE = $num" >> "$incar_file"
echo "Set NCORE = $num in $incar_file"

