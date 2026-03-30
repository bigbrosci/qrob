# actions_py/ Usage Guide

This file documents the Python utilities in `actions_py/`. It is organised to make it easy to add more script entries later — each script has a short Purpose, Usage, Examples and Notes subsection.

Table of contents
- [reformat.py](#reformatpy)
- [sort_atoms_by_ele.py](#sort_atoms_by_elepy)
- [How to add an entry](#how-to-add-an-entry)
- [Dependencies](#dependencies)
- [Troubleshooting](#troubleshooting)


## reformat.py

Purpose
- Read a VASP POSCAR/CONTCAR (direct or cartesian coordinates) and write an explicit output in Direct or Cartesian format.

Usage
```
reformat.py FILE [c|d]
```

- `FILE` — input file (e.g. `POSCAR` or `CONTCAR`).
- `c` — output Cartesian coordinates (file: `<input_basename>_cartesian`).
- `d` — output Direct (fractional) coordinates (file: `<input_basename>_direct`).
- Default (if mode omitted): `c` (Cartesian).

Examples
```
reformat.py POSCAR d
# writes POSCAR_direct

reformat.py POSCAR
# writes POSCAR_cartesian (default)
```

Notes
- Output is written beside the input file (same directory).
- ASE version differences: some ASE releases may not accept a writer keyword to force direct/cartesian; the script will attempt to write and warn if necessary.


## sort_atoms_by_ele.py

Purpose
- Reorder atoms in a VASP-format file by element groups.

Usage
```
sort_atoms_by_ele.py FILE [ELE1 ELE2 ...]
```

- `FILE` — input POSCAR or other VASP-format file.
- `ELE1 ELE2 ...` — optional list of element symbols specifying desired order (e.g. `Fe C H O`).
- Default (no element args): group atoms by element in alphabetical order.
- Atoms whose element is not listed are appended afterwards in their original order.

Examples
```
sort_atoms_by_ele.py POSCAR
# writes POSCAR_sorted with atoms grouped alphabetically

sort_atoms_by_ele.py POSCAR Fe C H O
# writes POSCAR_sorted with Fe first, then C, then H, then O, then others
```

Output
- File: `<input_basename>_sorted` written in the same directory as the input.


## How to add an entry

When documenting more scripts, follow this template:

- Title: script filename
- Purpose: one-line summary
- Usage: code block showing command-line usage
- Examples: one or two typical examples
- Notes: any behavior details, side-effects, or version caveats

Keep each entry short and link back to this TOC.


## Dependencies

- ASE (Atomic Simulation Environment) is required for these scripts.

Install with:
```bash
pip install ase
```


## Troubleshooting

- "Cannot read file": ensure the input is a valid POSCAR/CONTCAR or format ASE supports.
- "Permission denied": check file permissions and write access to the directory.
- Writer format differences: if outputs don't appear in the expected coordinate type, try updating ASE.


---

If you'd like, I can also add short unit examples and a `tests/` directory with small POSCAR fixtures to validate these scripts automatically.
# Usage: `reformat.py` and `sort_atoms_by_ele.py`

This document explains how to use the two helper scripts in `actions_py/` that operate on VASP POSCAR files. Both scripts rely on ASE (Atomic Simulation Environment) being available in your Python environment.

## `reformat.py`

Purpose: read a VASP POSCAR (direct or cartesian coordinates) and write a new POSCAR explicitly in Cartesian or Direct coordinates.

Usage:

```
reformat.py FILE [c|d]
```

- `FILE` — input POSCAR (e.g. `POSCAR`, `CONTCAR` or any file ASE understands).
- `c` — write output in Cartesian coordinates (output file: `<input_basename>_cartesian`).
- `d` — write output in Direct (fractional) coordinates (output file: `<input_basename>_direct`).
- If the mode is omitted, the default is `c` (Cartesian).

Examples:

```
reformat.py POSCAR d
# writes POSCAR_direct

reformat.py POSCAR    # default: writes POSCAR_cartesian
```

Notes:
- The script preserves the input file directory and writes the output there.
- If ASE version used does not support the writer keyword to force direct/cartesian, the script will attempt to write the VASP file and warn you.

## `sort_atoms_by_ele.py`

Purpose: reorder atoms in a VASP POSCAR by element grouping.

Usage:

```
sort_atoms_by_ele.py FILE [ELE1 ELE2 ...]
```

- `FILE` — input POSCAR or other VASP-format file.
- `ELE1 ELE2 ...` — optional list of element symbols specifying the desired group order (e.g. `Fe C H O`).
- If no elements are provided, the default behavior is to group atoms by element in alphabetical order.
- Any atoms whose element is not listed in the provided order will be appended after the ordered groups in their original order.

Example:

```
sort_atoms_by_ele.py POSCAR
# writes POSCAR_sorted with atoms grouped alphabetically by element

sort_atoms_by_ele.py POSCAR Fe C H O
# writes POSCAR_sorted with Fe atoms first, then C, then H, then O, then any other elements
```

Output:
- The output filename is `<input_basename>_sorted` written in the same directory as the input file.

## Dependencies

Install ASE in your active Python environment if not already present:

```bash
pip install ase
```

## Troubleshooting

- If a script reports it cannot read the file, ensure the input is a valid POSCAR/CONTCAR or a format ASE supports.
- To convert between fractional and cartesian coordinates reliably, ensure you have a recent ASE version; otherwise the writer may default to one format.

---

If you'd like, I can also add example POSCAR files and a small test harness to demonstrate both scripts automatically.
