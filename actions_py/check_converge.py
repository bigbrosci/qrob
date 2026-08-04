#!/usr/bin/env python3
"""Report Slurm state, then classify a finished VASP calculation.

Active jobs are deliberately not inspected or added to any result list.  Once a
calculation directory is no longer present in ``squeue``, its OUTCAR and the
tail of vasp.log are used to classify it as completed or failed.
"""

from __future__ import annotations

import argparse
from collections import deque
import getpass
from pathlib import Path
import subprocess
import sys


repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

from brain.outcar import ConvergenceSummary, summarize_convergence


RESULTS_FILE = "check_results.txt"
GOOD_LIST = "list_good.txt"
BAD_LIST = "list_bad.txt"
RERUN_LIST = "list_rerun.txt"
SCRATCH_LIST = "list_scratch.txt"
FAILED_LIST = "failed_list.txt"
KILLED_MARKER = "KILLED BY SIGNAL:"
AUTOMATION_SCRATCH = 10
AUTOMATION_RERUN = 11
AUTOMATION_COMPLETED = 12


def append_line(path: str | Path, text: str) -> None:
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(text + "\n")


def calculation_paths(input_path: str | Path) -> tuple[Path, Path]:
    """Return the absolute calculation directory and OUTCAR path."""
    resolved = Path(input_path).expanduser().resolve()
    if resolved.is_dir():
        return resolved, resolved / "OUTCAR"
    if resolved.is_file() or resolved.name == "OUTCAR":
        return resolved.parent, resolved
    # The command's only supported file input is OUTCAR, so a missing path with
    # any other name is best treated as an intended calculation directory.
    return resolved, resolved / "OUTCAR"


def slurm_jobs_for_directory(calc_dir: Path, user: str) -> list[tuple[str, str]]:
    """Return ``(job id, state)`` entries whose Slurm WorkDir is calc_dir."""
    try:
        process = subprocess.run(
            ["squeue", "-h", "-u", user, "-o", "%A|%T|%Z"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("squeue is not installed or is not in PATH") from exc

    if process.returncode != 0:
        detail = process.stderr.strip() or "squeue returned an error"
        raise RuntimeError(detail)

    requested = calc_dir.resolve()
    matches: list[tuple[str, str]] = []
    for raw_line in process.stdout.splitlines():
        parts = raw_line.split("|", 2)
        if len(parts) != 3:
            continue
        job_id, state, work_dir = (part.strip() for part in parts)
        if not work_dir:
            continue
        try:
            queued_dir = Path(work_dir).expanduser().resolve()
        except OSError:
            continue
        if queued_dir == requested:
            matches.append((job_id, state or "UNKNOWN"))
    return matches


def log_was_killed(log_path: Path, tail_lines: int = 100) -> bool:
    """Look for a Slurm kill marker near the end of the VASP log."""
    if not log_path.is_file():
        return False
    with log_path.open(encoding="utf-8", errors="ignore") as handle:
        return any(KILLED_MARKER in line for line in deque(handle, maxlen=tail_lines))


def record_completed(summary: ConvergenceSummary) -> None:
    calc_dir = str(summary.calc_dir)
    append_line(
        RESULTS_FILE,
        f"{calc_dir}, Good: {summary.reason} Ionic: {summary.ionic_step}, NSW: {summary.nsw}, "
        f"Electronic: {summary.electronic_step}, NELM: {summary.nelm}.",
    )
    append_line(GOOD_LIST, calc_dir)


def record_failed(summary: ConvergenceSummary, killed: bool) -> None:
    calc_dir = str(summary.calc_dir)
    reason = (
        "vasp.log reports KILLED BY SIGNAL."
        if killed
        else summary.reason
    )
    append_line(
        RESULTS_FILE,
        f"{calc_dir}, Bad: {reason} Ionic: {summary.ionic_step}, NSW: {summary.nsw}, "
        f"Electronic: {summary.electronic_step}, NELM: {summary.nelm}.",
    )
    append_line(BAD_LIST, calc_dir)
    if killed:
        append_line(FAILED_LIST, calc_dir)

    action = summary.action or ("rerun" if summary.ionic_step > 1 else "scratch")
    append_line(RERUN_LIST if action == "rerun" else SCRATCH_LIST, calc_dir)
    append_line(RESULTS_FILE, f"{calc_dir}, Action: {action}.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Report whether a VASP calculation is still in Slurm. Only jobs no "
            "longer in the queue are checked for convergence or failure."
        )
    )
    parser.add_argument(
        "input_path",
        help="Calculation directory, or its OUTCAR file",
    )
    parser.add_argument(
        "--user",
        default=getpass.getuser(),
        help="Slurm user to query (default: current user)",
    )
    parser.add_argument(
        "--skip-slurm",
        action="store_true",
        help="Skip the queue query and classify immediately (useful off-cluster)",
    )
    parser.add_argument(
        "--automation",
        action="store_true",
        help=(
            "Return status 10 for scratch, 11 for rerun, and 12 for completed; "
            "active jobs return 0"
        ),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    calc_dir, outcar_path = calculation_paths(args.input_path)

    if not calc_dir.is_dir():
        print(f"Error: calculation directory does not exist: {calc_dir}", file=sys.stderr)
        return 2

    if not args.skip_slurm:
        try:
            active_jobs = slurm_jobs_for_directory(calc_dir, args.user)
        except RuntimeError as exc:
            print(f"Error: cannot determine Slurm status: {exc}", file=sys.stderr)
            print("No result files were changed. Use --skip-slurm to classify off-cluster.", file=sys.stderr)
            return 2

        if active_jobs:
            for job_id, state in active_jobs:
                print(f"Job {job_id} is {state} in Slurm: {calc_dir}")
            print("The job is still active; no convergence or failure files were changed.")
            return 0

        print(f"No active Slurm job found for {calc_dir}; checking finished-job output.")

    summary = summarize_convergence(outcar_path)
    killed = log_was_killed(calc_dir / "vasp.log")

    if summary.converged and not killed:
        record_completed(summary)
        print(f"COMPLETED: {calc_dir} ({summary.reason})")
        if args.automation:
            return AUTOMATION_COMPLETED
    else:
        record_failed(summary, killed)
        reason = "KILLED BY SIGNAL" if killed else summary.reason
        action = summary.action or ("rerun" if summary.ionic_step > 1 else "scratch")
        print(f"FAILED: {calc_dir} ({reason}) Action: {action}.")
        if args.automation:
            return AUTOMATION_RERUN if action == "rerun" else AUTOMATION_SCRATCH
    return 0


if __name__ == "__main__":
    sys.exit(main())
