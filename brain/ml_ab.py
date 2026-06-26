#!/usr/bin/env python3
# References:
# - https://github.com/abelcarreras/vasp_parser/blob/master/vasp_parser.py
# - https://github.com/utf/pymlff
# - https://vasp.at/wiki/ML_AB
"""Helpers for converting VASP XML outputs into ML_AB-style datasets."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import copy
import itertools
import warnings

from ase.data import atomic_masses, atomic_numbers

try:
    from .vasprun import get_atom_symbols, parse_calculation_steps
except ImportError:
    from vasprun import get_atom_symbols, parse_calculation_steps


BLOCK_SEP_0 = "**************************************************\n"
BLOCK_SEP_1 = "--------------------------------------------------\n"
BLOCK_SEP_2 = "==================================================\n"


@dataclass
class MLABConfiguration:
    system_name: str
    atom_symbols: list[str]
    atom_counts: list[int]
    cell_vectors: list[list[float]]
    atom_positions: list[list[float]]
    total_energy: float
    atom_forces: list[list[float]]
    stress_kbar: list[float]
    ctifor: float | None = None

    @property
    def num_atom_types(self) -> int:
        return len(self.atom_symbols)

    @property
    def num_atoms(self) -> int:
        return sum(self.atom_counts)

    @property
    def atom_types_numbers(self) -> OrderedDict[str, int]:
        return OrderedDict(zip(self.atom_symbols, self.atom_counts))


@dataclass
class MLABDataset:
    configurations: list[MLABConfiguration]
    basis_set: dict[str, list[tuple[int, int]]]
    atomic_mass: dict[str, float]
    reference_energy: dict[str, float]
    version: str = "1.0 Version"

    @property
    def atom_types(self) -> list[str]:
        return list(sorted({symbol for config in self.configurations for symbol in config.atom_symbols}))

    @property
    def num_configurations(self) -> int:
        return len(self.configurations)

    @property
    def max_num_atom_types(self) -> int:
        return max(config.num_atom_types for config in self.configurations)

    @property
    def max_num_atoms(self) -> int:
        return max(config.num_atoms for config in self.configurations)

    @property
    def max_num_atoms_per_type(self) -> int:
        return max(max(config.atom_counts) for config in self.configurations)

    @property
    def num_basis_set_per_type(self) -> list[int]:
        return [len(self.basis_set[symbol]) for symbol in self.atom_types]

    def to_string(self) -> str:
        _validate_ctifor_consistency(self.configurations)

        text = f"{self.version}\n"
        text += BLOCK_SEP_0
        text += "The number of configurations\n"
        text += BLOCK_SEP_1
        text += f"{self.num_configurations}\n"

        text += BLOCK_SEP_0
        text += "The maximum number of atom type\n"
        text += BLOCK_SEP_1
        text += f"{self.max_num_atom_types}\n"

        text += BLOCK_SEP_0
        text += "The atom types in the data file\n"
        text += BLOCK_SEP_1
        text += _three_per_line(self.atom_types, prefix=" ")

        text += BLOCK_SEP_0
        text += "The maximum number of atoms per system\n"
        text += BLOCK_SEP_1
        text += f"{self.max_num_atoms}\n"

        text += BLOCK_SEP_0
        text += "The maximum number of atoms per atom type\n"
        text += BLOCK_SEP_1
        text += f"{self.max_num_atoms_per_type}\n"

        text += BLOCK_SEP_0
        text += "Reference atomic energy (eV)\n"
        text += BLOCK_SEP_1
        text += _three_per_line([f"{self.reference_energy[symbol]:.14f}" for symbol in self.atom_types], prefix=" ")

        text += BLOCK_SEP_0
        text += "Atomic mass\n"
        text += BLOCK_SEP_1
        text += _three_per_line([f"{self.atomic_mass[symbol]:.14f}" for symbol in self.atom_types], prefix=" ")

        text += BLOCK_SEP_0
        text += "The numbers of basis sets per atom type\n"
        text += BLOCK_SEP_1
        text += _three_per_line([str(len(self.basis_set[symbol])) for symbol in self.atom_types], prefix=" ")

        for symbol in self.atom_types:
            text += BLOCK_SEP_0
            text += f"Basis set for {symbol}\n"
            text += BLOCK_SEP_1
            text += "\n".join(f" {config_idx} {atom_idx}" for config_idx, atom_idx in self.basis_set[symbol]) + "\n"

        for idx, config in enumerate(self.configurations, start=1):
            text += configuration_to_string(idx, config)
        return text

    def write_file(self, output_path: str | Path) -> Path:
        output = Path(output_path)
        output.write_text(self.to_string(), encoding="utf-8")
        return output

    @classmethod
    def read_file(cls, input_path: str | Path) -> "MLABDataset":
        parser = _MLABParser(Path(input_path))
        return parser.parse()

    def __add__(self, other: "MLABDataset") -> "MLABDataset":
        if self.version != other.version:
            warnings.warn("ML_AB versions do not match; keeping the left-hand version.")

        for symbol, mass in other.atomic_mass.items():
            if symbol in self.atomic_mass and abs(self.atomic_mass[symbol] - mass) > 1.0e-4:
                raise ValueError(f"Atomic masses do not match for {symbol}")
        for symbol, energy in other.reference_energy.items():
            if symbol in self.reference_energy and abs(self.reference_energy[symbol] - energy) > 1.0e-8:
                raise ValueError(f"Reference energies do not match for {symbol}")

        combined_configs = copy.deepcopy(self.configurations) + copy.deepcopy(other.configurations)
        new_basis = copy.deepcopy(self.basis_set)
        offset = len(self.configurations)
        for symbol, basis_entries in other.basis_set.items():
            new_basis.setdefault(symbol, [])
            for config_idx, atom_idx in basis_entries:
                new_basis[symbol].append((config_idx + offset, atom_idx))

        new_atomic_mass = {**self.atomic_mass, **other.atomic_mass}
        new_reference_energy = {**self.reference_energy, **other.reference_energy}
        return MLABDataset(
            configurations=combined_configs,
            basis_set=new_basis,
            atomic_mass=new_atomic_mass,
            reference_energy=new_reference_energy,
            version=self.version,
        )


def _grouper(iterable: Iterable[str], size: int) -> Iterable[list[str]]:
    iterator = iter(iterable)
    return iter(lambda: list(itertools.islice(iterator, size)), [])


def _three_per_line(values: list[str], prefix: str = "") -> str:
    return "\n".join(prefix + " ".join(group) for group in _grouper(values, 3)) + "\n"


def _validate_ctifor_consistency(configurations: list[MLABConfiguration]) -> None:
    presence = {config.ctifor is not None for config in configurations}
    if len(presence) > 1:
        raise ValueError("CTIFOR must be present for all configurations or omitted for all.")


def _ordered_symbols_and_counts(symbols: list[str]) -> tuple[list[str], list[int]]:
    ordered_symbols: list[str] = []
    counts: list[int] = []
    for symbol in symbols:
        if ordered_symbols and ordered_symbols[-1] == symbol:
            counts[-1] += 1
        elif symbol in ordered_symbols:
            idx = ordered_symbols.index(symbol)
            counts[idx] += 1
        else:
            ordered_symbols.append(symbol)
            counts.append(1)
    return ordered_symbols, counts


def _resolve_system_name(base_dir: Path) -> str:
    for candidate in ("CONTCAR", "POSCAR"):
        path = base_dir / candidate
        if path.is_file():
            with path.open("r", encoding="utf-8") as handle:
                first_line = handle.readline().strip()
            if first_line:
                return first_line[:40]
    return (base_dir.name or "Generated By xml2mlab")[:40]


def parse_vasprun_to_mlab_configurations(vasprun_path: str | Path, ctifor: float | None = None) -> list[MLABConfiguration]:
    vasprun = Path(vasprun_path).resolve()
    if not vasprun.is_file():
        raise FileNotFoundError(f"No vasprun.xml file found at {vasprun}")

    base_dir = vasprun.parent
    system_name = _resolve_system_name(base_dir)
    atom_symbols_all = get_atom_symbols(vasprun)
    if not atom_symbols_all:
        raise ValueError(f"Could not read atom symbols from {vasprun}")

    ordered_symbols, counts = _ordered_symbols_and_counts(atom_symbols_all)
    steps = parse_calculation_steps(vasprun)
    complete_steps = [step for step in steps if step.energy is not None and step.forces and len(step.stress) == 6]

    if not complete_steps:
        raise ValueError(f"No complete configurations could be read from {vasprun}")

    configurations: list[MLABConfiguration] = []
    for step in complete_steps:
        configurations.append(
            MLABConfiguration(
                system_name=system_name,
                atom_symbols=ordered_symbols,
                atom_counts=counts,
                cell_vectors=step.lattice,
                atom_positions=step.positions,
                total_energy=step.energy if step.energy is not None else 0.0,
                atom_forces=step.forces,
                stress_kbar=step.stress,
                ctifor=ctifor,
            )
        )
    return configurations


def build_dataset(
    configurations: list[MLABConfiguration],
    basis_set: dict[str, list[tuple[int, int]]] | None = None,
    reference_energy: dict[str, float] | None = None,
    version: str = "1.0 Version",
) -> MLABDataset:
    if not configurations:
        raise ValueError("No configurations supplied for ML_AB dataset construction.")

    atom_types = list(sorted({symbol for config in configurations for symbol in config.atom_symbols}))
    if basis_set is None:
        basis_set = {symbol: [(1, 1)] for symbol in atom_types}
    if reference_energy is None:
        reference_energy = {symbol: 0.0 for symbol in atom_types}
    atomic_mass = {symbol: float(atomic_masses[atomic_numbers[symbol]]) for symbol in atom_types}

    return MLABDataset(
        configurations=configurations,
        basis_set=basis_set,
        atomic_mass=atomic_mass,
        reference_energy=reference_energy,
        version=version,
    )


def configuration_to_string(num: int, data: MLABConfiguration) -> str:
    conv = ""
    conv += BLOCK_SEP_0
    conv += f"Configuration num. {int(num)}\n"

    conv += BLOCK_SEP_2
    conv += "System name\n"
    conv += BLOCK_SEP_1
    conv += f"{data.system_name}\n"

    conv += BLOCK_SEP_2
    conv += "The number of atom types\n"
    conv += BLOCK_SEP_1
    conv += f"{data.num_atom_types}\n"

    conv += BLOCK_SEP_2
    conv += "The number of atoms\n"
    conv += BLOCK_SEP_1
    conv += f"{data.num_atoms}\n"

    conv += BLOCK_SEP_0
    conv += "Atom types and atom numbers\n"
    conv += BLOCK_SEP_1
    for symbol, count in data.atom_types_numbers.items():
        conv += f" {symbol} {count}\n"

    if data.ctifor is not None:
        conv += BLOCK_SEP_2
        conv += "CTIFOR\n"
        conv += BLOCK_SEP_1
        conv += f"{data.ctifor:.14f}\n"

    conv += BLOCK_SEP_2
    conv += "Primitive lattice vectors (ang.)\n"
    conv += BLOCK_SEP_1
    conv += "".join("{:.16f} {:.16f} {:.16f}\n".format(*row) for row in data.cell_vectors)

    conv += BLOCK_SEP_2
    conv += "Atomic positions (ang.)\n"
    conv += BLOCK_SEP_1
    conv += "".join("{:.16f} {:.16f} {:.16f}\n".format(*row) for row in data.atom_positions)

    conv += BLOCK_SEP_2
    conv += "Total energy (eV)\n"
    conv += BLOCK_SEP_1
    conv += f"{data.total_energy:.14f}\n"

    conv += BLOCK_SEP_2
    conv += "Forces (eV ang.^-1)\n"
    conv += BLOCK_SEP_1
    conv += "".join("{:.16f} {:.16f} {:.16f}\n".format(*row) for row in data.atom_forces)

    conv += BLOCK_SEP_2
    conv += "Stress (kbar)\n"
    conv += BLOCK_SEP_1
    conv += "XX YY ZZ\n"
    conv += BLOCK_SEP_1
    conv += "{:.16f} {:.16f} {:.16f}\n".format(*data.stress_kbar[:3])
    conv += BLOCK_SEP_1
    conv += "XY YZ ZX\n"
    conv += BLOCK_SEP_1
    conv += "{:.16f} {:.16f} {:.16f}\n".format(*data.stress_kbar[3:])
    return conv


def write_ml_ab(configurations: list[MLABConfiguration], output_path: str | Path) -> Path:
    dataset = build_dataset(configurations)
    return dataset.write_file(output_path)


class _MLABParser:
    def __init__(self, path: Path):
        self.path = path
        self.lines = path.read_text(encoding="utf-8").splitlines()
        self.index = 0

    def parse(self) -> MLABDataset:
        version = self.lines[self.index].strip()
        self.index += 1

        n_configs = int(self._read_named_scalar("The number of configurations"))
        _max_num_types = int(self._read_named_scalar("The maximum number of atom type"))
        atom_types = self._read_named_list("The atom types in the data file")
        _max_atoms = int(self._read_named_scalar("The maximum number of atoms per system"))
        _max_atoms_per_type = int(self._read_named_scalar("The maximum number of atoms per atom type"))

        reference_energy_values = [float(x) for x in self._read_named_list("Reference atomic energy (eV)")]
        atomic_mass_values = [float(x) for x in self._read_named_list("Atomic mass")]
        basis_counts = [int(x) for x in self._read_named_list("The numbers of basis sets per atom type")]

        reference_energy = dict(zip(atom_types, reference_energy_values))
        atomic_mass = dict(zip(atom_types, atomic_mass_values))

        basis_set: dict[str, list[tuple[int, int]]] = {}
        for atom_type, basis_count in zip(atom_types, basis_counts):
            title = f"Basis set for {atom_type}"
            entries = self._read_named_matrix(title, basis_count)
            basis_set[atom_type] = [(int(row[0]), int(row[1])) for row in entries]

        configurations = [self._read_configuration() for _ in range(n_configs)]
        return MLABDataset(
            configurations=configurations,
            basis_set=basis_set,
            atomic_mass=atomic_mass,
            reference_energy=reference_energy,
            version=version,
        )

    def _skip_blank(self) -> None:
        while self.index < len(self.lines) and self.lines[self.index].strip() == "":
            self.index += 1

    def _expect_sep(self, sep: str) -> None:
        self._skip_blank()
        if self.index >= len(self.lines) or self.lines[self.index] != sep.strip():
            raise ValueError(f"Expected separator '{sep.strip()}' near line {self.index + 1} in {self.path}")
        self.index += 1

    def _read_named_scalar(self, title: str) -> str:
        self._expect_sep(BLOCK_SEP_0.strip())
        if self.lines[self.index].strip() != title:
            raise ValueError(f"Expected '{title}' near line {self.index + 1} in {self.path}")
        self.index += 1
        self._expect_sep(BLOCK_SEP_1.strip())
        value = self.lines[self.index].strip()
        self.index += 1
        return value

    def _read_named_list(self, title: str) -> list[str]:
        self._expect_sep(BLOCK_SEP_0.strip())
        if self.lines[self.index].strip() != title:
            raise ValueError(f"Expected '{title}' near line {self.index + 1} in {self.path}")
        self.index += 1
        self._expect_sep(BLOCK_SEP_1.strip())
        values: list[str] = []
        while self.index < len(self.lines):
            line = self.lines[self.index].strip()
            if not line:
                self.index += 1
                continue
            if line in {BLOCK_SEP_0.strip(), BLOCK_SEP_2.strip()}:
                break
            values.extend(line.split())
            self.index += 1
        return values

    def _read_named_matrix(self, title: str, n_rows: int) -> list[list[str]]:
        self._expect_sep(BLOCK_SEP_0.strip())
        if self.lines[self.index].strip() != title:
            raise ValueError(f"Expected '{title}' near line {self.index + 1} in {self.path}")
        self.index += 1
        self._expect_sep(BLOCK_SEP_1.strip())
        rows = []
        for _ in range(n_rows):
            rows.append(self.lines[self.index].split())
            self.index += 1
        return rows

    def _read_configuration(self) -> MLABConfiguration:
        self._expect_sep(BLOCK_SEP_0.strip())
        header = self.lines[self.index].strip()
        if not header.startswith("Configuration num."):
            raise ValueError(f"Expected configuration header near line {self.index + 1} in {self.path}")
        self.index += 1

        system_name = self._read_config_scalar("System name")
        n_atom_types = int(self._read_config_scalar("The number of atom types"))
        _n_atoms = int(self._read_config_scalar("The number of atoms"))
        atom_symbols, atom_counts = self._read_atom_types_numbers(n_atom_types)

        ctifor = None
        self._skip_blank()
        if self.index < len(self.lines) and self.lines[self.index].strip() == BLOCK_SEP_2.strip():
            maybe_title = self.lines[self.index + 1].strip() if self.index + 1 < len(self.lines) else ""
            if maybe_title == "CTIFOR":
                ctifor = float(self._read_config_scalar("CTIFOR"))

        cell_vectors = self._read_vector_block("Primitive lattice vectors (ang.)", 3)
        atom_positions = self._read_vector_block("Atomic positions (ang.)", sum(atom_counts))
        total_energy = float(self._read_config_scalar("Total energy (eV)"))
        atom_forces = self._read_vector_block("Forces (eV ang.^-1)", sum(atom_counts))
        stress_kbar = self._read_stress_block()

        return MLABConfiguration(
            system_name=system_name,
            atom_symbols=atom_symbols,
            atom_counts=atom_counts,
            cell_vectors=cell_vectors,
            atom_positions=atom_positions,
            total_energy=total_energy,
            atom_forces=atom_forces,
            stress_kbar=stress_kbar,
            ctifor=ctifor,
        )

    def _read_config_scalar(self, title: str) -> str:
        self._expect_sep(BLOCK_SEP_2.strip())
        if self.lines[self.index].strip() != title:
            raise ValueError(f"Expected '{title}' near line {self.index + 1} in {self.path}")
        self.index += 1
        self._expect_sep(BLOCK_SEP_1.strip())
        value = self.lines[self.index].strip()
        self.index += 1
        return value

    def _read_atom_types_numbers(self, n_types: int) -> tuple[list[str], list[int]]:
        self._expect_sep(BLOCK_SEP_0.strip())
        if self.lines[self.index].strip() != "Atom types and atom numbers":
            raise ValueError(f"Expected atom type block near line {self.index + 1} in {self.path}")
        self.index += 1
        self._expect_sep(BLOCK_SEP_1.strip())
        symbols: list[str] = []
        counts: list[int] = []
        for _ in range(n_types):
            symbol, count = self.lines[self.index].split()[:2]
            symbols.append(symbol)
            counts.append(int(count))
            self.index += 1
        return symbols, counts

    def _read_vector_block(self, title: str, n_rows: int) -> list[list[float]]:
        self._expect_sep(BLOCK_SEP_2.strip())
        if self.lines[self.index].strip() != title:
            raise ValueError(f"Expected '{title}' near line {self.index + 1} in {self.path}")
        self.index += 1
        self._expect_sep(BLOCK_SEP_1.strip())
        rows: list[list[float]] = []
        for _ in range(n_rows):
            rows.append([float(x) for x in self.lines[self.index].split()[:3]])
            self.index += 1
        return rows

    def _read_stress_block(self) -> list[float]:
        self._expect_sep(BLOCK_SEP_2.strip())
        if self.lines[self.index].strip() != "Stress (kbar)":
            raise ValueError(f"Expected stress block near line {self.index + 1} in {self.path}")
        self.index += 1
        self._expect_sep(BLOCK_SEP_1.strip())
        if self.lines[self.index].strip() != "XX YY ZZ":
            raise ValueError(f"Expected XX YY ZZ header near line {self.index + 1} in {self.path}")
        self.index += 1
        self._expect_sep(BLOCK_SEP_1.strip())
        first = [float(x) for x in self.lines[self.index].split()[:3]]
        self.index += 1
        self._expect_sep(BLOCK_SEP_1.strip())
        if self.lines[self.index].strip() != "XY YZ ZX":
            raise ValueError(f"Expected XY YZ ZX header near line {self.index + 1} in {self.path}")
        self.index += 1
        self._expect_sep(BLOCK_SEP_1.strip())
        second = [float(x) for x in self.lines[self.index].split()[:3]]
        self.index += 1
        return first + second
