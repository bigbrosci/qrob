#!/usr/bin/env bash

set -euo pipefail

print_energy() {
    local job_dir="$1"
    if [[ -e "${job_dir}/OUTCAR" ]]; then
        echo -e "${job_dir}\t$(grep '  without' "${job_dir}/OUTCAR" | tail -n 1 | awk '{print $7}')"
    else
        echo -e "${job_dir}"
    fi
}

if [[ -f list ]]; then
    while IFS= read -r job_dir; do
        [[ -z "${job_dir}" ]] && continue
        print_energy "${job_dir}"
    done < list
else
    for job_dir in *; do
        [[ -d "${job_dir}" ]] || continue
        if [[ -e "${job_dir}/OUTCAR" ]]; then
            print_energy "${job_dir}"
        fi
    done
fi
