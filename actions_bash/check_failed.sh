#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
output_file="$script_dir/failed_list.txt"

: > "$output_file"

for log in "$script_dir"/Cu*/vasp.log; do
  if [[ ! -f "$log" ]]; then
    continue
  fi

  if tail -n 100 "$log" | grep -q 'KILLED BY SIGNAL:'; then
    dir_name="$(basename "$(dirname "$log")")"
    printf '%s\n' "$dir_name" >> "$output_file"
    rm -f -- "$log"
  fi
done
