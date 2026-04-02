# QRob Manual

This document keeps the QRob overview, setup notes, and pointers aligned with the repository layout rooted at `~/bin/qrob`. Use it as the single place to learn how the toolkit is structured, how to activate it, and where to find the scripts, GUIs, and reference data now that the layout and naming have been refreshed.

## 1. Goals and big picture

- **What QRob does** – A VASP-focused helper robot: the `brain/` package encodes reusable parsers and parameter dictionaries, the `actions_py/` and `actions_bash/` folders expose concrete CLI helpers on top of that knowledge, and the `incar_gui/` / `geo_gui/` folders deliver lightweight web interfaces for composing inputs and editing structures.
- **How it is organised** – Think of `qrob` as a single workspace. The `brain/` module contains the logic (INCAR/KPOINTS/POSCAR utilities and dictionaries) and the `actions_*` layers are the commands you run every day. The `books/` and `friends/` folders hold supplemental data and third-party scripts, while the GUIs live under their own directories with dedicated docs.
- **Updates** – Add new parameters in `brain/`, extend CLI helpers in `actions_py/`, or drop new third-party helpers in `friends/`. Most customisations only need you to edit Python dictionaries or add a script, so you generally will not touch the old `Q_robot` naming anymore.

## 2. Quick start

### 2.1 Create the Python environment

1. Ensure `conda` or `mamba` is installed. The pinned environment is under `manual/qrob_env.yml`.
2. From the repo root, run either:
   ```bash
   mamba env create -f manual/qrob_env.yml
   # or
   conda env create -f manual/qrob_env.yml
   ```
3. Activate it with `conda activate qrob`. If you prefer a different name, edit the `name:` field in the YAML before creating the environment.
4. If you use tools that need extra packages (`streamlit`, `flask`, `py3Dmol`, etc.), install them with `pip install` while the `qrob` env is active. Some GUIs also ship their own `requirements.txt` files (`incar_gui/requirements.txt`).

### 2.2 Shell configuration

Add these lines to your shell startup file (`~/.bashrc`, `~/.zshrc`, `~/.profile`, etc.) so the commands, scripts, and modules are always available:

```bash
export QROB_ROOT="$HOME/bin/qrob"
export PATH="$QROB_ROOT/actions_py:$QROB_ROOT/actions_bash:$PATH"
export PYTHONPATH="$QROB_ROOT/brain${PYTHONPATH:+:$PYTHONPATH}"
```

- Adjust `$HOME/bin/qrob` if you keep the repo elsewhere.
- If you plan to run VTST scripts from `friends/vtstscripts-1040/`, append that directory to `PATH` as well (e.g., `export PATH="$QROB_ROOT/friends/vtstscripts-1040:$PATH"`).
- Restart your shell or `source` the file to pick up the changes.

### 2.3 Getting started with scripts

1. Activate your `qrob` environment.
2. Ensure the repository root is the current working directory so the Python helpers find the `brain/` package.
3. Run a script, e.g., `get_incar.py freq dftd2 ispin` to generate an INCAR file.
4. Most scripts live under `actions_py/` and declare `#!/usr/bin/env python3`, so you can invoke them directly (they handle bootstrapping). When in doubt, inspect `actions_py/USAGE.md` for usage hints on that folder's helpers.

## 3. Repository layout

- `brain/` – Core Python modules that know how to read/write VASP inputs and outputs and contain the dictionaries used to generate settings (INCAR, KPOINTS, lattice helpers, etc.). Reuse these modules when creating new automation scripts or GUI backends.
- `actions_py/` – Python command-line utilities that import `brain` and expose high-level tasks. Key examples:
  - `get_incar.py` – wrap `brain/incar.py`; pass task keywords (`dftd2`, `freq`, `ispin`, `neb`, etc.) or `--list` to see the registered keywords.
  - `kp.py` – generate KPOINTS files (line, mesh, etc.) from a POSCAR or arguments.
  - `pp.py` – create POTCAR snippets from your inputs.
  - `cssm.py`, `dcenter.py`, `dos_extract.py`, `vtotav.py` – helper calculators for surfaces, DOS, or work functions.
  - `get_bader.py`, `get_mag.py`, `get_bandgap.py`, `zpe.py`, `freq_correction.py` – analysis utilities that read VASP outputs.
  - `bootstrap.py` – ensures the repo root is in `sys.path` so other scripts can import `brain` (run automatically).
- `actions_bash/` – bash shortcuts that wrap common workflows such as cleaning directories (`clean_light.sh`, `clean_deep.sh`), collecting job metadata (`check_converge.sh`, `get_mag.sh`, `liste.sh`), and submitting or cleaning batches (`bader.sh`, `save_calculations.sh`, etc.). These scripts assume the same `PATH` additions as above.
- `books/` – domain knowledge: pseudopotential tables, DFT-D2 parameters, lattice references, and sample structures under `books/structures/`. The `brain/data.py` module imports/extends this raw information.
- `friends/` – third-party helpers we borrow when the work is already done (ASE helpers, VTST utilities, VASPKIT, etc.). Unpack the tarballs if needed and add the extracted `vtstscripts-1040/` (or whichever version you use) to your `PATH` before invoking those helpers.
- `incar_gui/` – Flask-based INCAR generator with its own docs and requirements. See `incar_gui/INTRODUCTION.md` for bootstrapping and `task_config.json` for how the UI maps to `brain/incar` task dictionaries.
- `geo_gui/` – Streamlit POSCAR viewer/editor with 3D controls, docs under `geo_gui/docs/`, and a comprehensive README. Run it with `streamlit run geo_gui/geo_gui.py` once your environment satisfies the dependencies listed in that README.
- `manual/` – this overview plus supporting files (PowerPoint decks, PDF, figures, and the environment YAML). Keep `manual/qrob_env.yml` in sync with the dependencies you rely on.
- `books/structures/` – example POSCARs and test fixtures used by the GUI or scripts.
- `LICENSE`, `README` – remain as general project metadata.

## 4. Using the Python helpers (`actions_py/`)

- The scripts simply import and reuse `brain/` modules, so any changes you make under `brain/` are instantly available.
- You do not need to copy the repo root to `PYTHONPATH` manually when invoking the scripts; `actions_py/bootstrap.py` registers it automatically.
- Common workflows:
  1. `get_incar.py` – generate an INCAR; pass keywords like `freq`, `dftd2`, `ispin`, `neb`, `single`, `pbe0`, etc. Use `--list` to inspect supported tasks.
  2. `kp.py` – produce KPOINTS meshes or line-mode k-paths from a POSCAR or command-line arguments.
  3. `pp.py` – build POTCAR fragments for single or mixed-element jobs.
  4. `cssm.py`, `fix_by_layer.py`, `translate.py`, `rotate.py`, etc. – operate on POSCAR files when preparing slabs or defects.
- Refer to `actions_py/USAGE.md` for friendly usage notes for each script, especially `reformat.py` and `sort_atoms_by_ele.py` (the short README there also explains how to add future entries).

## 5. Bash helpers (`actions_bash/`)

- These scripts target frequent operations that involve job directories or scheduler metadata.
- Examples:
  - `check_converge.sh $JOBDIR` – scan the log for convergence warnings.
  - `liste.sh` – show running or queued jobs with extra context.
  - `clean_light.sh` / `clean_deep.sh` – remove temporary VASP outputs while keeping inputs.
  - `zpe.sh`, `bader.sh` – wrap ASE/VTST tools for specific property calculations.
- You can call them directly after exporting the `actions_bash/` directory into your `PATH`.
- Open the scripts to understand the scheduler/environment assumptions before using them on a supercomputer.

## 6. GUI tools

### INCAR GUI (`incar_gui/`)
- Activate the `qrob` environment.
- Run `pip install -r incar_gui/requirements.txt` inside the GUI directory (Flask + Async tools).
- Start the server with `python incar_gui/app.py` and visit the printed `http://127.0.0.1:5001`.
- Update `incar_gui/task_config.json` to add new preset tasks or reorganise sections; the UI automatically reloads the new configuration.
- Use ASE when you want the GUI to read your POSCAR for MAGMOM or DFT+U presets.
- See `incar_gui/INTRODUCTION.md` for additional tips (multi-language notes, environment scripts, etc.).

### GEO GUI (`geo_gui/`)
- Install the dependencies: `streamlit`, `py3Dmol`, `numpy`, `ase` (optional) inside the `qrob` environment.
- Launch `streamlit run geo_gui/geo_gui.py` from the repo root.
- The app lets you load a POSCAR/CONTCAR, edit atoms, translate, delete, and save the result from the browser.
- Read `geo_gui/README.md` for workflow summaries and `geo_gui/docs/` for step-by-step guidance.

## 7. Books, friends, and reports

- `books/data` populates `brain/data.py` with useful dictionaries (lattice constants, DFT-D2 parameters, atomic masses, magnetisation targets, etc.). Edit `brain/data.py` to update or extend these reference tables.
- `books/structures/` holds example POSCARs (e.g., `bulk.vasp`, `surface.vasp`) that the GUI or scripts can use as fixtures.
- `friends/` contains third-party vaults:
  - The `vtstscripts-1040/` directory bundles the VTST toolkit. Add it to `PATH` (`export PATH="$QROB_ROOT/friends/vtstscripts-1040:$PATH"`) before calling scripts such as `nebmake.py`.
  - Unpack `friends/vtstscripts.tgz`/`vtstcode-213.tgz` if you need older versions; the repo keeps both for reference.
- The `reports/` directory (if you add it) would host output summaries. Currently, raw outputs are created in your working directories when running the helpers.

## 8. Extending the robot

- Add new dictionaries in `brain/incar.py` (`standard_incar`, `tasks_incar`) when you need custom parameter blocks.
- When developing new CLI helpers, place them in `actions_py/`, import the necessary `brain` modules, and document the usage within `actions_py/USAGE.md`.
- Use `books` as your data source: convert new reference tables into Python dictionaries or JSON and load them through `brain/data.py`.
- GUI customizations: edit `incar_gui/task_config.json` for new INCAR presets and tweak `geo_gui/docs/` for updated tutorials.

## 9. Resources and troubleshooting

- Stay in sync with these files as you develop:
  - `manual/qrob_env.yml` for the Conda environment
  - `actions_py/USAGE.md` for Python helper documentation
  - `incar_gui/INTRODUCTION.md` and `geo_gui/README.md` for GUI-specific tips
- Common issues:
  - **Script import errors** – ensure `PYTHONPATH` includes `brain/` (see the shell bootstrap snippet) and your current shell session loads the `qrob` environment.
  - **Missing dependencies** – install `ase`, `streamlit`, or other packages using `pip install` inside the `qrob` environment; the GUI docs list their extras.
  - **VTST helpers not found** – unpack the tarball and add the extracted directory to `PATH`.
- Need deeper help? Review the PowerPoint (`manual/Q_robot.pptx`, `manual/Q_robot_Introduction.pptx`) and the PDF (`manual/The Q-Robot.pdf`) for slides and diagrams that explain the bigger workflow.

Happy VASP automation! Keep this file aligned with the actual folders so new collaborators can rely on it without hunting for outdated paths. Feel free to rebase this document whenever the layout changes again.
