---
name: qrob-vasp-inputs
description: Create, diagnose, or update QRob VASP input preparation tools for POSCAR, INCAR, KPOINTS, and POTCAR.
---

# VASP input preparation

Read the relevant command in `actions_py/`, its shared implementation in `brain/`, and the corresponding usage in `actions_py/USAGE.md` before editing. Use the current code when older manuals disagree with it.

Start from the repository AGENTS.md, PROJECT_MEMORY.md, and HANDOFF.md. Keep
current task status and validation evidence in PROJECT_MEMORY.md, not this skill.
Reuse the existing implementation; inspect only task-related code and fixtures.

- For POSCAR structure transformations, check lattice and coordinate mode, atom and species order, selective-dynamics flags, and whether ASE adds an unwanted velocity block. Preserve information the caller needs downstream. Treat atom indices as 0-based where the command uses ASE indices.
- For INCAR defaults and magnetic moments, inspect `brain/incar.py` and the existing `get_incar.py` or `update_incar.py` path. Keep shared parameter data there rather than creating another copy.
- For POTCAR creation, inspect `actions_py/pp.py` and `brain/potcar.py`. Automatic lookup prefers `./POSCAR`, then `./00/POSCAR` for NEB; the output belongs in the invocation directory. Keep element order consistent with the source POSCAR.
- For the separate portable POTCAR utility, locate
  `~/bin/qrob_private/anvil/get_potcars.py` (outside this repository). Preserve its
  standard-library-only design and Python 3.5-3.10 requirement. Its editable
  POTCAR_DIR is independent of pp.py's library discovery. Preserve argument and
  POSCAR species order, including repeats; exact potential variants must not
  silently select a different variant. Resolve/copy all inputs before replacing
  an existing output. Use synthetic potentials for checks rather than embedding
  private library contents in tests or documentation.
- For KPOINTS, use the existing `kp.py` and shared helpers where possible. Check the requested calculation type before changing mesh or path defaults.

Verify changed behavior with a small representative input and focused syntax or existing tests. Report any tool or pseudopotential dependency unavailable in the current environment.

For standalone compatibility changes, check both syntax and standard-library
API availability (including pre-3.6 path handling); do not equate a modern
interpreter's grammar check with running every supported version. For structure
changes, compare cell, coordinates, element order, constraints, and tail policy.
Keep raw inputs intact and distinguish raw DFT, ZPE, and thermal quantities.
Do not import another project's slab references or correction defaults.

State exactly what was exercised locally and what remains unverified on the
target machine. Update command usage when behavior changes and record the task
in PROJECT_MEMORY.md before delivery.
