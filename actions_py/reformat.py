#!/usr/bin/env python3
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()
"""Convert VASP POSCAR (direct/cartesian) and save with explicit name.

Usage:
  reformat.py FILE [c|d]

If mode is `c` -> write Cartesian coordinates (output: <name>_cartesian)
If mode is `d` -> write Direct coordinates (output: <name>_direct)
If mode omitted -> default is convert to Cartesian (same as `c`).
"""
import sys
import os
import argparse
import ase
from ase.io import read, write

def main():
	parser = argparse.ArgumentParser(description="Convert VASP POSCAR between direct and cartesian output formats")
	parser.add_argument("file", help="Input file (e.g. POSCAR)")
	parser.add_argument("mode", nargs="?", choices=["c", "d"], help="Output mode: c=cartesian, d=direct (default: c)")
	args = parser.parse_args()

	infile = args.file
	mode = args.mode or "c"

	if not os.path.exists(infile):
		print(f"Error: input file '{infile}' does not exist.")
		sys.exit(2)

	try:
		# Read the input file and strip trailing blank lines. ASE's VASP reader
		# may assert when trailing empty lines are present (e.g. while
		# attempting to parse velocities). Creating a file-like object with
		# trailing blanks removed avoids that issue.
		from io import StringIO
		with open(infile, 'r', encoding='utf-8') as fh:
			lines = fh.readlines()

		# Remove only trailing blank/whitespace-only lines
		while lines and lines[-1].strip() == "":
			lines.pop()

		# Use a file-like object and specify VASP format explicitly
		s = StringIO(''.join(lines))
		atoms = read(s, format='vasp')
	except Exception:
		# Fallback: try reading the original file to surface the original error
		try:
			atoms = read(infile)
		except Exception as e:
			print(f"Error: failed to read '{infile}': {e}")
			sys.exit(3)

	base = os.path.basename(infile)
	name, ext = os.path.splitext(base)
	if name == "":
		name = base

	if mode == "c":
		out_name = f"{name}_cartesian"
		direct_flag = False
	else:
		out_name = f"{name}_direct"
		direct_flag = True

	# Preserve directory of input file for output
	out_path = os.path.join(os.path.dirname(infile) or ".", out_name)

	try:
		# ASE's VASP writer supports the `direct` keyword to choose fractional coordinates
		write(out_path, atoms, format="vasp", vasp5=True, direct=direct_flag)
	except TypeError:
		# In case older ASE doesn't accept `direct` kw, fall back to writing and warn
		if direct_flag:
			print("Warning: ASE writer does not accept 'direct' keyword; writing default VASP format (may be cartesian).")
		write(out_path, atoms, format="vasp", vasp5=True)

	print(f"Wrote '{out_path}' ({'direct' if direct_flag else 'cartesian'})")

if __name__ == "__main__":
	main()
