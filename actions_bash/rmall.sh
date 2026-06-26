#!/usr/bin/env bash
# Remove common VASP/auxiliary files using one command with cleanup modes.

set -euo pipefail

mode="${1:-light}"

light_patterns=(
    '*.log'
    'e.*'
    'e_*'
    'o.*'
    'o_*'
    'err.*'
    'out.*'
    'REPORT*'
    'PCDAT*'
    'p4vasp.log'
    'vasp*share*'
    'vasp*tes*'
    'gam.*'
    'IB*'
    'EI*'
    'core*'
    'slurm*'
)

deep_patterns=(
    'CHG*'
    'WAVE*'
    'AE*'
    'DOS*'
    'PRO*'
)

usage() {
    cat <<'EOF'
Usage: rmall.sh [light|deep] [--dry-run]

Modes:
  light    Remove logs and common temporary VASP outputs (default)
  deep     Remove everything from light plus large charge/wavefunction files

Options:
  --dry-run   Print matching files without deleting them
EOF
}

dry_run=false
if [[ "${mode}" == "--help" || "${mode}" == "-h" ]]; then
    usage
    exit 0
fi

if [[ $# -ge 2 ]]; then
    if [[ "${2}" == "--dry-run" ]]; then
        dry_run=true
    else
        echo "Unknown option: ${2}" >&2
        usage >&2
        exit 2
    fi
elif [[ $# -eq 1 && "${1}" == "--dry-run" ]]; then
    mode="light"
    dry_run=true
fi

case "${mode}" in
    light)
        patterns=("${light_patterns[@]}")
        ;;
    deep)
        patterns=("${light_patterns[@]}" "${deep_patterns[@]}")
        ;;
    *)
        echo "Unknown mode: ${mode}" >&2
        usage >&2
        exit 2
        ;;
esac

cmd=(find . -mindepth 1 -type f "(")
first=true
for pattern in "${patterns[@]}"; do
    if $first; then
        cmd+=(-name "${pattern}")
        first=false
    else
        cmd+=(-o -name "${pattern}")
    fi
done
cmd+=(")")

if $dry_run; then
    cmd+=(-print)
else
    cmd+=(-print -delete)
fi

"${cmd[@]}"
