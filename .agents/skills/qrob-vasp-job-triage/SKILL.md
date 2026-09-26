---
name: qrob-vasp-job-triage
description: Diagnose QRob VASP calculation status, OUTCAR convergence, and Slurm monitoring or resubmission workflows.
---

# VASP job triage

Read `actions_py/check_converge.py`, `brain/outcar.py`, and `actions_bash/autocheck.sh` for the specific task. Review the calculation directory, its Slurm work directory, `OUTCAR`, log tail, and tracking lists before proposing a rerun.

1. Check whether the calculation is still running or pending in Slurm. `check_converge.py` matches jobs by work directory; active jobs are left unclassified. If Slurm is unavailable, its `--skip-slurm` option classifies output off-cluster, but does not establish that a job is inactive.
2. For a finished job, use the existing convergence summary and relevant log tail to distinguish completed, scratch-restart, and partial-rerun cases. Avoid reading a whole large OUTCAR merely to obtain final values; reuse the shared readers where they fit.
3. If considering `autocheck.sh`, inspect its job-list mode, `list_scratch.txt`, `list_rerun.txt`, `job_done.txt`, and `run_vasp_single`. The script may call `save_calculations.sh` and `sbatch`; running even `--once` can resubmit. Do not start it merely to inspect a job.
4. For a requested automation change, preserve its existing status-code contract and test the active, completed, scratch, and rerun branches with mocked Slurm commands before using it on a live cluster.

Explain the evidence for the classification and identify any missing scheduler or output data. Submit or resubmit only as part of a user-requested job action.
