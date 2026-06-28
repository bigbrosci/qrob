#!/usr/bin/env python3
"""Check VASP convergence status from an OUTCAR path or calculation directory."""

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

import argparse

from brain.outcar import summarize_convergence


RESULTS_FILE = "check_results.txt"
GOOD_LIST = "list_good.txt"
BAD_LIST = "list_bad.txt"
RERUN_LIST = "list_rerun.txt"
SCRATCH_LIST = "list_scratch.txt"


def append_line(path: str, text: str) -> None:
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(text + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check convergence from an OUTCAR file or calculation directory.")
    parser.add_argument("input_path", help="Path to OUTCAR or a calculation directory containing OUTCAR")
    args = parser.parse_args()

    summary = summarize_convergence(args.input_path)
    calc_dir = str(summary.calc_dir)

    if summary.converged:
        append_line(
            RESULTS_FILE,
            f"{calc_dir}, Good: {summary.reason} Ionic: {summary.ionic_step}, NSW: {summary.nsw}, "
            f"Electronic: {summary.electronic_step}, NELM: {summary.nelm}.",
        )
        append_line(GOOD_LIST, calc_dir)
        return 0

    append_line(
        RESULTS_FILE,
        f"{calc_dir}, Bad: {summary.reason} Ionic: {summary.ionic_step}, NSW: {summary.nsw}, "
        f"Electronic: {summary.electronic_step}, NELM: {summary.nelm}.",
    )
    append_line(BAD_LIST, calc_dir)

    if summary.action == "rerun":
        append_line(RERUN_LIST, calc_dir)
    else:
        append_line(SCRATCH_LIST, calc_dir)

    append_line(RESULTS_FILE, f"{calc_dir}, Action: {summary.action}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
