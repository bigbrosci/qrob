#!/usr/bin/env python3
"""Launch the INCAR GUI or generate an INCAR from task keywords."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()

from brain import incar as brain_incar


def list_tasks() -> None:
    print("Supported INCAR tasks:")
    print(" ".join(sorted(brain_incar.tasks_recorded)))


def launch_gui() -> None:
    gui_script = Path(__file__).resolve().parent.parent / "incar_gui" / "app.py"
    if not gui_script.exists():
        print(f"Error: GUI script not found at {gui_script}", file=sys.stderr)
        sys.exit(1)

    env = os.environ.copy()
    try:
        subprocess.run([sys.executable, str(gui_script)], check=True, env=env)
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)


def run_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Produce an INCAR file from brain/incar.py",
        epilog="Run without arguments to launch the INCAR GUI. Use --list to print task keywords.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("tasks", nargs="*", help="Task keywords such as dftu, neb, ispin")
    parser.add_argument("--list", "-l", action="store_true", help="List supported task keywords")
    args = parser.parse_args(argv)

    if args.list:
        list_tasks()
        return 0

    try:
        brain_incar.build_incar(args.tasks)
        task_msg = f" (tasks: {' '.join(args.tasks)})" if args.tasks else ""
        print(f"INCAR generated from brain/incar.py{task_msg}")
        return 0
    except brain_incar.UnsupportedTasksError as exc:
        print(exc, file=sys.stderr)
        return 1


def main() -> int:
    args = sys.argv[1:]
    if args:
        return run_cli(args)

    launch_gui()
    return 0


if __name__ == "__main__":
    sys.exit(main())
