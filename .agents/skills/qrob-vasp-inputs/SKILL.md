---
name: qrob-vasp-inputs
description: Create, diagnose, or update QRob VASP input preparation tools for POSCAR, INCAR, KPOINTS, and POTCAR.
---

# VASP input preparation

Read the relevant command in `actions_py/`, its shared implementation in `brain/`, and the corresponding usage in `actions_py/USAGE.md` before editing. Use the current code when older manuals disagree with it.

- For POSCAR structure transformations, check lattice and coordinate mode, atom and species order, selective-dynamics flags, and whether ASE adds an unwanted velocity block. Preserve information the caller needs downstream. Treat atom indices as 0-based where the command uses ASE indices.
- For INCAR defaults and magnetic moments, inspect `brain/incar.py` and the existing `get_incar.py` or `update_incar.py` path. Keep shared parameter data there rather than creating another copy.
- For POTCAR creation, inspect `actions_py/pp.py` and `brain/potcar.py`. Automatic lookup prefers `./POSCAR`, then `./00/POSCAR` for NEB; the output belongs in the invocation directory. Keep element order consistent with the source POSCAR.
- For KPOINTS, use the existing `kp.py` and shared helpers where possible. Check the requested calculation type before changing mesh or path defaults.

Verify changed behavior with a small representative input and focused syntax or existing tests. Report any tool or pseudopotential dependency unavailable in the current environment.
