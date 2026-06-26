#!/usr/bin/env python3
"""Helpers for monitoring VASP jobs, primarily on Slurm systems."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import getpass
import re
import shutil
import subprocess
from typing import Iterable

try:
    from .outcar import summarize_convergence
except ImportError:
    from outcar import summarize_convergence


DEFAULT_REPORT = Path.home() / "bin" / "Q_robot" / "reports" / "job_list.txt"


@dataclass
class SlurmJob:
    job_id: str
    state: str | None = None
    name: str | None = None
    work_dir: str | None = None
    raw: str | None = None


@dataclass
class JobCalcStatus:
    calc_dir: Path
    incar_exists: bool
    oszicar_exists: bool
    outcar_exists: bool
    nelm_incar: int
    nsw_incar: int
    nelm_oszicar: int
    nsw_oszicar: int
    converged: bool
    finished: bool
    warning: str | None = None


def _run_command(command: list[str]) -> str:
    process = subprocess.run(command, capture_output=True, text=True)
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip() or f"Command failed: {' '.join(command)}")
    return process.stdout


def get_line(file_in: str, look_up: str) -> tuple[int, list[str]]:
    line_num = 0
    with open(file_in, encoding="utf-8", errors="ignore") as data_in:
        lines = data_in.readlines()
    for num, line in enumerate(lines):
        if look_up in line:
            line_num = num
    return line_num, lines


def _read_text_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8", errors="ignore").splitlines()


def _extract_incar_int(lines: Iterable[str], key: str, default: int) -> int:
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=\s*([-+]?\d+(?:\.\d+)?)", re.IGNORECASE)
    for raw_line in lines:
        line = raw_line.split("#", 1)[0].split("!", 1)[0].strip()
        match = pattern.search(line)
        if match:
            try:
                return int(float(match.group(1)))
            except ValueError:
                return default
    return default


def cycles_in(path: str = ".") -> tuple[int, int]:
    """Return NELM and NSW values from INCAR."""
    file_in = Path(path) / "INCAR"
    lines = _read_text_lines(file_in)
    nelm_in = _extract_incar_int(lines, "NELM", 60)
    nsw_in = _extract_incar_int(lines, "NSW", 0)
    return nelm_in, nsw_in


def cycles_osz(path: str = ".") -> tuple[int, int]:
    """Return the last electronic and ionic step counts from OSZICAR."""
    file_in = Path(path) / "OSZICAR"
    nelm_osz = 0
    nsw_osz = 0
    if not file_in.exists():
        return nelm_osz, nsw_osz

    lines = _read_text_lines(file_in)
    for num, line in enumerate(lines):
        if "F=" in line:
            try:
                nelm_osz = int(lines[num - 1].rstrip().split()[1])
                nsw_osz = int(line.rstrip().split()[0])
            except (IndexError, ValueError):
                continue
    return nelm_osz, nsw_osz


def converge_and_finish(path: str = ".") -> list[str]:
    """Return ['Yes'|'No', 'Yes'|'No'] for convergence and normal finish."""
    outcar = Path(path) / "OUTCAR"
    if not outcar.exists():
        return ["No", "No"]

    summary = summarize_convergence(outcar)
    finished = "Yes" if any("Voluntary context" in line for line in _read_text_lines(outcar)) else "No"
    return ["Yes" if summary.converged else "No", finished]


def get_calc_status(path: str = ".") -> JobCalcStatus:
    """Summarize the local VASP calculation state for one working directory."""
    calc_dir = Path(path).resolve()
    nelm_in, nsw_in = cycles_in(calc_dir)
    nelm_osz, nsw_osz = cycles_osz(calc_dir)
    convergence, finish = converge_and_finish(calc_dir)

    warning = None
    if nsw_osz >= 5 and nelm_osz == nelm_in and nelm_in > 0:
        warning = "Electronic steps reached NELM; check convergence."

    return JobCalcStatus(
        calc_dir=calc_dir,
        incar_exists=(calc_dir / "INCAR").is_file(),
        oszicar_exists=(calc_dir / "OSZICAR").is_file(),
        outcar_exists=(calc_dir / "OUTCAR").is_file(),
        nelm_incar=nelm_in,
        nsw_incar=nsw_in,
        nelm_oszicar=nelm_osz,
        nsw_oszicar=nsw_osz,
        converged=(convergence == "Yes"),
        finished=(finish == "Yes"),
        warning=warning,
    )


def check_one_job(path: str = ".") -> None:
    status = get_calc_status(path)
    print(
        f"{status.calc_dir}\tNSW_INCAR:\t {status.nsw_incar} \t NSW_OSZICAR:\t {status.nsw_oszicar} \t "
        f"Converge:\t {'Yes' if status.converged else 'No'} \t Finish:\t {'Yes' if status.finished else 'No'}"
    )
    if status.warning:
        print(f"Warning: {status.warning}")


def list_slurm_jobs(user_id: str | None = None) -> list[SlurmJob]:
    """Return current Slurm jobs for a user using a parseable squeue format."""
    user = user_id or getpass.getuser()
    output = _run_command(["squeue", "-h", "-u", user, "-o", "%A|%T|%j|%Z"])
    jobs: list[SlurmJob] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 3)
        while len(parts) < 4:
            parts.append("")
        job_id, state, name, work_dir = parts
        jobs.append(SlurmJob(job_id=job_id.strip(), state=state.strip(), name=name.strip(), work_dir=work_dir.strip() or None))
    return jobs


def get_slurm_job(job_id: str) -> SlurmJob:
    """Read one Slurm job record from scontrol."""
    output = _run_command(["scontrol", "show", "job", str(job_id)])
    flat = output.replace("\n", " ")

    def extract(field: str) -> str | None:
        match = re.search(rf"\b{field}=([^\s]+)", flat)
        return match.group(1) if match else None

    return SlurmJob(
        job_id=str(job_id),
        state=extract("JobState"),
        name=extract("JobName"),
        work_dir=extract("WorkDir"),
        raw=output,
    )


def get_slurm_job_state(job_id: str | int) -> str | None:
    """Return the Slurm state string for one job ID."""
    return get_slurm_job(str(job_id)).state


def get_slurm_jobs_by_state(user_id: str | None = None) -> dict[str, list[SlurmJob]]:
    """Group current Slurm jobs by their queue state."""
    grouped: dict[str, list[SlurmJob]] = {}
    for job in list_slurm_jobs(user_id):
        key = job.state or "UNKNOWN"
        grouped.setdefault(key, []).append(job)
    return grouped


def get_id_slurm(user_id: str) -> list[str]:
    """Compatibility wrapper returning only job IDs."""
    return [job.job_id for job in list_slurm_jobs(user_id)]


def get_dir_slurm(job_id: str) -> str | None:
    """Compatibility wrapper returning the job working directory."""
    return get_slurm_job(str(job_id)).work_dir


def get_id_qstat(user_id: str) -> list[str]:
    """Legacy compatibility stub; returns an empty list when qstat is unavailable."""
    if shutil.which("qstat") is None:
        return []
    output = _run_command(["qstat", "-u", user_id])
    list_out = output.splitlines()[2:]
    return [line.split()[0] for line in list_out if line.split()]


def get_dir_qstat(job_id: str) -> str | None:
    """Legacy compatibility stub for non-Slurm systems."""
    if shutil.which("qstat") is None:
        return None
    output = _run_command(["qstat", "-j", str(job_id)])
    for line in output.splitlines():
        if "workdir" in line.lower():
            return line.split(":", 1)[1].strip()
    return None


def load_job_record(report: str | Path = DEFAULT_REPORT) -> dict[str, str]:
    record_path = Path(report)
    if not record_path.exists():
        return {}
    result: dict[str, str] = {}
    with record_path.open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if ":" not in line:
                continue
            job_id, job_path = line.rstrip().split(":", 1)
            result[job_id.strip()] = job_path.strip()
    return result


def write_job_record(records: dict[str, str], report: str | Path = DEFAULT_REPORT) -> None:
    record_path = Path(report)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    with record_path.open("w", encoding="utf-8") as handle:
        for job_id, job_path in sorted(records.items(), key=lambda item: int(item[0])):
            handle.write(f"{job_id}:{job_path}\n")


def update_record(user_id: str | None = None, report: str | Path = DEFAULT_REPORT) -> dict[str, str]:
    """Refresh the local cache of Slurm job IDs to working directories."""
    records = load_job_record(report)
    for job in list_slurm_jobs(user_id):
        if job.job_id not in records and job.work_dir:
            records[job.job_id] = job.work_dir
    write_job_record(records, report)
    return records


def get_path(job_id: str | int, report: str | Path = DEFAULT_REPORT) -> str | None:
    """Return the cached job path, allowing partial numeric job IDs."""
    records = update_record(report=report)
    job_id_str = str(job_id)
    matches = [key for key in records if key.startswith(job_id_str)]
    if not matches:
        return None
    best_match = max(matches, key=len)
    return records.get(best_match)


def get_job_status(job_id: str | int, report: str | Path = DEFAULT_REPORT) -> dict[str, str | bool | None]:
    """Return queue and calculation status for one Slurm job ID."""
    job_id_str = str(job_id)
    work_dir = get_path(job_id_str, report=report)
    queue_job = None
    try:
        queue_job = get_slurm_job(job_id_str)
    except RuntimeError:
        queue_job = None

    result: dict[str, str | bool | None] = {
        "job_id": job_id_str,
        "state": queue_job.state if queue_job else None,
        "name": queue_job.name if queue_job else None,
        "work_dir": work_dir or (queue_job.work_dir if queue_job else None),
        "converged": None,
        "finished": None,
        "warning": None,
    }

    calc_path = result["work_dir"]
    if isinstance(calc_path, str) and calc_path:
        calc_status = get_calc_status(calc_path)
        result["converged"] = calc_status.converged
        result["finished"] = calc_status.finished
        result["warning"] = calc_status.warning

    return result
