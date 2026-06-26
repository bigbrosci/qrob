````markdown
Prerequisites
- Install Anaconda (or Miniconda) first. Download from https://www.anaconda.com or https://docs.conda.io/en/latest/miniconda.html and follow the installer instructions for your platform.

- After installing conda, create the environment for this project using the YAML in `manual/qrob_env.yml`:

```bash
conda env create -f manual/qrob_env.yml
conda activate qrob
```

`actions/` Usage Guide

This file documents small utility scripts in `actions/`. It is organised to make it easy to add more script entries later — each script has a short Purpose, Usage, Examples and Notes subsection.
`actions/` Usage Guide

This file documents small utility scripts in `actions/`. It is organised to make it easy to add more script entries later — each script has a short Purpose, Usage, Examples and Notes subsection.

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


## sort_atoms.py

Purpose

Usage
```
sort_atoms.py -i FILE --mode element [--elements ELE1 ELE2 ...]
```


Examples
```
sort_atoms.py -i POSCAR --mode element
# writes POSCAR_sorted with atoms grouped alphabetically

sort_atoms.py -i POSCAR --mode element --elements Fe C H O
# writes POSCAR_sorted with Fe first, then C, then H, then O, then others

sort_atoms.py -i POSCAR --mode z
# writes POSCAR_sorted with all atoms sorted by Cartesian z

sort_atoms.py -i POSCAR --mode z-within-element --elements Ni C H O
# writes POSCAR_sorted with Ni/C/H/O groups and each group sorted by z
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
