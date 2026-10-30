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

Output retains selective-dynamics flags and ends after the expected atom
coordinates; the optional velocity block is removed. If trimming fails, the
script prints a warning; check the output before using it.

## get_potcars.py (Standalone)

This separate utility lives at `~/bin/qrob_private/anvil/get_potcars.py`, outside
the QRob repository (moved on 2026-10-30).

Requires only the Python standard library; intended for Python 3.5-3.10.
It can run outside this repository without ASE or QRob modules. Edit POTCAR_DIR
near the top of the file; its initial value is
`/anvil/projects/x-chm260090/bin/potcars`.

```bash
get_potcars.py
get_potcars.py Fe C H O
get_potcars.py Fe_pv O
```

- No arguments: read ./POSCAR, falling back to ./00/POSCAR for NEB.
- Explicit arguments: preserve the given order, including repeated entries.
- For each name, look up `<POTCAR_DIR>/<name>/POTCAR`; a bare element also
  falls back to `<element>_sv/POTCAR`. Explicit variants use only their exact name.
- VASP5 reads the element/count header. VASP4 requires a title containing only
  element symbols matching the count groups; otherwise give explicit arguments.
- Write ./POTCAR, replacing an existing output only after copying succeeds.
  Missing potentials or invalid input leave an existing POTCAR unchanged.

With the script outside PATH, use `python3 /path/to/get_potcars.py` followed by
the same arguments. Python compatibility does not imply the entire QRob
repository supports those versions. The repository-integrated alternative is
pp.py with brain/potcar.py and its own library discovery rules.

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

- Structure tools such as reformat.py and sort_atoms.py require ASE.
  The standalone get_potcars.py does not.
- Many other maintained commands live beside them in `actions_py/`; read the script header or `registry.py` for quick hints on dependencies and outputs.

## Efficient analysis of large outputs

Scalar OUTCAR readers in `brain/outcar.py` read backwards in 64 KiB chunks and
stop at the last matching record. Final energy, Fermi level, magnetization,
geometry, and iteration lookups no longer load and index the entire OUTCAR.
Frequency and convergence analyses stream through the records they need.
Convergence classification and automation exit codes remain unchanged.

Energy readers retain their energy definitions: `get_energy()` returns
`energy(sigma->0)`, while `get_toten()` returns free-energy TOTEN.
`get_GS_species.py` retains its explicit TOTEN fallback. The shared frequency
reader preserves repeated modes; individual thermochemistry scripts retain
their existing deduplication and cutoff policies.

These readers are used by the thermochemistry, magnetization, bandgap,
NEB plotting, database update, and job-checking commands. `zpe.py` needs ASE
only when `--temperature` is requested. Geometry manipulation and
thermochemistry continue to use ASE. `get_mag_ase.py` retains its ASE-based
reader for selecting arbitrary ionic frames.

Additional changes reduce intermediate storage: XML-to-ML_AB conversion
streams calculation elements, MD coordinate extraction streams frames,
`dcenter.py` loads the DOS table once and integrates using NumPy, and
POTCAR concatenation copies data in chunks. APIs that return all configurations
still retain those requested results in memory.

The legacy Gaussian-log utility (using `gpm`) has moved to
`deprecated/get_energy.py`; it is not a VASP energy command. There is no `get_energies.py` in this checkout. For a single
VASP energy from Python, use `brain.outcar.get_energy("path/to/OUTCAR")`.

Validation: run `python -m pytest -q`. ASE is needed for the geometry and ML_AB
integration tests; lxml additionally enables interrupted-XML recovery tests.
