#!/usr/bin/env python3
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