# actions_py Usage Guide

This file documents a few core scripts in `actions_py/`. Use it as a starting point for the maintained Python-side CLI tools.

## reformat.py

Purpose
- Read a VASP POSCAR/CONTCAR and rewrite it explicitly in Direct or Cartesian coordinates.

Usage
```bash
reformat.py FILE [c|d]
```

- `FILE`: input structure file.
- `c`: write `<input>_cartesian`.
- `d`: write `<input>_direct`.
- Default mode is `c`.

Examples
```bash
reformat.py POSCAR d
reformat.py CONTCAR
```

## sort_atoms.py

Purpose
- Reorder atoms in a VASP-format file by element groups.

Usage
```bash
sort_atoms.py -i FILE --mode element [--elements ELE1 ELE2 ...]
```

- `FILE`: input POSCAR or compatible VASP-format file.
- `ELE1 ELE2 ...`: optional desired element order.
- If no elements are provided, atoms are grouped alphabetically.

Examples
```bash
sort_atoms.py -i POSCAR --mode element
sort_atoms.py -i POSCAR --mode element --elements Fe C H O
sort_atoms.py -i POSCAR --mode z
sort_atoms.py -i POSCAR --mode z-within-element --elements Ni C H O
```

## Notes

- These scripts expect ASE in the active Python environment.
- Many other maintained commands live beside them in `actions_py/`; read the script header or `registry.py` for quick hints on dependencies and outputs.
