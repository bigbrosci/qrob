# QRob Manual

This document keeps the QRob overview, setup notes, and pointers aligned with the repository layout rooted at `~/bin/q-rob`. Use it as the single place to learn how the toolkit is structured, how to activate it, and where to find the scripts, GUIs, and reference data now that the layout and naming have been refreshed.

### 中文说明
本文档保持与 `~/bin/q-rob` 实际结构一致，提供项目组织、启动步骤、工具位置等信息，方便快速掌握 QRob 各个子模块及其用途。

## 1. Goals and big picture

- **What QRob does** – A VASP-focused helper robot: the `brain/` package encodes reusable parsers and parameter dictionaries, the `actions_py/` and `actions_bash/` folders expose concrete CLI helpers on top of that knowledge, and `incar_gui/` delivers a lightweight web interface for composing inputs.
- **How it is organised** – Think of `q-rob` as a single workspace. The `brain/` module contains the logic (INCAR/KPOINTS/POSCAR utilities and dictionaries) and the `actions_*` layers are the commands you run every day. The `books/` and `friends/` folders hold supplemental data and third-party scripts, while the GUI docs live alongside `incar_gui/`.
- **Updates** – Add new parameters in `brain/`, extend CLI helpers in `actions_py/`, or drop new third-party helpers in `friends/`. Most customisations only need you to edit Python dictionaries or add a script, so you generally will not touch the old `Q_robot` naming anymore.

### 中文说明
QRob 就像一个专注 VASP 的机器人：`brain/` 封装参数与读写逻辑，`actions_*` 提供常用命令，`books/`、`friends/` 是外部参考库，各部分独立而互补，维护起来也更容易。

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

Add these lines to your shell startup file (`~/.bashrc`, `~/.zshrc`, `~/.profile`, etc.) so the commands, scripts, and modules are always available. Prepending your existing `PATH` keeps the system defaults first and avoids surprising overrides:

```bash
export QROB_ROOT="$HOME/bin/q-rob"
export PATH="$PATH:$QROB_ROOT/actions_py:$QROB_ROOT/actions_bash"
export PYTHONPATH="$QROB_ROOT/brain${PYTHONPATH:+:$PYTHONPATH}"
```

- Adjust `$HOME/bin/q-rob` if you keep the repo elsewhere.
- If you plan to run VTST scripts from `friends/vtstscripts-1040/`, append that directory to `PATH` as well (e.g., `export PATH="$QROB_ROOT/friends/vtstscripts-1040:$PATH"`).
- Restart your shell or `source` the file to pick up the changes.

### 中文说明
在终端 RC 配置里先定义 `QROB_ROOT`，再把 `actions_py/`、`actions_bash/` 加入 `PATH`，`brain/` 追加到 `PYTHONPATH`，这样命令与模块都能被无缝引用，保留原 `PATH` 顺序。

### 2.3 Getting started with scripts

1. Activate your `qrob` environment.
2. Ensure the repository root is the current working directory so the Python helpers find the `brain/` package.
3. Run a script, e.g., `get_incar.py freq dftd2 ispin` to generate an INCAR file.
4. Most scripts live under `actions_py/` and declare `#!/usr/bin/env python3`, so you can invoke them directly (they handle bootstrapping). When in doubt, inspect `actions_py/USAGE.md` for usage hints on that folder's helpers.

## 3. Repository layout

- `brain/` – Core Python modules that know how to read/write VASP inputs and outputs and contain the dictionaries used to generate settings (INCAR, KPOINTS, lattice helpers, etc.). Reuse these modules when creating new automation scripts or GUI backends.
- `actions_py/` – Python command-line utilities that import `brain` and expose high-level tasks. Key examples:
  - `get_incar.py` – wrap `brain/incar.py`; pass task keywords (`dftd2`, `freq`, `ispin`, `neb`, etc.) or `--list` to see the registered keywords.
  - `ncore.py` – add `NCORE = 8` to `INCAR` by default for non-frequency jobs, or set a custom value such as `ncore.py 16`.
  - `check_converge.py` – inspect `OUTCAR` convergence and sort jobs into good/rerun/scratch tracking lists.
  - `kp.py` – generate KPOINTS files (line, mesh, etc.) from a POSCAR or arguments.
  - `pp.py` – create POTCAR snippets from your inputs.
  - `cssm.py`, `dcenter.py`, `dos_extract.py`, `vtotav.py` – helper calculators for surfaces, DOS, or work functions.
  - `get_bader.py`, `get_mag.py`, `get_bandgap.py`, `zpe.py`, `frequency_correction.py` – analysis utilities that read VASP outputs.
  - `bootstrap.py` – ensures the repo root is in `sys.path` so other scripts can import `brain` (run automatically).
- `actions_bash/` – bash shortcuts that wrap common workflows such as cleaning directories (`rmall.sh`), collecting job metadata (`get_mag.sh`, `liste.sh`), and submitting or cleaning batches (`bader.sh`, `save_calculations.sh`, etc.). These scripts assume the same `PATH` additions as above.
- `books/` – domain knowledge: pseudopotential tables, DFT-D2 parameters, lattice references, and sample structures under `books/structures/`. The `brain/data.py` module imports/extends this raw information.
- `friends/` – third-party helpers we borrow when the work is already done (ASE helpers, VTST utilities, VASPKIT, etc.). Unpack the tarballs if needed and add the extracted `vtstscripts-1040/` (or whichever version you use) to your `PATH` before invoking those helpers.
- `incar_gui/` – Flask-based INCAR generator with its own docs and requirements. See `incar_gui/INTRODUCTION.md` for bootstrapping and `task_config.json` for how the UI maps to `brain/incar` task dictionaries.
- `manual/` – this overview plus supporting files (PowerPoint decks, PDF, figures, and the environment YAML). Keep `manual/qrob_env.yml` in sync with the dependencies you rely on.
- `books/structures/` – example POSCARs and test fixtures used by the GUI or scripts.
- `LICENSE`, `README` – remain as general project metadata.

## 4. Using the Python helpers (`actions_py/`)

- The scripts simply import and reuse `brain/` modules, so any changes you make under `brain/` are instantly available.
- You do not need to copy the repo root to `PYTHONPATH` manually when invoking the scripts; `actions_py/bootstrap.py` registers it automatically.
- Common workflows:
  1. `get_incar.py` – generate an INCAR; pass keywords like `freq`, `dftd2`, `ispin`, `neb`, `single`, `pbe0`, etc. Use `--list` to inspect supported tasks.
  2. `ncore.py` – add `NCORE = 8` to `INCAR` when it is missing on a non-frequency job, or set a custom value.
  3. `kp.py` – produce KPOINTS meshes or line-mode k-paths from a POSCAR or command-line arguments.
  4. `pp.py` – build POTCAR fragments for single or mixed-element jobs.
  5. `cssm.py`, `fix_atoms.py`, `translate.py`, `rotate.py`, etc. – operate on POSCAR files when preparing slabs or defects.
- Refer to `actions_py/USAGE.md` for friendly usage notes for each script, especially `reformat.py` and `sort_atoms.py` (the short README there also explains how to add future entries).

### 中文说明
`actions_py/` 脚本都能一键运行（shebang + bootstrap），它们继承 `brain/` 的知识，适合在项目根目录下直接调用。添加新脚本时，推荐把用法写进 `manual/usage_py.md`。

## 5. Bash helpers (`actions_bash/`)

- These scripts target frequent operations that involve job directories or scheduler metadata.
- Examples:
  - `check_converge.py $JOBDIR` – scan `OUTCAR` convergence and update the tracking lists.
  - `liste.sh` – show job energies from a `list` file, or fall back to scanning subdirectories when `list` is missing.
  - `rmall.sh light` / `rmall.sh deep` – remove temporary VASP outputs with lighter or deeper cleanup modes.
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
- GUI customizations: edit `incar_gui/task_config.json` for new INCAR presets.

## 9. Resources and troubleshooting

- Stay in sync with these files as you develop:
  - `manual/qrob_env.yml` for the Conda environment
  - `actions_py/USAGE.md` for Python helper documentation
  - `incar_gui/INTRODUCTION.md` for GUI-specific tips
- Common issues:
  - **Script import errors** – ensure `PYTHONPATH` includes `brain/` (see the shell bootstrap snippet) and your current shell session loads the `qrob` environment.
  - **Missing dependencies** – install `ase`, `streamlit`, or other packages using `pip install` inside the `qrob` environment; the GUI docs list their extras.
  - **VTST helpers not found** – unpack the tarball and add the extracted directory to `PATH`.
- Need deeper help? Review the PowerPoint (`manual/Q_robot.pptx`, `manual/Q_robot_Introduction.pptx`) and the PDF (`manual/The Q-Robot.pdf`) for slides and diagrams that explain the bigger workflow.

Happy VASP automation! Keep this file aligned with the actual folders so new collaborators can rely on it without hunting for outdated paths. Feel free to rebase this document whenever the layout changes again.
