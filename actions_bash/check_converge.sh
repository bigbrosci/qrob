#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <OUTCAR_path_or_calculation_directory>" >&2
  exit 1
fi

input_path="$1"

RESULTS_FILE="${RESULTS_FILE:-check_results.out}"
GOOD_LIST="${GOOD_LIST:-list_good.txt}"
BAD_LIST="${BAD_LIST:-list_bad.txt}"
RERUN_LIST="${RERUN_LIST:-list_rerun.txt}"
SCRATCH_LIST="${SCRATCH_LIST:-list_scratch.txt}"

append_line() {
  local path="$1"
  local text="$2"
  printf '%s\n' "$text" >> "$path"
}

parse_value() {
  local outcar_path="$1"
  local pattern="$2"
  local value
  value=$(grep -m1 -i "$pattern" "$outcar_path" 2>/dev/null | sed -E "s/.*$pattern[^0-9.-]*([-0-9.]+).*/\1/" | head -n1)
  if [[ -z "${value:-}" ]]; then
    echo 0
  else
    echo "$value"
  fi
}

parse_iteration() {
  local outcar_path="$1"
  awk '
    {
      line = $0
      gsub(/-/, "", line)
      if (match(line, /Iteration[[:space:]]+([0-9]+)[[:space:]]*\\(([[:space:]]*([0-9]+)/, m)) {
        ionic = m[1]
        electronic = m[2]
      }
    }
    END {
      print (ionic + 0) " " (electronic + 0)
    }
  ' "$outcar_path"
}

if [[ -d "$input_path" ]]; then
  outcar_path="$input_path/OUTCAR"
  calc_dir="$(cd "$input_path" && pwd)"
elif [[ -f "$input_path" ]]; then
  outcar_path="$input_path"
  calc_dir="$(cd "$(dirname "$outcar_path")" && pwd)"
else
  echo "Input path not found: $input_path" >&2
  exit 1
fi

if [[ ! -f "$outcar_path" ]]; then
  touch "$RESULTS_FILE" "$GOOD_LIST" "$BAD_LIST" "$RERUN_LIST" "$SCRATCH_LIST"
  append_line "$RESULTS_FILE" "$calc_dir, Bad: OUTCAR not found. Ionic: 0, NSW: 0, Electronic: 0, NELM: 0."
  append_line "$BAD_LIST" "$calc_dir"
  append_line "$RESULTS_FILE" "$calc_dir, Action: scratch."
  append_line "$SCRATCH_LIST" "$calc_dir"
  exit 0
fi

nsw=$(parse_value "$outcar_path" "NSW")
nelm=$(parse_value "$outcar_path" "NELM")
read -r ionic_step electronic_step < <(parse_iteration "$outcar_path")

has_ionic=0
if grep -q 'reached required accuracy' "$outcar_path"; then
  has_ionic=1
fi

has_elec=0
if grep -q 'aborting loop because EDIFF is reached' "$outcar_path"; then
  has_elec=1
fi

if [[ "$nsw" -le 1 ]]; then
  is_static=1
else
  is_static=0
fi

if [[ "$is_static" -eq 1 ]]; then
  if [[ "$has_elec" -eq 1 && "$nelm" -gt "$electronic_step" ]]; then
    converged=1
    reason='Job converged.'
  else
    converged=0
    reason='Single-point calculation did not converge or was terminated.'
  fi
else
  if [[ "$has_ionic" -eq 1 && "$nelm" -gt "$electronic_step" ]]; then
    converged=1
    reason='Job converged.'
  else
    converged=0
    reason='Relaxation did not converge or was terminated.'
  fi
fi

if [[ "$converged" -eq 1 ]]; then
  touch "$RESULTS_FILE" "$GOOD_LIST" "$BAD_LIST" "$RERUN_LIST" "$SCRATCH_LIST"
  append_line "$RESULTS_FILE" "$calc_dir, Good: $reason Ionic: $ionic_step, NSW: $nsw, Electronic: $electronic_step, NELM: $nelm."
  append_line "$GOOD_LIST" "$calc_dir"
else
  touch "$RESULTS_FILE" "$GOOD_LIST" "$BAD_LIST" "$RERUN_LIST" "$SCRATCH_LIST"
  append_line "$RESULTS_FILE" "$calc_dir, Bad: $reason Ionic: $ionic_step, NSW: $nsw, Electronic: $electronic_step, NELM: $nelm."
  append_line "$BAD_LIST" "$calc_dir"

  if [[ "$ionic_step" -gt 1 ]]; then
    action='rerun'
    append_line "$RERUN_LIST" "$calc_dir"
  else
    action='scratch'
    append_line "$SCRATCH_LIST" "$calc_dir"
  fi

  append_line "$RESULTS_FILE" "$calc_dir, Action: $action."
fi
