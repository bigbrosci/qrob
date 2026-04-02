#!/usr/bin/env python3
"""Convenience launcher for the INCAR GUI and CLI helpers."""

import os
import sys
from pathlib import Path
import subprocess


def launch_cli(argv):
    """Delegate to the old CLI helper when arguments are provided."""
    from actions_py.get_incar_cli import main as cli_main

    cli_main(argv)


def launch_gui():
    """Run the Flask-based INCAR GUI."""
    gui_script = Path(__file__).resolve().parent.parent / "incar_gui" / "app.py"
    if not gui_script.exists():
        print(f"Error: GUI script not found at {gui_script}", file=sys.stderr)
        sys.exit(1)

    env = os.environ.copy()
    try:
        subprocess.run([sys.executable, str(gui_script)], check=True, env=env)
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)


def main():
    args = sys.argv[1:]

    if args:
        launch_cli(args)
    else:
        launch_gui()


if __name__ == "__main__":
    main()
