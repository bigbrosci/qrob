#!/usr/bin/env python3
"""Helpers for reading common information from VASP OUTCAR files."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Dict, List, Optional, Union

from collections import deque
from itertools import islice
try:
    from dataclasses import dataclass
except ImportError:  # pragma: no cover
    def dataclass(cls=None, **kwargs):
        def wrap(cls):
            return cls
        if cls is None:
            return wrap
        return wrap(cls)


LOOK_POT = "POTCAR"
LOOK_INCAR_START = "Startparameter"
LOOK_SEPARATE = "------------------------------" * 2
LOOK_VECTORS = "VOLUME and BASIS-vectors are now"
LOOK_KPOINTS = "irreducible k-points"
LOOK_POSITION = "POSITION      "
LOOK_ITERATION = "Iteration"
LOOK_ENERGY = "energy(sigma->0) ="
LOOK_TIME_ELE = "LOOP"
LOOK_TIME_ION = "LOOP+"
LOOK_FERMI = "E-fermi"
LOOK_VACUUM = "vacuum level"
LOOK_FREQ = "f  ="
LOOK_FREQ_I = "f/i="
LOOK_CONVERGE = "reached required accuracy"
LOOK_ELEC_CONVERGE = "aborting loop because EDIFF is reached"
LOOK_MAGNETIZATION = "magnetization (x)"
LOOK_VDW = "IVDW"


@dataclass
class ConvergenceSummary:
    calc_dir: Path
    outcar_path: Path
    outcar_exists: bool
    nsw: int
    nelm: int
    ionic_step: int
    electronic_step: int
    mode: str
    converged: bool
    reason: str
    action: Optional[str]
    finished: bool = False


def _ensure_path(path: Union[str, Path] = "OUTCAR") -> Path:
    return Path(path).resolve()


def read_lines(path: Union[str, Path] = "OUTCAR") -> List[str]:
    outcar = _ensure_path(path)
    if not outcar.is_file():
        raise FileNotFoundError(f"No OUTCAR file found at {outcar}")
    return outcar.read_text(encoding="utf-8", errors="ignore").splitlines()


def _get_dict_line(lines: List[str]) -> Dict[str, List[int]]:
    lookups = [
        LOOK_POT,
        LOOK_INCAR_START,
        LOOK_SEPARATE,
        LOOK_VECTORS,
        LOOK_KPOINTS,
        LOOK_POSITION,
        LOOK_ITERATION,
        LOOK_ENERGY,
        LOOK_TIME_ELE,
        LOOK_TIME_ION,
        LOOK_FERMI,
        LOOK_VACUUM,
        LOOK_FREQ,
        LOOK_FREQ_I,
        LOOK_CONVERGE,
        LOOK_MAGNETIZATION,
        LOOK_VDW,
    ]
    result = {lookup: [] for lookup in lookups}
    for num, line in enumerate(lines):
        for lookup in lookups:
            if lookup in line:
                result[lookup].append(num)
    return result


def iter_lines(path="OUTCAR"):
    """Stream decoded lines without retaining the file in memory."""
    with Path(path).open(encoding="utf-8", errors="ignore") as handle:
        yield from handle


def _reverse_records(path, chunk_size=65536):
    """Yield (byte offset, line) backwards, including an unterminated last line."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    with Path(path).open("rb") as handle:
        handle.seek(0, 2)
        position = handle.tell()
        end = position
        pending = b""
        while position:
            size = min(position, chunk_size)
            position -= size
            handle.seek(position)
            parts = (handle.read(size) + pending).split(b"\n")
            pending = parts[0]
            offset = position + len(pending) + 1
            records = []
            for raw in parts[1:]:
                if offset < end:
                    records.append((offset, raw.rstrip(b"\r").decode("utf-8", errors="ignore")))
                offset += len(raw) + 1
            yield from reversed(records)
        if end:
            yield 0, pending.rstrip(b"\r").decode("utf-8", errors="ignore")


def reverse_lines(path="OUTCAR", chunk_size=65536):
    """Read from EOF in bounded chunks; stop as soon as the requested value is found."""
    for _, line in _reverse_records(path, chunk_size):
        yield line


def last_matching_line(path, marker):
    for line in reverse_lines(path):
        if marker in line:
            return line
    raise ValueError(f"{marker!r} not found in {path}")


def last_block(path, marker):
    """Stream forwards from the final marker, avoiding earlier ionic steps."""
    offset = next((offset for offset, line in _reverse_records(path) if marker in line), None)
    if offset is None:
        raise ValueError(f"{marker!r} not found in {path}")
    with Path(path).open("rb") as handle:
        handle.seek(offset)
        for raw in handle:
            yield raw.decode("utf-8", errors="ignore").rstrip("\r\n")


def tail_lines(path, count=100):
    return list(reversed(list(islice(reverse_lines(path), max(0, count)))))


_NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][-+]?\d+)?"
_ENERGY = re.compile(r"energy\(sigma->0\)\s*=\s*(" + _NUMBER + r")")
_TOTEN = re.compile(r"free\s+energy\s+TOTEN\s*=\s*(" + _NUMBER + r")")
_ITERATION = re.compile(r"Iteration\s+(\d+)\(\s*(\d+)\)")


def _number(value):
    return float(value.replace("D", "E").replace("d", "e"))


def get_toten(path="OUTCAR"):
    for line in reverse_lines(path):
        match = _TOTEN.search(line) if "TOTEN" in line else None
        if match:
            return _number(match.group(1))
    raise ValueError(f"No TOTEN found in {path}")


def get_frequencies(path="OUTCAR"):
    """Return (real cm-1, real meV, imaginary cm-1, imaginary meV) in file order.

    Preserve repeated/degenerate modes; deduplication is a caller policy.
    """
    real, real_mev, imag, imag_mev = [], [], [], []
    pattern = re.compile(r"(" + _NUMBER + r")\s+cm-1\s+(" + _NUMBER + r")\s+meV")
    for line in iter_lines(path):
        imaginary = LOOK_FREQ_I in line
        if not imaginary and LOOK_FREQ not in line:
            continue
        match = pattern.search(line)
        if match:
            frequencies, energies = (imag, imag_mev) if imaginary else (real, real_mev)
            frequencies.append(_number(match.group(1)))
            energies.append(_number(match.group(2)))
    return real, real_mev, imag, imag_mev


def get_imaginary_mode(path, natoms, mass_weighted=False):
    """Return displacements for the strongest imaginary mode, storing one mode only."""
    lines = last_block(path, "Eigenvectors after division by SQRT(mass)") if mass_weighted else iter_lines(path)
    strongest = 0.0
    result = None
    for line in lines:
        if "f/i" not in line:
            continue
        frequency = float(line.split()[6])
        next(lines, None)  # x/y/z/dx/dy/dz header
        mode = [row.split()[3:6] for row in islice(lines, natoms)]
        if len(mode) != natoms or any(len(row) != 3 for row in mode):
            raise ValueError(f"Incomplete imaginary mode in {path}")
        if frequency > strongest:
            strongest, result = frequency, mode
    if result is None:
        raise ValueError(f"No imaginary mode found in {path}")
    return result


def get_vasp_version(path="OUTCAR"):
    return next(iter_lines(path)).strip().split()[0]


def get_incar(path: Union[str, Path] = "OUTCAR") -> Dict[str, str]:
    prefix = deque(maxlen=30)
    lines = []
    started = False
    for line in iter_lines(path):
        if not started:
            if LOOK_INCAR_START not in line:
                prefix.append(line)
                continue
            lines = list(prefix)
            started = True
        lines.append(line)
        if LOOK_SEPARATE in line:
            break
    dict_line = {marker: [i for i, line in enumerate(lines) if marker in line]
                 for marker in (LOOK_INCAR_START, LOOK_SEPARATE)}
    incar_start_candidates = dict_line[LOOK_INCAR_START]
    if not incar_start_candidates:
        return {}
    incar_start_num = incar_start_candidates[0]
    separate_num = dict_line[LOOK_SEPARATE]
    incar_end_num = None
    for num, line_num in enumerate(separate_num):
        if 15 < incar_start_num - line_num < 30 and num + 1 < len(separate_num):
            incar_end_num = separate_num[num + 1]
            break
    if incar_end_num is None:
        return {}

    dict_incar: Dict[str, str] = {}
    for line in lines[incar_start_num:incar_end_num]:
        if "=" not in line:
            continue
        if ";" in line:
            parts = line.split(";")
        else:
            parts = [line]
        for part in parts:
            if "=" not in part:
                continue
            item_ele = [piece.strip() for piece in part.rstrip().split("=")]
            if len(item_ele) < 2:
                continue
            key = item_ele[0].split()[-1] if "LDAU" in part else item_ele[0]
            if "DFIELD" in part:
                continue
            value = item_ele[1] if any(token in part for token in ("POMASS", "ZVAL", "RWIGS", "LDAU")) else item_ele[1].split()[0].strip()
            dict_incar[key] = value
    return dict_incar


def get_volume_vectors(path="OUTCAR"):
    import numpy as np
    lines = list(islice(last_block(path, LOOK_VECTORS), 11))
    volume = float(lines[3].split(":")[1])
    vectors = [[float(value) for value in line.split()[:3]] for line in lines[5:8]]
    return np.transpose(np.array(vectors)), [float(value) for value in lines[10].split()[:3]], volume


def get_kpoints(path="OUTCAR"):
    for line in iter_lines(path):
        if LOOK_KPOINTS in line:
            return line.split()[1]
    raise ValueError(f"No k-points found in {path}")


def get_position(path="OUTCAR"):
    rows = []
    lines = last_block(path, LOOK_POSITION)
    next(lines)
    next(lines, None)
    for line in lines:
        if not line.strip() or line.lstrip().startswith("---"):
            break
        rows.append(line.split()[:3])
    return rows


def get_iteration_info(path="OUTCAR"):
    iterations = deque()
    output = []
    for line in iter_lines(path):
        if LOOK_ITERATION in line:
            match = _ITERATION.search(line)
            if match:
                iterations.append((int(match.group(1)), int(match.group(2))))
        elif LOOK_TIME_ELE in line and LOOK_TIME_ION not in line and iterations:
            ionic, electronic = iterations.popleft()
            output.append((ionic, electronic, float(line.split()[-1])))
    return output


def get_fermi(path="OUTCAR"):
    return last_matching_line(path, LOOK_FERMI).split()[2]


def get_vacuum(path="OUTCAR"):
    return tuple(last_matching_line(path, LOOK_VACUUM).split()[-2:])


def get_freq(path="OUTCAR"):
    real, energies, _, _ = get_frequencies(path)
    return real, energies


def get_freq_i(path="OUTCAR"):
    _, _, imag, energies = get_frequencies(path)
    return imag, energies


def converge_or_not(path="OUTCAR"):
    return any(LOOK_CONVERGE in line for line in reverse_lines(path))


def get_mag(path="OUTCAR"):
    """Read all orbital columns, including tot, from the final x-magnetization table."""
    result = {}
    for line in last_block(path, LOOK_MAGNETIZATION):
        parts = line.split()
        if parts and parts[0].isdigit():
            result[int(parts[0])] = [float(value) for value in parts[1:]]
        elif result:
            break
    return result


def get_vdw(path="OUTCAR"):
    lines = reverse_lines(path)
    for line in lines:
        if LOOK_VDW in line:
            return next(lines).rstrip()
    raise ValueError(f"No IVDW found in {path}")


def get_energy(path="OUTCAR", fallback_toten=False):
    """Return final sigma->0 energy (eV), optionally falling back to final TOTEN."""
    toten = None
    for line in reverse_lines(path):
        match = _ENERGY.search(line) if "energy(sigma->0)" in line else None
        if match:
            return _number(match.group(1))
        if fallback_toten and toten is None and "TOTEN" in line:
            match = _TOTEN.search(line)
            if match:
                toten = _number(match.group(1))
    if toten is not None:
        return toten
    raise ValueError(f"No DFT energy found in {path}")


def get_last_iteration(path="OUTCAR"):
    for line in reverse_lines(path):
        match = _ITERATION.search(line) if LOOK_ITERATION in line else None
        if match:
            return int(match.group(1)), int(match.group(2))
    return 0, 0


def has_electronic_convergence_marker(path="OUTCAR"):
    return any(LOOK_ELEC_CONVERGE in line for line in reverse_lines(path))


def summarize_convergence(path: Union[str, Path]) -> ConvergenceSummary:
    resolved = _ensure_path(path)
    outcar_path = resolved / "OUTCAR" if resolved.is_dir() else resolved
    calc_dir = outcar_path.parent.resolve()

    if not outcar_path.is_file():
        return ConvergenceSummary(
            calc_dir=calc_dir,
            outcar_path=outcar_path,
            outcar_exists=False,
            nsw=0,
            nelm=0,
            ionic_step=0,
            electronic_step=0,
            mode="unknown",
            converged=False,
            reason="OUTCAR not found.",
            action="scratch",
        )

    incar = get_incar(outcar_path)
    nsw = int(float(incar.get("NSW", "0"))) if incar.get("NSW") is not None else 0
    nelm = int(float(incar.get("NELM", "0"))) if incar.get("NELM") is not None else 0
    ionic_step = electronic_step = 0
    has_elec = has_ionic = finished = False
    for line in iter_lines(outcar_path):
        if LOOK_ITERATION in line:
            match = _ITERATION.search(line)
            if match:
                ionic_step, electronic_step = map(int, match.groups())
        has_elec = has_elec or LOOK_ELEC_CONVERGE in line
        has_ionic = has_ionic or LOOK_CONVERGE in line
        finished = finished or "Voluntary context" in line
    is_static = nsw <= 1
    mode = "single-point" if is_static else "relaxation"

    if is_static:
        converged = has_elec and nelm > electronic_step
        reason = "Job converged." if converged else "Single-point calculation did not converge or was terminated."
    else:
        converged = has_ionic and nelm > electronic_step
        reason = "Job converged." if converged else "Relaxation did not converge or was terminated."

    action = None if converged else ("rerun" if ionic_step > 1 else "scratch")

    return ConvergenceSummary(
        calc_dir=calc_dir,
        outcar_path=outcar_path,
        outcar_exists=True,
        nsw=nsw,
        nelm=nelm,
        ionic_step=ionic_step,
        electronic_step=electronic_step,
        mode=mode,
        converged=converged,
        reason=reason,
        action=action,
        finished=finished,
    )
