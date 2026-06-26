# Bash helper scripts

The `actions_bash/` folder collects quick shell wrappers for common VASP chores (convergence checks, log cleanup, and utility helpers) that complement the Python `actions_py/` scripts. Add `~/bin/qrob/actions_bash` to your `PATH` (see `manual/QRob.md`) so you can run these helpers from any job directory. Most of the scripts assume you are inside the job folder or have access to the standard VASP outputs (`OUTCAR`, `CONTCAR`, etc.).

## 中文说明
`actions_bash/` 提供的脚本都是纯 Bash 实现，适合在含有 VASP 输出的工作目录里直接执行，主要用于清理、检查、备份、提取磁矩/能量等常见操作。只需把目录加入 `PATH` 后就能按名字调用。

## Per-script usage

### `bader.sh`
- **Purpose:** Produce charge-summing input before running the VTST `bader` utility.
- **Usage:** `bader.sh`
- **Details:** Runs `chgsum.pl AECCAR0 AECCAR2` to generate `CHGCAR_sum`, then invokes `bader CHGCAR -ref CHGCAR_sum`.

### `bk.sh`
- **Purpose:** Safely back up a file or directory by creating a gzipped `.tar.gz` archive and removing the original.
- **Usage:** `bk.sh <file-or-dir>`
- **Details:** Checks for existence, archives the target, and reports the archive path.

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
- **Details:** Calls `liste.sh`, sorts the reported energies, and prints the job name reported by the VTST helper.

### `liste.sh`
- **Purpose:** Display the most recent energy for jobs in `list`, or scan subdirectories when `list` is absent.
- **Usage:** `liste.sh`
- **Details:** If a `list` file exists, it reads job names from there; otherwise it falls back to scanning subdirectories like the old `ta.sh`. It prints one tab-separated `<job> <energy>` line per matching `OUTCAR`.

### `rmall.sh`
- **Purpose:** Unified cleanup helper for light or deep VASP file removal.
- **Usage:** `rmall.sh [light|deep] [--dry-run]`
- **Details:** `light` removes logs and common temporary outputs; `deep` removes everything from `light` plus large charge/wavefunction files such as `CHG*`, `WAVE*`, `AE*`, `DOS*`, and `PRO*`. Use `--dry-run` to preview matches before deletion.

### `save_calculations.sh`
- **Purpose:** Archive the main output files by appending a suffix, keeping the current run’s data intact.
- **Usage:** `save_calculations.sh [tag]`
- **Details:** Moves `CONTCAR`, `POSCAR`, `OUTCAR`, `DOSCAR`, `XDATCAR`, `OSZICAR`, and `vasprun.xml` to versions with the tag (or an auto-incremented number) and copies the tagged `CONTCAR` back to `POSCAR`.

### `zpe.sh`
- **Purpose:** Estimate the zero-point energy correction from `OUTCAR` vibrational frequencies.
- **Usage:** `zpe.sh`
- **Details:** Sums the `f  =` energy terms, divides by 2000, and prints the resulting value.

## Tips
- These scripts are most reliable when run from the same directory that contains the VASP outputs they read or modify.
- Check `actions_bash/` directly if you need to tweak a script for your scheduler or naming conventions; they are intentionally simple so you can adapt them quickly.

### 中文说明
确保在包含 `OUTCAR`/`CONTCAR` 的目录下运行这些脚本，必要时根据你的作业系统调整脚本内容。本手册为集中式文档，其内容与 `manual/usage_py.md` 配合使用，可快速了解全部 Bash 与 Python 工具。
