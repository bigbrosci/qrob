# Python helper scripts

The `actions_py/` folder gathers the Python utilities that wrap the `brain/` knowledge into runnable tools. Each script is a portable CLI (shebang + bootstrap) so that once your `qrob` environment is activated and `~/bin/qrob/actions_py` is on `PATH`, you can run them directly (for example `get_incar.py dftd2 ispin`). Every script imports `actions_py.bootstrap.ensure_repo_root()` so it knows how to reach the shared `brain` modules regardless of the current directory.

## 中文说明
`actions_py/` 中的 Python 工具继承了 `brain/` 的模型与参数字典，通过 shebang + `ensure_repo_root()` 实现跨目录执行。激活 `qrob` 环境并将 `actions_py/` 目录加入 `PATH` 后，就能在任何含 VASP 文件的目录里通过脚本名称快速生成 INCAR、处理 POSCAR、提取磁矩等常见任务。

## Running the helpers

1. Activate the `qrob` Conda environment (see `manual/qrob_env.yml`).
2. Add `~/bin/qrob/actions_py` (or wherever the repo lives) to `PATH` so the scripts behave like standard commands.
3. Run a helper from a job directory that contains the expected input files (`POSCAR`, `OUTCAR`, etc.).
4. If a script requires ASE, NumPy, or SciPy, install them inside the `qrob` environment (the README for each GUI lists extras if needed).

## Script reference

### Bootstrapping & metadata

- `bootstrap.py` – adds the repo root to `sys.path`. It runs automatically inside every helper and does not need to be invoked directly.
- `registry.py` – exposes structured metadata (description, usage, required files) for the other helpers; useful when introspecting scripts from automation.
- `atom_selector.py` – compatibility shim that re-exports `brain.poscar.parse_atom_targets` so other scripts can parse element names and index lists with a simple import.

### Surface & POSCAR editing

- `bottom.py` – reads `POSCAR`/`CONTCAR`, shifts the structure so the lowest atom is at a fixed Z (default +0.1 Å), and writes `_bottomed` output; run from the job folder with `python bottom.py` or just `bottom.py` when `PATH` is set.
- `center_atoms.py` – centers and wraps the atoms in a POSCAR to the cell center; usage: `center_atoms.py POSCAR` and the script writes `POSCAR_centered`.
- `cssm.py` – generates Slab POSCARs for the metals listed in `brain.data.dict_metals`; simply run `cssm.py` to cleave multiple surfaces (bcc 110, hcp 0001, fcc 111) and write the resulting files with the appropriate element line already inserted.
- `expand.py` – expands a VASP cell by integer multiples; call `expand.py POSCAR Nx Ny Nz` to produce `POSCARex` with the enlarged supercell.
- `move_atoms.py` – copies atom subsets from `file_from` to `file_to` (e.g., transfer adsorbates between slabs); invoke via `move_atoms.py POSCAR_small POSCAR_large C H 12`.
- `move_slab.py` – adjusts a slab so the bottom atom is at `z≈0.2 Å` and adds 15 Å vacuum on top; run `move_slab.py` (it reads `POSCAR` and writes `POSCAR_new`).
- `translate.py` – apply a translation vector or move specific atoms; pass `-x`, `-y`, `-z` or use point pairs `-a` / `-b` with `-s` to select atoms.
- `swap_atoms.py` – replace selected atoms between two files by specifying `-A`, `-B`, `-s` (source indices), and `-f` (replacements); see the script help for exact flags.
- `switch_atoms.py` – switch the chemical symbols of two atoms in a single POSCAR: `python switch_atoms.py 8 Mo 20 Ni` swaps atom 8 to Mo and atom 20 to Ni.
- `reformat.py` – convert coordinates between direct and cartesian; usage `reformat.py POSCAR d` (or `c`) and the output file is named `<input>_direct` (or `_cartesian`).
- `sort_atoms_by_ele.py` – group atoms by element; call `sort_atoms_by_ele.py POSCAR Fe C H O` (or omit the element order to use alphabetical grouping) to write `<input>_sorted`.
- `delete_atoms.py` – remove atoms identified by element or zero-based index range; usage `delete_atoms.py POSCAR C 0 5` produces `POSCAR_deleted`.
- `fix_by_atoms.py`, `fix_by_layer.py`, `fix_by_z.py` – set selective dynamics flags:
  - `fix_by_atoms.py` accepts target lists (indices/elements) plus three-character flag strings (e.g., `TTF`).
  - `fix_by_layer.py` constrains the bottom N layers of a slab based on grouped z coordinates.
  - `fix_by_z.py zcut [FILE]` fixes atoms with z < `zcut` and writes `<input>_fixed`.
- `frequency_correction.py` – (still experimental) inspects `OUTCAR` frequencies, identifies the largest imaginary mode, and rewrites the structure for subsequent calculations.
- `xyz_to_poscar.py` – convert an `.xyz` file to `POSCAR`; usage: `xyz_to_poscar.py molecule.xyz [OUTPOSCAR]`.

### Calculators & utilities

- `get_incar.py` – wraps `brain.incar.build_incar`; pass keywords like `freq`, `dftd2`, `ispin`, `neb`, or `--list` to see supported tasks. Running `get_incar.py` without arguments now launches the Flask GUI instead of printing an INCAR.
- `get_abc.py` – reads `POSCAR`/`CONTCAR` and prints the lattice lengths, face areas, and volume.
- `kp.py` – generates `KPOINTS` from `POSCAR` or hand-crafted meshes; run `kp.py` in a folder with `POSCAR` and let the default mesh (3×3×1) or existing file drive the output.
- `pp.py` – build `POTCAR` fragments by reading the local `POSCAR`; just run `pp.py` and it will select the required potentials from `brain.potcar`.
- `plot_dft.py` – plot DFT results. Usage examples: `plot_dft.py --type linear -i data.csv` for linear regressions or `plot_dft.py --type neb --name JOBNAME` to visualize NEB energies. It supports `--dirs` to specify subdirectories.
- `vtotav.py` – average a LOCPOT/CHGCAR file along a direction to produce one-dimensional curves; call `vtotav.py LOCPOT z`.
- `dos_extract.py` – sum DOS for selected atoms/orbitals by reading `DOSCAR` and `POSCAR`; usage `dos_extract.py C s DOS_out.dat` (select atoms and output file name).
- `dcenter.py` – integrate `.dat` files (e.g., produced by `dos_extract.py`) to compute d-band center between a start/end energy.
- `get_dimer.py` – prepare the POSCAR needed for a dimer calculation after a frequency run (requires `IBRION=5`/`NWRITE=3`); simply run `get_dimer.py` to generate the IDM-friendly structure.
- `get_dis_AB.py` – print the distance between two atom indices: `get_dis_AB.py 0 3`.
- `get_fcc_bulk.py` – regenerate an fcc POSCAR: `get_fcc_bulk.py Pt 3.92` writes `POSCAR` using ASE’s `bulk` builder.
- `bm_fitting.py` – fit Birch–Murnaghan data; supply a CSV with lattice parameter and energy columns (e.g., `bm_fitting.py data.csv`).
- `get_bader.py` – parse `ACF.dat` and `POTCAR` to gather Bader charges alongside ZVAL information; run `get_bader.py POSCAR` after the `bader` run.
- `get_bandgap.py` – compute band-edge energies from `OUTCAR`/`EIGENVAL`; pass optional directory/`;g` to tune the Fermi level.
- `get_mag.py` & `get_mag_ase.py` – print per-atom magnetizations; the former uses `brain.outcar.get_mag` (can take element/index selectors), while the latter relies purely on ASE and supports `--outcar`, `--index`, and JSON/text outputs.
- `get_mass_center.py` – calculate the center of mass from `POSCAR`/`CONTCAR`, optionally write a `DIPOL` line back into an `INCAR` file.
- `zpe.py` – read `OUTCAR` frequencies via `brain.outcar.get_freq` and print the zero-point energy (ZPE) in eV.

### 中文说明
本节列出的脚本包含结构编辑（`translate.py` / `move_slab.py`）、参数生成（`get_incar.py`, `kp.py`）、物理分析（`get_bader.py`, `zpe.py`）等场景。若添加新工具，请在 `actions_py/` 新建脚本、使用 `ensure_repo_root()` 并同步更新本手册。

## Notes

- Many scripts assume the standard VASP outputs (`POSCAR`, `OUTCAR`, `DOSCAR`, `CONTCAR`, `EIGENVAL`). Keep a backup before overwriting anything in place.
- If you want to add a new helper, add the CLI under `actions_py/`, import `ensure_repo_root()`, and document the usage here so collaborators know where to look.
- This manual replaces the former `actions_py/USAGE.md` and centralizes the documentation for both Python and Bash helpers (see `manual/bash_usage.md`).

### 中文提示
常见脚本依赖 `POSCAR`/`OUTCAR` 等 VASP 文件，新增工具时请保持与 `brain/` 数据一致，并在本手册留下说明，方便团队查阅。
