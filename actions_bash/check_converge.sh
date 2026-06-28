#!/bin/bash

INPUT_PATH=$1

if [[ -z "$INPUT_PATH" ]]; then
    echo "Usage: $0 OUTCAR_or_calc_dir"
    exit 1
fi

RESULTS_FILE="check_results.txt"
GOOD_LIST="list_good.txt"
BAD_LIST="list_bad.txt"
RERUN_LIST="list_rerun.txt"
SCRATCH_LIST="list_scratch.txt"

if [[ -d "$INPUT_PATH" ]]; then
    CALC_DIR=$(cd "$INPUT_PATH" && pwd)
    OUTCAR_FILE="$CALC_DIR/OUTCAR"
else
    OUTCAR_FILE="$INPUT_PATH"
    CALC_DIR=$(cd "$(dirname "$OUTCAR_FILE")" && pwd)
fi

if [[ ! -f "$OUTCAR_FILE" ]]; then
    echo "$CALC_DIR, Bad: OUTCAR not found. Ionic: 0, NSW: 0, Electronic: 0, NELM: 0." >> "$RESULTS_FILE"
    echo "$CALC_DIR" >> "$BAD_LIST"
    echo "$CALC_DIR" >> "$SCRATCH_LIST"
    echo "$CALC_DIR, Action: scratch." >> "$RESULTS_FILE"
    exit 0
fi

NSW=$(grep -m 1 "NSW" "$OUTCAR_FILE" | awk '{print $3}')
NELM=$(grep -m 1 "NELM" "$OUTCAR_FILE" | awk '{print $3}')

LAST_ITER=$(grep "Iter" "$OUTCAR_FILE" | tail -n 1 | sed 's/-//g' | sed 's/Iteration//g')
IONIC_STEP=$(echo "$LAST_ITER" | awk -F'(' '{print $1}' | tr -d ' ')
ELECTRONIC_STEP=$(echo "$LAST_ITER" | awk -F'(' '{print $2}' | tr -d ') ')

if [[ -z "$NSW" ]]; then
    NSW=0
fi

if [[ -z "$NELM" ]]; then
    NELM=0
fi

if [[ -z "$IONIC_STEP" ]]; then
    IONIC_STEP=0
fi

if [[ -z "$ELECTRONIC_STEP" ]]; then
    ELECTRONIC_STEP=0
fi

mark_bad() {
    local reason=$1
    local action

    echo "$CALC_DIR, Bad: $reason Ionic: $IONIC_STEP, NSW: $NSW, Electronic: $ELECTRONIC_STEP, NELM: $NELM." >> "$RESULTS_FILE"
    echo "$CALC_DIR" >> "$BAD_LIST"

    if [[ "$IONIC_STEP" -gt 1 ]]; then
        action="rerun"
        echo "$CALC_DIR" >> "$RERUN_LIST"
    else
        action="scratch"
        echo "$CALC_DIR" >> "$SCRATCH_LIST"
    fi

    echo "$CALC_DIR, Action: $action." >> "$RESULTS_FILE"
}

# Reliable convergence markers:
# - relaxation jobs: "reached required accuracy"
# - static / single-step jobs: "aborting loop because EDIFF is reached"
if [[ "$NSW" -le 1 ]]; then
    if grep -q "aborting loop because EDIFF is reached" "$OUTCAR_FILE" && [[ "$NELM" -gt "$ELECTRONIC_STEP" ]]; then
        echo "$CALC_DIR, Good: Job converged. Ionic: $IONIC_STEP, NSW: $NSW, Electronic: $ELECTRONIC_STEP, NELM: $NELM." >> "$RESULTS_FILE"
        echo "$CALC_DIR" >> "$GOOD_LIST"
    else
        mark_bad "Single-point calculation did not converge or was terminated."
    fi
else
    if grep -q "reached required accuracy" "$OUTCAR_FILE" && [[ "$NELM" -gt "$ELECTRONIC_STEP" ]]; then
        echo "$CALC_DIR, Good: Job converged. Ionic: $IONIC_STEP, NSW: $NSW, Electronic: $ELECTRONIC_STEP, NELM: $NELM." >> "$RESULTS_FILE"
        echo "$CALC_DIR" >> "$GOOD_LIST"
    else
        mark_bad "Relaxation did not converge or was terminated."
    fi
fi

