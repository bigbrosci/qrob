# QROB

QROB is a workflow-oriented toolkit for routine VASP work. It is organized like
an assistant robot for computational materials tasks: generate INCAR settings,
inspect and edit POSCAR structures, and run small day-to-day utilities around
common calculations.

## Project layout

- `brain/`: reusable core logic for VASP-related parsing and parameter
  generation.
- `actions_py/` and `actions_bash/`: Python utilities and Bash helpers built on top of `brain/` and ASE.
- `incar_gui/`: Flask interface for interactive INCAR generation.
- `geo_gui/`: Streamlit interface for viewing and editing POSCAR structures.
- `manual/`: installation, usage notes, slides, and environment setup.
- `books/`: example/reference structures and related data files.
- `friends/`: bundled third-party helper scripts.

## Quick start

- Installation docs: `manual/INSTALL.md`
- Usage docs: `manual/USAGE.md`
- Run the INCAR interface: `python incar_gui/app.py`
- Run the geometry interface: `streamlit run geo_gui/geo_gui.py`

## Direction

The long-term goal of QROB is to make routine VASP operations feel like using a
small domain-specific robot: `brain` provides reusable knowledge, `actions`
provide concrete operations, and the GUI modules provide visual interaction for
model building and input preparation.
