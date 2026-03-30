````markdown
Prerequisites
- Install Anaconda (or Miniconda) first. Download from https://www.anaconda.com or https://docs.conda.io/en/latest/miniconda.html and follow the installer instructions for your platform.

- After installing conda, create the environment for this project using the YAML in `manual/qrob_env.yml`:

```bash
conda env create -f manual/qrob_env.yml
conda activate qrob
```

`actions_py/` Usage Guide

See `manual/brain_actions_registry.md` for the Brain ↔ Actions interface map and the new action registry.

This file documents small utility scripts in `actions_py/`. It is organised to make it easy to add more script entries later — each script has a short Purpose, Usage, Examples and Notes subsection. Shell-based helpers are now collected under `actions_bash/`.

Table of contents


## reformat.py

Purpose

Usage
```
reformat.py FILE [c|d]
```


Examples
```
reformat.py POSCAR d
# writes POSCAR_direct

reformat.py POSCAR
# writes POSCAR_cartesian (default)
```

Notes


## sort_atoms_by_ele.py

Purpose

Usage
```
sort_atoms_by_ele.py FILE [ELE1 ELE2 ...]
```


Examples
```
sort_atoms_by_ele.py POSCAR
# writes POSCAR_sorted with atoms grouped alphabetically

sort_atoms_by_ele.py POSCAR Fe C H O
# writes POSCAR_sorted with Fe first, then C, then H, then O, then others
```

Output


## How to add an entry

When documenting more scripts, follow this template:


Keep each entry short and link back to this TOC.


## Dependencies


Install with:
```bash
pip install ase
```


## Troubleshooting




If you'd like, I can also add short unit examples and a `tests/` directory with small POSCAR fixtures to validate these scripts automatically.
