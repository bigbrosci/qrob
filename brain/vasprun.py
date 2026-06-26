#!/usr/bin/env python3
# References:
# - https://github.com/abelcarreras/vasp_parser/blob/master/vasp_parser.py
"""Structured helpers for reading data from VASP ``vasprun.xml`` files."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass
class VasprunStep:
    lattice: list[list[float]]
    positions: list[list[float]]
    forces: list[list[float]]
    stress: list[float]
    energy: float | None


def _resolve_vasprun_path(path: str | Path = "vasprun.xml") -> Path:
    vasprun = Path(path).resolve()
    if not vasprun.is_file():
        raise FileNotFoundError(f"No vasprun.xml file found at {vasprun}")
    return vasprun


@lru_cache(maxsize=32)
def _get_root(path: str | Path = "vasprun.xml") -> ET.Element:
    vasprun = _resolve_vasprun_path(path)
    return ET.parse(vasprun).getroot()


def _parse_varray(node: ET.Element | None) -> list[list[float]]:
    if node is None:
        return []
    values: list[list[float]] = []
    for row in node.findall("./v"):
        if row.text:
            values.append([float(value) for value in row.text.split()])
    return values


def _find_last_named_value(root: ET.Element, tag: str, name: str) -> str | None:
    value = None
    for node in root.findall(f".//{tag}[@name='{name}']"):
        if node.text and node.text.strip():
            value = node.text.strip()
    return value


def _parse_stress_components(matrix: list[list[float]]) -> list[float]:
    if len(matrix) != 3 or any(len(row) != 3 for row in matrix):
        return []
    return [
        matrix[0][0],
        matrix[1][1],
        matrix[2][2],
        matrix[0][1],
        matrix[1][2],
        matrix[2][0],
    ]


def get_version(path: str | Path = "vasprun.xml") -> str | None:
    root = _get_root(path)
    return _find_last_named_value(root, "i", "version")


def get_nedos(path: str | Path = "vasprun.xml") -> int | None:
    root = _get_root(path)
    value = _find_last_named_value(root, "i", "NEDOS")
    return int(float(value)) if value is not None else None


def get_fermi(path: str | Path = "vasprun.xml") -> float | None:
    root = _get_root(path)
    value = _find_last_named_value(root, "i", "efermi")
    return float(value) if value is not None else None


def get_kpoints(path: str | Path = "vasprun.xml") -> list[list[float]]:
    root = _get_root(path)
    kpoint_nodes = root.findall(".//kpoints/varray[@name='kpointlist']")
    if not kpoint_nodes:
        return []
    return _parse_varray(kpoint_nodes[-1])


def get_epsilon(path: str | Path = "vasprun.xml") -> list[list[float]]:
    root = _get_root(path)
    epsilon_node = root.find(".//varray[@name='epsilon']")
    return _parse_varray(epsilon_node)


def get_born_charges(path: str | Path = "vasprun.xml") -> list[list[list[float]]]:
    root = _get_root(path)
    born_node = root.find(".//array[@name='born_charges']")
    if born_node is None:
        return []

    born_charges: list[list[list[float]]] = []
    top_set = born_node.find("./set")
    if top_set is None:
        return born_charges

    for atom_set in top_set.findall("./set"):
        atom_tensor: list[list[float]] = []
        for row in atom_set.findall("./v"):
            if row.text:
                atom_tensor.append([float(value) for value in row.text.split()])
        if atom_tensor:
            born_charges.append(atom_tensor)
    return born_charges


def get_atom_symbols(path: str | Path = "vasprun.xml") -> list[str]:
    root = _get_root(path)
    atom_nodes = root.findall(".//atominfo/array[@name='atoms']/set/rc")
    symbols: list[str] = []
    for atom in atom_nodes:
        symbol_node = atom.find("./c")
        if symbol_node is not None and symbol_node.text:
            symbols.append(symbol_node.text.strip())
    return symbols


def parse_calculation_steps(path: str | Path = "vasprun.xml") -> list[VasprunStep]:
    root = _get_root(path)
    steps: list[VasprunStep] = []

    for calculation in root.findall(".//calculation"):
        energy = None
        for name in ("e_wo_entrp", "e_fr_energy", "e_0_energy"):
            energy_node = calculation.find(f"./energy/i[@name='{name}']")
            if energy_node is not None and energy_node.text:
                energy = float(energy_node.text)
                break

        structure = calculation.find("./structure")
        lattice = _parse_varray(None if structure is None else structure.find("./crystal/varray[@name='basis']"))
        positions = _parse_varray(None if structure is None else structure.find("./varray[@name='positions']"))
        forces = _parse_varray(calculation.find("./varray[@name='forces']"))
        stress_matrix = _parse_varray(calculation.find("./varray[@name='stress']"))
        stress = _parse_stress_components(stress_matrix)

        if lattice and positions:
            steps.append(
                VasprunStep(
                    lattice=lattice,
                    positions=positions,
                    forces=forces,
                    stress=stress,
                    energy=energy,
                )
            )

    return steps


def get_final_step(path: str | Path = "vasprun.xml") -> VasprunStep | None:
    steps = parse_calculation_steps(path)
    return steps[-1] if steps else None


def get_final_energy(path: str | Path = "vasprun.xml") -> float | None:
    step = get_final_step(path)
    return step.energy if step is not None else None


def get_final_forces(path: str | Path = "vasprun.xml") -> list[list[float]]:
    step = get_final_step(path)
    return step.forces if step is not None else []


def get_final_stress(path: str | Path = "vasprun.xml") -> list[float]:
    step = get_final_step(path)
    return step.stress if step is not None else []
