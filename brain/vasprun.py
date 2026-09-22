#!/usr/bin/env python3
# References:
# - https://github.com/abelcarreras/vasp_parser/blob/master/vasp_parser.py
"""Structured helpers for reading data from VASP ``vasprun.xml`` files."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import xml.etree.ElementTree as ET

try:
    from lxml import etree as LXML_ET
except ImportError:  # pragma: no cover - only needed for incomplete XML files
    LXML_ET = None


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
    try:
        return ET.parse(vasprun).getroot()
    except ET.ParseError:
        # Interrupted VASP jobs commonly leave a truncated ``vasprun.xml``.
        # The legacy XML-to-ML_AB converter accepted these files with lxml's
        # recovery mode, so retain that useful behavior here.
        if LXML_ET is None:
            raise
        parser = LXML_ET.XMLParser(recover=True)
        return LXML_ET.parse(str(vasprun), parser).getroot()


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
    for node in _iter_top_level(path):
        if node.tag != "atominfo":
            continue
        symbols = []
        for atom in node.findall("./array[@name='atoms']/set/rc"):
            symbol = atom.find("./c")
            if symbol is not None and symbol.text:
                symbols.append(symbol.text.strip())
        return symbols
    return []


def _calculation_step(calculation) -> VasprunStep | None:
    energy = None
    # ML_AB uses the free energy / TOTEN value, preserving the historical order.
    for name in ("e_fr_energy", "e_wo_entrp", "e_0_energy"):
        energy_node = calculation.find(f"./energy/i[@name='{name}']")
        if energy_node is not None and energy_node.text:
            energy = float(energy_node.text)
            break
    structure = calculation.find("./structure")
    lattice = _parse_varray(None if structure is None else structure.find("./crystal/varray[@name='basis']"))
    positions = _parse_varray(None if structure is None else structure.find("./varray[@name='positions']"))
    forces = _parse_varray(calculation.find("./varray[@name='forces']"))
    stress = _parse_stress_components(_parse_varray(calculation.find("./varray[@name='stress']")))
    if lattice and positions:
        return VasprunStep(lattice, positions, forces, stress, energy)
    return None


def _iter_top_level(path: str | Path = "vasprun.xml"):
    """Yield top-level elements, releasing each before reading the next.

    As with the full-tree reader, lxml recovery accepts interrupted output when
    lxml is available. No persistent cache is used for a growing trajectory.
    """
    vasprun = _resolve_vasprun_path(path)
    with vasprun.open("rb") as handle:
        if LXML_ET is not None:
            context = LXML_ET.iterparse(handle, events=("start", "end"), recover=True)
        else:
            context = ET.iterparse(handle, events=("start", "end"))
        root = None
        depth = 0
        for event, node in context:
            if event == "start":
                depth += 1
                if root is None:
                    root = node
                continue
            if depth == 2:
                yield node
                root.remove(node)
                node.clear()
            depth -= 1


def iter_calculation_steps(path: str | Path = "vasprun.xml"):
    """Yield ionic steps without retaining the full XML tree."""
    for node in _iter_top_level(path):
        if node.tag == "calculation":
            step = _calculation_step(node)
            if step is not None:
                yield step


def parse_calculation_steps(path: str | Path = "vasprun.xml") -> list[VasprunStep]:
    """Return all ionic steps without retaining the XML tree as a second copy."""
    return list(iter_calculation_steps(path))


def get_final_step(path: str | Path = "vasprun.xml") -> VasprunStep | None:
    final = None
    for step in iter_calculation_steps(path):
        final = step
    return final


def get_final_energy(path: str | Path = "vasprun.xml") -> float | None:
    step = get_final_step(path)
    return step.energy if step is not None else None


def get_final_forces(path: str | Path = "vasprun.xml") -> list[list[float]]:
    step = get_final_step(path)
    return step.forces if step is not None else []


def get_final_stress(path: str | Path = "vasprun.xml") -> list[float]:
    step = get_final_step(path)
    return step.stress if step is not None else []
