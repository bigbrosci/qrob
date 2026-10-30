# QRob project guidance

## Startup and handoff

QRob is the target repository; another project's documentation may inform the
workflow but does not authorize edits to that project or supply QRob's scientific
defaults. Resolve the actual repository root before changing files.

At startup, after a context reset, or when the user says "开工":

1. Read this file, [PROJECT_MEMORY.md](PROJECT_MEMORY.md), and
   [HANDOFF.md](HANDOFF.md). Reuse unchanged material already read this session.
2. Follow the user's current task; otherwise use the latest memory's next step.
   Check the worktree and relevant implementation before assuming old status.
3. Read only the applicable local skill and task-related command, shared helper,
   usage, and tests. Prefer current code to historical manual examples.
4. Report confirmed state, remaining work, and the next action. Startup alone
   does not request job submission, resubmission, cleanup, or scientific changes.

Before delivery, update PROJECT_MEMORY.md with the task/date, changed paths,
evidence, checks and limitations, and remaining work/next command. Distinguish
user reports, code inspection, synthetic checks, and live cluster validation.
Keep the current summary short and preserve dated history. Update HANDOFF.md
when entrypoints or cross-device steps change; keep reusable methods in skills,
not task status. Do not create parallel agent.md/memory.md state files.

## Scope, Reuse, and Device State

- Search existing implementations first, using focused reads and bounded output.
  Preserve user changes; do not perform unrelated refactors or copy large datasets
  to prepare a handoff. Git history records tracked edits; preserve original
  scientific inputs separately before an authorized overwrite.
- Shared repository history is distinct from device facts: interpreter, installed
  packages, PATH, mounts, fonts, scheduler access, and POTCAR availability must be
  checked on the device doing the work. Same environment names do not prove
  equivalent installations. Record only necessary non-sensitive device evidence.
- Preserve saved calculation paths, hashes, raw outputs, and failures. Path changes
  or synchronization do not authorize rewriting provenance or declaring success.
  A local process check cannot establish another machine's job or sync state.
- Independent utilities explicitly requested by the user may use only the standard
  library. In particular, get_potcars.py must remain standalone and Python
  3.5-3.10 compatible; this is not a repository-wide compatibility promise.

## Scientific and Engineering Guidance

- QRob is a VASP utility repository. Reusable parsers and parameter data live in `brain/`; executable Python commands live in `actions_py/`; shell and Slurm helpers live in `actions_bash/`. `incar_gui/` is a separate Flask interface. Check the current script and `actions_py/USAGE.md` before assuming an older manual example is current.
- Approach VASP questions with scientific rigor: check the calculation goal, VASP version, INCAR tags, POSCAR/KPOINTS/POTCAR consistency, convergence settings, and units. For version-sensitive behavior or uncertain tag interactions, consult the [VASP Wiki](https://vasp.at/wiki/) and distinguish documented behavior from an inference about this project's scripts.
- Use ASE and pymatgen competently for structure building, conversion, and analysis. Choose the library that fits the existing code and task; check its current API when uncertain. When converting between libraries or writing VASP files, verify species order, cell, coordinates, constraints/selective dynamics, and magnetic moments.
- Design high-throughput HPC workflows for repeatability and failure recovery: make job inputs and outputs traceable, handle partial or failed runs without silent data loss, respect scheduler and cluster-specific resources, and avoid needless full-file scans or duplicate calculations. Inspect the target cluster's modules, launcher, and queue policy before changing submission behavior.
- Keep shared parsing and parameter logic in `brain/` when more than one command needs it. Preserve the command-line interface and calculation-file conventions of existing `actions_py/` tools unless the task calls for changing them.
- Current magnetic-moment database values are in `brain/incar.py`. `actions_py/mol2poscar.py` and `actions_py/sort_atoms.py` are the retained implementations; check there before adding or restoring a duplicate utility.
- VASP inputs and outputs may be large or scientifically sensitive. Inspect headers, tails, and the relevant records first; use the streaming/reverse readers in `brain/outcar.py` for final values where appropriate. Distinguish `energy(sigma->0)` from TOTEN when reporting energy.
- In structure edits, preserve the intended cell, atom ordering, selective-dynamics flags, and element order required by downstream POSCAR/POTCAR files. Use ASE's 0-based atom indices when a script specifies indices.
- `check_converge.py` checks Slurm state before classifying finished jobs. `autocheck.sh` can save and resubmit jobs, so inspect its list files and effects before running it on a cluster. Do not submit or resubmit a job unless the user requests that action.
- Use focused existing tests under `tests/` and syntax checks for changed Python or shell files. For cluster operations, validate with fixtures or mocks when possible; report what was not exercised on a live scheduler.

Use the `qrob-vasp-inputs` skill for POSCAR, INCAR, KPOINTS, and POTCAR preparation, and `qrob-vasp-job-triage` for convergence and Slurm job investigations.
