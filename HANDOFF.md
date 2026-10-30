# QRob Handoff

## Start Here

Open the actual QRob checkout, then read [AGENTS.md](AGENTS.md) and the current
summary in [PROJECT_MEMORY.md](PROJECT_MEMORY.md). The shorthand "开工" means
this handoff procedure. Continue the user's specified task; with no pending
task, report readiness rather than inventing a calculation to run.

Run these read-only checks from the checkout:

```bash
pwd
git status --short
python3 --version
command -v python3
```

Read the relevant implementation and applicable local skill. An open IDE tab
does not change the requested project. APARE is an external reference project;
its MKM parameters, model states, and instructions are not QRob defaults.

## Repository Map

| Area | Purpose |
| --- | --- |
| actions_py/ | Python command entrypoints; current examples in actions_py/USAGE.md |
| brain/ | Shared parsers, parameter data, and helpers |
| actions_bash/ | Shell utilities and Slurm automation |
| tests/ | Existing parser and analysis regression checks |
| install/ | Shell setup snippets and qrob_env.yml |
| incar_gui/ | Separate Flask INCAR interface; see its INTRODUCTION.md |
| manual/ | Broader and historical documentation; verify examples against code |
| .agents/skills/ | Reusable input-preparation and job-triage methods |

## Environment and Portability

The maintained environment recipe is [install/qrob_env.yml](install/qrob_env.yml)
(Python 3.11), with shell snippets [install/bashrc](install/bashrc) and
[install/zshrc](install/zshrc). Older installation examples reference an actions/
directory and manual/qrob_env.yml; use the actual checkout layout instead.
Review shell snippets for this machine before sourcing them. Do not assume
another user's absolute paths, environment, private POTCAR library, or Slurm
commands are available. No installation or shell-profile change is automatic.

The separate `~/bin/qrob_private/anvil/get_potcars.py` uses only the standard
library and is intended for Python 3.5-3.10. Edit its top-level POTCAR_DIR for
the target library. It can be copied out of QRob; neither ASE nor QRob imports
are required. This compatibility scope does not apply to other QRob commands.

## Common Commands

These are examples, not commands executed by opening this document. Run file
generation in the intended calculation directory, with the script path adjusted
to the actual checkout:

```bash
python3 ~/bin/qrob_private/anvil/get_potcars.py
python3 ~/bin/qrob_private/anvil/get_potcars.py Fe C H O
python3 /path/to/qrob/actions_py/reformat.py POSCAR c
python3 /path/to/qrob/actions_py/reformat.py POSCAR d
```

POTCAR output is in the invocation directory. POSCAR conversion output is beside
the input. Check [usage](actions_py/USAGE.md) for ordering and overwrite behavior.

For code changes, use the relevant existing tests from the checkout:

```bash
python3 -m pytest -q tests/test_outcar_readers.py
python3 -m pytest -q tests/test_analysis_efficiency.py
```

Scale verification to the change. Documentation-only edits need link and diff
checks, not physical calculations. A syntax check with Python 3.5 grammar is
not execution on Python 3.5; record the actual interpreter tested. Scheduler
fixtures do not prove live-cluster success.

## Job and Data Boundaries

Check queue state and calculation evidence before recommending a rerun.
check_converge.py can append tracking files even though it does not submit jobs;
--skip-slurm does not prove a job is inactive. autocheck.sh can save and submit
jobs even with --once. Use the job-triage skill before touching these workflows.
Preserve raw files and existing failure records. Submit or resubmit only when
requested by the user. Do not include credentials or private POTCAR contents
in handoff records.

## Finish a Task

Update PROJECT_MEMORY.md with what changed, why, evidence and validation scope,
and the next action. Keep command behavior in USAGE.md, navigation here, and
reusable procedures in skills. Record incomplete work explicitly; do not turn
a proposal, a successful import, or a previous device's check into acceptance.
