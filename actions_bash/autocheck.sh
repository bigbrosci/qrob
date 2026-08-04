#!/usr/bin/env bash
# Monitor VASP calculation folders and resubmit failed Slurm jobs.

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly CHECK_CONVERGE="$SCRIPT_DIR/../actions_py/check_converge.py"
readonly SAVE_CALCULATIONS="$SCRIPT_DIR/save_calculations.sh"

interval=1800
run_once=false

usage() {
    cat <<'EOF'
Usage: autocheck.sh [--interval SECONDS] [--once] JOB_LIST.txt
       autocheck.sh [--interval SECONDS] [--once] FOLDER [FOLDER ...]

Every 30 minutes (by default), check each folder in Slurm and:
  - leave running, pending, and completed jobs unchanged;
  - directly resubmit scratch failures with: sbatch run_vasp_single;
  - save partial calculations, then resubmit rerun failures.

Examples:
  nohup autocheck.sh job_list.txt > autocheck.log 2>&1 &
  nohup autocheck.sh /work/me/job1 /work/me/job2 > autocheck.log 2>&1 &
  autocheck.sh --once /work/me/job1

In job-list mode, each non-empty, non-comment line is a calculation folder.
Completed folders are removed from the list and appended to job_done.txt.
EOF
}

while (($#)); do
    case "$1" in
        --interval)
            if (($# < 2)); then
                echo "Error: --interval requires a value." >&2
                usage >&2
                exit 2
            fi
            interval=$2
            shift 2
            ;;
        --once)
            run_once=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --)
            shift
            break
            ;;
        -*)
            echo "Error: unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
        *)
            break
            ;;
    esac
done

if (($# == 0)); then
    echo "Error: provide a job-list file or at least one calculation folder." >&2
    usage >&2
    exit 2
fi

if [[ ! "$interval" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: interval must be a positive integer number of seconds." >&2
    exit 2
fi

for required_command in sbatch squeue; do
    if ! command -v "$required_command" >/dev/null 2>&1; then
        echo "Error: required command is not available: $required_command" >&2
        exit 2
    fi
done

if [[ ! -x "$CHECK_CONVERGE" ]]; then
    echo "Error: checker is not executable: $CHECK_CONVERGE" >&2
    exit 2
fi
if [[ ! -x "$SAVE_CALCULATIONS" ]]; then
    echo "Error: save helper is not executable: $SAVE_CALCULATIONS" >&2
    exit 2
fi

# check_converge.py writes its tracking lists in the launch directory. Keeping
# this directory fixed makes the lists predictable even while jobs run elsewhere.
readonly STATE_DIR="$PWD"
declare -a CALC_DIRS=()
declare -A SEEN_DIRS=()
declare -A DONE_DIRS=()
list_mode=false
job_list_file=""
job_done_file=""
list_base=""

add_calculation_folder() {
    local folder=$1
    local calc_dir
    if [[ ! -d "$folder" ]]; then
        echo "Error: calculation folder does not exist: $folder" >&2
        return 1
    fi
    calc_dir="$(cd "$folder" && pwd -P)"
    if [[ -z "${SEEN_DIRS[$calc_dir]+present}" ]]; then
        CALC_DIRS+=("$calc_dir")
        SEEN_DIRS["$calc_dir"]=1
    fi
}

if (($# == 1)) && [[ -f "$1" ]]; then
    list_mode=true
    job_list_file="$(cd "$(dirname "$1")" && pwd -P)/$(basename "$1")"
    list_base="$(dirname "$job_list_file")"
    job_done_file="$list_base/job_done.txt"

    while IFS= read -r folder || [[ -n "$folder" ]]; do
        folder=${folder%$'\r'}
        if [[ -z "$folder" || "$folder" =~ ^[[:space:]]*# ]]; then
            continue
        fi
        if [[ "$folder" != /* ]]; then
            folder="$list_base/$folder"
        fi
        add_calculation_folder "$folder" || exit 2
    done < "$job_list_file"
else
    for folder in "$@"; do
        add_calculation_folder "$folder" || exit 2
    done
fi

if ((${#CALC_DIRS[@]} == 0)); then
    echo "Error: no calculation folders were found." >&2
    exit 2
fi

timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

listed_exactly() {
    local list_file=$1
    local calc_dir=$2
    [[ -f "$list_file" ]] && grep -Fqx -- "$calc_dir" "$list_file"
}

record_completed_job() {
    local completed_dir=$1
    local raw_entry
    local candidate
    local temporary_list

    if [[ "$list_mode" != true ]]; then
        return 0
    fi

    if ! listed_exactly "$job_done_file" "$completed_dir"; then
        printf '%s\n' "$completed_dir" >> "$job_done_file"
    fi

    temporary_list="$(mktemp "$list_base/.job_list.tmp.XXXXXX")"
    while IFS= read -r raw_entry || [[ -n "$raw_entry" ]]; do
        candidate=${raw_entry%$'\r'}
        if [[ -n "$candidate" && ! "$candidate" =~ ^[[:space:]]*# ]]; then
            if [[ "$candidate" != /* ]]; then
                candidate="$list_base/$candidate"
            fi
            if [[ -d "$candidate" ]]; then
                candidate="$(cd "$candidate" && pwd -P)"
                if [[ "$candidate" == "$completed_dir" ]]; then
                    continue
                fi
            fi
        fi
        printf '%s\n' "$raw_entry"
    done < "$job_list_file" > "$temporary_list"

    chmod --reference="$job_list_file" "$temporary_list" 2>/dev/null || true
    mv -f -- "$temporary_list" "$job_list_file"
    echo "[$(timestamp)] Moved completed folder from $job_list_file to $job_done_file: $completed_dir"
}

submit_scratch() {
    local calc_dir=$1
    if [[ ! -f "$calc_dir/run_vasp_single" ]]; then
        echo "[$(timestamp)] ERROR: missing $calc_dir/run_vasp_single; not submitted."
        return 1
    fi
    echo "[$(timestamp)] Scratch resubmission: $calc_dir"
    (cd "$calc_dir" && sbatch run_vasp_single)
}

submit_rerun() {
    local calc_dir=$1
    if [[ ! -f "$calc_dir/run_vasp_single" ]]; then
        echo "[$(timestamp)] ERROR: missing $calc_dir/run_vasp_single; not saved or submitted."
        return 1
    fi
    echo "[$(timestamp)] Saving partial calculation and resubmitting: $calc_dir"
    (cd "$calc_dir" && "$SAVE_CALCULATIONS" && sbatch run_vasp_single)
}

check_folder() {
    local calc_dir=$1
    local check_output
    local check_status

    if check_output="$(cd "$STATE_DIR" && "$CHECK_CONVERGE" --automation "$calc_dir" 2>&1)"; then
        check_status=0
    else
        check_status=$?
    fi

    while IFS= read -r line; do
        [[ -n "$line" ]] && echo "[$(timestamp)] $line"
    done <<< "$check_output"

    case "$check_status" in
        0)
            # The job is still present in Slurm.
            ;;
        10)
            if listed_exactly "$STATE_DIR/list_scratch.txt" "$calc_dir"; then
                submit_scratch "$calc_dir" || true
            else
                echo "[$(timestamp)] ERROR: scratch result was not found in list_scratch.txt; not submitted."
            fi
            ;;
        11)
            if listed_exactly "$STATE_DIR/list_rerun.txt" "$calc_dir"; then
                submit_rerun "$calc_dir" || true
            else
                echo "[$(timestamp)] ERROR: rerun result was not found in list_rerun.txt; not submitted."
            fi
            ;;
        12)
            if record_completed_job "$calc_dir"; then
                DONE_DIRS["$calc_dir"]=1
                echo "[$(timestamp)] Completed folder retired from further checks: $calc_dir"
            else
                echo "[$(timestamp)] ERROR: could not update the job-list files; the folder remains monitored."
            fi
            ;;
        *)
            echo "[$(timestamp)] ERROR: check_converge.py exited with status $check_status; no action taken."
            ;;
    esac
}

echo "[$(timestamp)] Monitoring ${#CALC_DIRS[@]} folder(s); interval: ${interval}s; state directory: $STATE_DIR"
trap 'echo "[$(timestamp)] autocheck stopped."; exit 0' INT TERM

while true; do
    for calc_dir in "${CALC_DIRS[@]}"; do
        if [[ -z "${DONE_DIRS[$calc_dir]+completed}" ]]; then
            check_folder "$calc_dir"
        fi
    done

    if ((${#DONE_DIRS[@]} == ${#CALC_DIRS[@]})); then
        echo "[$(timestamp)] All monitored folders completed; autocheck exiting."
        break
    fi
    if [[ "$run_once" == true ]]; then
        break
    fi
    echo "[$(timestamp)] Next check in ${interval} seconds."
    sleep "$interval"
done
