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
- `delete_atoms.py` – remove atoms identified by element or zero-based index range; usage `delete_atoms.py POSCAR C 0 5` produces `POSCAR_deleted` and `atom_deleted` (a plain-text list of the removed atoms and their Cartesian coordinates).
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

## Merged legacy helpers

The local merge adds a larger legacy toolbox into `actions_py/`. Many of these scripts predate the newer curated wrappers, so their CLIs are less uniform, but they are now kept in the clone because they add useful structure editing, slab building, analysis, and literature helpers.

### Structure building & geometry editing

- `add.py` – add one structure or fragment onto another POSCAR-like geometry.
- `add_NH3_bri.py` – place an `NH3` adsorbate on a bridge site.
- `add_NH3_hollow.py` – place an `NH3` adsorbate on a hollow site.
- `add_NH3_top.py` – place an `NH3` adsorbate on a top site.
- `add_thiol_top.py` – place a thiol-like adsorbate on a top site.
- `add_top.py` – add an adsorbate to a top site on a slab.
- `bottom_slab.py` – normalize slab height by shifting the bottom layer to a chosen reference.
- `cart2dire.py` – convert Cartesian coordinates to direct coordinates.
- `cell_convert.py` – convert cell/coordinate representations for VASP structures.
- `cell_modify.py` – edit lattice vectors or cell dimensions for a structure.
- `center_atom.py` – move a selected atom to the cell center or a chosen reference position.
- `contcar_to_mol.py` – extract a molecule-like fragment from `CONTCAR`.
- `delete.py` – delete selected atoms from a structure using the legacy interface.
- `delete_H.py` – remove hydrogen atoms from a structure.
- `dihedral.py` – calculate or inspect a dihedral angle from selected atoms.
- `dire2cart.py` – convert direct coordinates to Cartesian coordinates.
- `fix_Ru.py` – apply selective-dynamics constraints tuned for Ru slab models.
- `fix_atoms.py` – freeze selected atoms with legacy selective-dynamics logic.
- `get_active_sites.py` – identify likely adsorption sites on a surface structure.
- `get_intact_mol.py` – detect or extract intact molecular fragments from a slab calculation.
- `get_poscar.py` – generate or rewrite a `POSCAR` from intermediate data.
- `get_poscar_from_g09.py` – convert Gaussian output into a VASP `POSCAR`.
- `get_slab.py` – build a slab model from a bulk structure.
- `get_top_sites.py` – enumerate top-site adsorption positions on a surface.
- `get_z.py` – report z-coordinate information for selected atoms or layers.
- `hbond_correct.py` – apply geometry corrections for hydrogen-bonded structures.
- `merge.py` – merge two structures or datasets into a combined output.
- `rotate.py` – rotate a structure or selected atoms.
- `rotate_gas.py` – rotate a gas-phase molecule before adsorption or placement.
- `sort_atoms_manually.py` – reorder atoms with an explicit user-provided sequence.
- `sortcar.py` – sort atoms in a POSCAR-like file using the older sorting workflow.
- `swap_poscar_atoms.py` – swap atom positions or identities inside a POSCAR.
- `switch_layers.py` – exchange or relabel slab layers.
- `wrap_atoms.py` – wrap atoms back into the unit cell.
- `xyz2mol.py` – convert XYZ coordinates into a molecule representation for downstream workflows.

### Analysis, energetics, and data extraction

- `bm.py` – legacy Birch-Murnaghan fitting helper for equation-of-state data.
- `calc_NH.py` – compute N-H related geometric or energetic descriptors.
- `calc_NH_bond.py` – measure or analyze N-H bond lengths.
- `calc_hbonds.py` – identify and measure hydrogen bonds in a structure.
- `check.py` – run a compact status or sanity check on common VASP outputs.
- `check_bad_geos.py` – flag problematic or distorted geometries.
- `check_data.py` – validate simple tabular or calculation data files.
- `check_geo.py` – inspect geometry consistency for a single structure.
- `check_geo_Ru.py` – geometry checker specialized for Ru systems.
- `check_geos.py` – batch-check many geometry folders from one command.
- `d2_dic.py` – expose DFT-D2 correction constants or lookup data.
- `entropy.py` – estimate entropic contributions from tabulated molecular data.
- `freq_correction.py` – legacy frequency-based correction helper.
- `get_G_NxHy.py` – estimate free-energy terms for NxHy species.
- `get_bib.py` – extract bibliography information from stored references.
- `get_data_infor.py` – collect summary information from calculation outputs.
- `get_energy.py` – print energies from VASP outputs using the legacy interface.
- `get_entropy.py` – retrieve entropy estimates for known gas-phase species.
- `get_file_name_from_log.py` – recover referenced file names from log files.
- `get_gas_N2.py` – prepare or analyze gas-phase `N2` reference calculations.
- `get_pdf_infor.py` – extract metadata or text snippets from PDF files.
- `get_species_entropy.py` – return entropy values for a named species.
- `get_zpe_from_outcar.py` – read zero-point energy information directly from `OUTCAR`.
- `job_check.py` – summarize job-state or calculation health for one or more folders.
- `job_path.py` – report calculation paths associated with tracked jobs.
- `linear_fit.py` – run a simple linear regression on tabulated data.
- `model_sim.py` – compare model outputs or calculate similarity metrics.
- `overlap.py` – compute overlap-like metrics between datasets or structures.
- `plot_lienar.py` – legacy plotting helper for linear-fit data.
- `plot_neb.py` – plot NEB energy profiles from image folders.
- `q_get_bader.py` – older Bader charge extraction helper.
- `ring_count.py` – count ring motifs in a molecular graph or structure.
- `work_plot_08_30.py` – project-specific plotting helper preserved from the legacy tree.
- `wplot.py` – generic plotting helper for workflow data.
- `xps.py` – estimate or summarize XPS-related shifts/data from calculations.

### Electronic-structure setup

- `convert_xml_to_ml_ab_input.py` – turn `vasprun.xml`-style outputs into machine-learning adsorption/binding input tables.
- `get_Ru_bulk.py` – generate an hcp Ru bulk structure with ASE.
- `hseband.py` – prepare inputs for HSE band-structure calculations.
- `hsekpoints.py` – generate HSE-friendly `KPOINTS`.
- `id_to_cif.py` – fetch or convert a material identifier into a CIF file.
- `in.py` – legacy INCAR generation shortcut.
- `incar.py` – older command-line entry for building `INCAR` settings.
- `md.py` – helper for molecular dynamics style VASP setups.
- `nscf_pdos.py` – prepare non-self-consistent PDOS calculations.
- `pbeband.py` – prepare PBE band-structure calculations.
- `pbekpoints.py` – generate PBE band-structure `KPOINTS`.

### Literature and project utilities

- `bibreader.py` – read and search locally stored bibliography entries.

### Notes for merged scripts

- Exact flags vary more than in the curated helpers above; if a merged script is unfamiliar, run it without arguments first or inspect its header for the original usage text.
- These scripts were preserved because they are still useful, not because they all share the same interface standard.

## Notes

- Many scripts assume the standard VASP outputs (`POSCAR`, `OUTCAR`, `DOSCAR`, `CONTCAR`, `EIGENVAL`). Keep a backup before overwriting anything in place.
- If you want to add a new helper, add the CLI under `actions_py/`, import `ensure_repo_root()`, and document the usage here so collaborators know where to look.
- This manual replaces the former `actions_py/USAGE.md` and centralizes the documentation for both Python and Bash helpers (see `manual/bash_usage.md`).

### 中文提示
常见脚本依赖 `POSCAR`/`OUTCAR` 等 VASP 文件，新增工具时请保持与 `brain/` 数据一致，并在本手册留下说明，方便团队查阅。
