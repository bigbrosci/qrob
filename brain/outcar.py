#!/usr/bin/env python3
"""Helpers for reading common information from VASP OUTCAR files."""

from pathlib import Path
import re
from typing import Dict, Iterable, List, Optional, Tuple, Union

import numpy as np

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


def get_vasp_version(path: Union[str, Path] = "OUTCAR") -> str:
    lines = read_lines(path)
    return lines[0].strip().split()[0]


def get_incar(path: Union[str, Path] = "OUTCAR") -> Dict[str, str]:
    lines = read_lines(path)
    dict_line = _get_dict_line(lines)
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


def get_volume_vectors(path: Union[str, Path] = "OUTCAR") -> Tuple[np.ndarray, List[float], float]:
    lines = read_lines(path)
    dict_line = _get_dict_line(lines)
    volume_lines = dict_line[LOOK_VECTORS][-1]
    volume = float(lines[volume_lines + 3].strip().split(":")[1].strip())
    va = [float(i) for i in lines[volume_lines + 5].split()[0:3]]
    vb = [float(i) for i in lines[volume_lines + 6].split()[0:3]]
    vc = [float(i) for i in lines[volume_lines + 7].split()[0:3]]
    length_abc = [float(i) for i in lines[volume_lines + 10].split()[0:3]]
    vector = np.transpose(np.array([va, vb, vc]))
    return vector, length_abc, volume


def get_kpoints(path: Union[str, Path] = "OUTCAR") -> str:
    lines = read_lines(path)
    dict_line = _get_dict_line(lines)
    line_kpoints = dict_line[LOOK_KPOINTS][0]
    return lines[line_kpoints].split()[1]


def get_position(path: Union[str, Path] = "OUTCAR") -> List[List[str]]:
    lines = read_lines(path)
    dict_line = _get_dict_line(lines)
    line_position_start = dict_line[LOOK_POSITION][-1]
    separate_num = dict_line[LOOK_SEPARATE]
    line_position_end = None
    for num, line_num in enumerate(separate_num):
        if line_num == line_position_start + 1 and num + 1 < len(separate_num):
            line_position_end = separate_num[num + 1]
            break
    if line_position_end is None:
        return []
    position_lines = lines[line_position_start + 2 : line_position_end]
    return [line.split()[0:3] for line in position_lines]


def get_iteration_info(path: Union[str, Path] = "OUTCAR") -> List[Tuple[int, int, float]]:
    lines = read_lines(path)
    dict_line = _get_dict_line(lines)
    lines_iteration = dict_line[LOOK_ITERATION]
    lines_time_ele_raw = dict_line[LOOK_TIME_ELE]
    lines_time_ion = set(dict_line[LOOK_TIME_ION])
    lines_time_ele = [i for i in lines_time_ele_raw if i not in lines_time_ion]
    output = []
    for num, line_num in enumerate(lines_iteration):
        line_ele = lines[line_num].split()
        ionic_step = int(line_ele[2].replace("(", ""))
        ele_step = int(line_ele[3].replace(")", ""))
        ele_time = float(lines[lines_time_ele[num]].split()[-1])
        output.append((ionic_step, ele_step, ele_time))
    return output


def get_fermi(path: Union[str, Path] = "OUTCAR") -> str:
    lines = read_lines(path)
    dict_line = _get_dict_line(lines)
    line_fermi = dict_line[LOOK_FERMI][-1]
    return lines[line_fermi].split()[2]


def get_vacuum(path: Union[str, Path] = "OUTCAR") -> Tuple[str, str]:
    lines = read_lines(path)
    dict_line = _get_dict_line(lines)
    line_vacuum = dict_line[LOOK_VACUUM][-1]
    vacuum_up, vacuum_dn = lines[line_vacuum].split()[-2:]
    return vacuum_up, vacuum_dn


def get_freq(path: Union[str, Path] = "OUTCAR") -> Tuple[List[float], List[float]]:
    lines = read_lines(path)
    dict_line = _get_dict_line(lines)
    nu = []
    zpe = []
    for i in dict_line[LOOK_FREQ]:
        line_ele = lines[i].split()
        nu.append(float(line_ele[7]))
        zpe.append(float(line_ele[9]))
    return nu, zpe


def get_freq_i(path: Union[str, Path] = "OUTCAR") -> Tuple[List[float], List[float]]:
    lines = read_lines(path)
    dict_line = _get_dict_line(lines)
    nu = []
    zpe = []
    for i in dict_line[LOOK_FREQ_I]:
        line_ele = lines[i].split()
        nu.append(float(line_ele[6]))
        zpe.append(float(line_ele[8]))
    return nu, zpe


def converge_or_not(path: Union[str, Path] = "OUTCAR") -> bool:
    lines = read_lines(path)
    return sum(1 for line in lines if LOOK_CONVERGE in line) >= 1


def get_mag(path: Union[str, Path] = "OUTCAR") -> Dict[int, List[float]]:
    lines = read_lines(path)
    dict_line = _get_dict_line(lines)
    line_mag_start = dict_line[LOOK_MAGNETIZATION][-1] + 4
    line_mag_end = 1
    for num, line in enumerate(lines[line_mag_start:]):
        if "tot  " in line:
            line_mag_end = num - 1
            break
    lines_mag = lines[line_mag_start : line_mag_start + line_mag_end]
    dict_mag = {}
    for line in lines_mag:
        line_ele = line.split()
        dict_mag[int(line_ele[0])] = [float(i) for i in line_ele[1:]]
    return dict_mag


def get_vdw(path: Union[str, Path] = "OUTCAR") -> str:
    lines = read_lines(path)
    dict_line = _get_dict_line(lines)
    line_vdw = dict_line[LOOK_VDW][-1]
    return lines[line_vdw - 1].rstrip()


def get_energy(path: Union[str, Path] = "OUTCAR") -> float:
    lines = read_lines(path)
    dict_line = _get_dict_line(lines)
    line_energy = dict_line[LOOK_ENERGY][-1]
    return float(lines[line_energy].rstrip().split()[-1])


def get_last_iteration(path: Union[str, Path] = "OUTCAR") -> Tuple[int, int]:
    lines = read_lines(path)
    ionic_step = 0
    electronic_step = 0
    pattern = re.compile(r"Iteration\s+(\d+)\(\s*(\d+)\)")
    for line in lines:
        match = pattern.search(line.replace("-", ""))
        if match:
            ionic_step = int(match.group(1))
            electronic_step = int(match.group(2))
    return ionic_step, electronic_step


def has_electronic_convergence_marker(path: Union[str, Path] = "OUTCAR") -> bool:
    return any(LOOK_ELEC_CONVERGE in line for line in read_lines(path))


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
    ionic_step, electronic_step = get_last_iteration(outcar_path)
    is_static = nsw <= 1
    mode = "single-point" if is_static else "relaxation"
    has_elec = has_electronic_convergence_marker(outcar_path)
    has_ionic = converge_or_not(outcar_path)

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
    )
