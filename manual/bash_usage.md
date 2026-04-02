# Bash helper scripts

The `actions_bash/` folder collects quick shell wrappers for common VASP chores (convergence checks, log cleanup, and utility helpers) that complement the Python `actions_py/` scripts. Add `~/bin/qrob/actions_bash` to your `PATH` (see `manual/QRob.md`) so you can run these helpers from any job directory. Most of the scripts assume you are inside the job folder or have access to the standard VASP outputs (`OUTCAR`, `CONTCAR`, etc.).

## Per-script usage

### `bader.sh`
- **Purpose:** Produce charge-summing input before running the VTST `bader` utility.
- **Usage:** `bader.sh`
- **Details:** Runs `chgsum.pl AECCAR0 AECCAR2` to generate `CHGCAR_sum`, then invokes `bader CHGCAR -ref CHGCAR_sum`.

### `bk.sh`
- **Purpose:** Safely back up a file or directory by creating a gzipped `.tar.gz` archive and removing the original.
- **Usage:** `bk.sh <file-or-dir>`
- **Details:** Checks for existence, archives the target, and reports the archive path.

### `check_converge.sh`
- **Purpose:** Inspect `OUTCAR` to flag convergence (ionic/electronic) issues and log successes/failures.
- **Usage:** `check_converge.sh OUTCAR`
- **Details:** Prints NSW/NELM/last-iteration info, appends summaries to `check_results.out`, and writes “good” or “bad” job names to `list_good.txt` or `list_bad.txt` respectively.

### `clean_deep.sh`
- **Purpose:** Aggressively delete temporary VASP files and outputs when you need to reclaim disk space.
- **Usage:** Run from a job directory: `clean_deep.sh`
- **Details:** Removes charge/wavefunction files, logs, DOS/PROCAR data, `POTCAR`, `IB*`, and similar artifacts below the current directory (using `find`).

### `clean_light.sh`
- **Purpose:** Less aggressive clean of logs, kpoints, and temporary VASP outputs while keeping core inputs.
- **Usage:** `clean_light.sh`
- **Details:** Deletes `.log`, `e.*`, `o.*`, `REPORT*`, `PCDAT*`, etc., but leaves structural inputs like `CONTCAR`, `POSCAR`, and `INCAR` untouched.

### `ej.sh`
- **Purpose:** Enter the working directory of a Slurm job (uses `scontrol`).
- **Usage:** `ej.sh <job-id>`
- **Details:** Reads the `WorkDir` of the job, cds into it, and optionally drops you into a shell for inspection.

### `get_mag.sh`
- **Purpose:** Extract magnetization entries from `OUTCAR` for particular atoms or the entire block.
- **Usage:** `get_mag.sh <atom-index> [index …]` or `get_mag.sh all`
- **Details:** Assumes `OUTCAR` plus `CONTCAR`/`POSCAR` are present; the script prints the requested lines from the last magnetization block.

### `get_ts.sh`
- **Purpose:** Pick a transition-state image from multiple NEB directories for follow-up frequency calculations.
- **Usage:** `get_ts.sh`
- **Details:** Calls `ta.sh`, sorts results, and prints the job name reported by the VTST helper.

### `liste.sh`
- **Purpose:** Display the most recent energy listed in each directory mentioned in a `list` file.
- **Usage:** `liste.sh`
- **Details:** Reads job names from `list`, looks for `OUTCAR`, and prints the “without” energy line for each job; useful for tracking progress across a sweep.

### `ncore.sh`
- **Purpose:** Update the `NCORE` setting in `INCAR` while respecting VASP restrictions.
- **Usage:** `ncore.sh <num-cores>`
- **Details:** Removes `NCORE` if `IBRION` is 5–8 (unsupported) and otherwise replaces/sets `NCORE = <num>` with a backup file `INCAR.bak`.

### `rmall.sh`
- **Purpose:** Remove a standard collection of auxiliary VASP files quickly.
- **Usage:** `rmall.sh`
- **Details:** Uses a single `find` command to delete `CHG*`, `WAVE*`, `AE*`, `err.*`, `out.*`, `REPORT*`, `PCDAT*`, and similar temporary files.

### `save_calculations.sh`
- **Purpose:** Archive the main output files by appending a suffix, keeping the current run’s data intact.
- **Usage:** `save_calculations.sh [tag]`
- **Details:** Moves `CONTCAR`, `POSCAR`, `OUTCAR`, `DOSCAR`, `XDATCAR`, `OSZICAR`, and `vasprun.xml` to versions with the tag (or an auto-incremented number) and copies the tagged `CONTCAR` back to `POSCAR`.

### `ta.sh`
- **Purpose:** List job directories alongside their final energy (the “without” energy extracted from `OUTCAR`).
- **Usage:** `ta.sh`
- **Details:** Iterates over subdirectories, prints `<job>,<energy>` for each job that contains an `OUTCAR`.

### `zpe.sh`
- **Purpose:** Estimate the zero-point energy correction from `OUTCAR` vibrational frequencies.
- **Usage:** `zpe.sh`
- **Details:** Sums the `f  =` energy terms, divides by 2000, and prints the resulting value.

## Tips
- These scripts are most reliable when run from the same directory that contains the VASP outputs they read or modify.
- Check `actions_bash/` directly if you need to tweak a script for your scheduler or naming conventions; they are intentionally simple so you can adapt them quickly.
