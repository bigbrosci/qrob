#!/usr/bin/env python3
"""Collect DFT and thermochemical energies for gas and surface species.

Includes NH3 and CH3OH chemistry. Clean slabs use G = E_DFT.
Use --temperature 673 --pressure 100000 for the old example conditions,
and --min-frequency 100 to enable the old optional low-frequency floor.
Gas properties are (geometry, rotational symmetry number, electronic spin);
check these assumptions for the electronic state and isomer being calculated.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

from ase.io import read
from ase.thermochemistry import HarmonicThermo, IdealGasThermo
from scipy.constants import Avogadro, c, e, h


# Default conditions for every calculation.
TEMPERATURE = 298.15  # K
PRESSURE = 101_325.0  # Pa (1 atm)

# IdealGasThermo needs the molecular geometry and external rotational symmetry
# number and electronic spin. Keys are directory names with the ``_gas`` suffix removed.
GAS_PROPERTIES = {
    'CO': ('linear', 1, 0),
    'CO2': ('linear', 2, 0),
    'H2': ('linear', 2, 0),
    'H2O': ('nonlinear', 2, 0),
    'CH2O': ('nonlinear', 2, 0),
    'HCOOH': ('nonlinear', 1, 0),
    'CH3OH': ('nonlinear', 1, 0),
    'N2': ('linear', 2, 0),
    'NH': ('linear', 1, 1),
    'NH2': ('nonlinear', 2, 0.5),
    'NH3': ('nonlinear', 3, 0),
    'NH-N': ('nonlinear', 1, 0.5),
    'NH-NH': ('nonlinear', 2, 0),
    'NH2-N': ('nonlinear', 2, 0),
    'NH2-NH': ('nonlinear', 1, 0.5),
    'NH2-NH2': ('nonlinear', 2, 0),
    'N': ('monatomic', 1, 1.5),
    'H': ('monatomic', 1, 0.5),
    'O': ('monatomic', 1, 1),
    'O2': ('linear', 2, 1),
}

ENERGY_RE = re.compile(r"energy\(sigma->0\)\s*=\s*([-+0-9.Ee]+)")
TOTEN_RE = re.compile(r"free energy\s+TOTEN\s*=\s*([-+0-9.Ee]+)")
WAVENUMBER_RE = re.compile(r"([-+0-9.]+)\s+cm-1")


def dft_energy(outcar: Path) -> float:
    """Return the final sigma->0 energy, falling back to the final TOTEN."""
    sigma_energy = None
    toten = None
    with outcar.open(errors="replace") as handle:
        for line in handle:
            match = ENERGY_RE.search(line)
            if match:
                sigma_energy = float(match.group(1))
            match = TOTEN_RE.search(line)
            if match:
                toten = float(match.group(1))

    if sigma_energy is not None:
        return sigma_energy
    if toten is not None:
        return toten
    raise ValueError(f"no DFT energy found in {outcar}")


def frequency_outcar(calc_dir: Path) -> Path:
    """Find the frequency output used by layouts in this data set."""
    for candidate in (
        calc_dir / "OUTCAR_freq",
        calc_dir / "freq" / "OUTCAR",
        calc_dir / "OUTCAR",
    ):
        if candidate.is_file():
            # The ordinary OUTCAR is useful only if it actually has frequencies.
            if candidate.name != "OUTCAR" or candidate.parent.name == "freq":
                return candidate
            if " f  =" in candidate.read_text(errors="replace"):
                return candidate
    raise FileNotFoundError(f"no vibrational frequencies found in {calc_dir}")


def vibrational_energies(calc_dir: Path, min_frequency: float = 0.0) -> list[float]:
    """Read real VASP modes and return their energies in eV."""
    freq_file = frequency_outcar(calc_dir)
    wavenumbers: list[float] = []
    with freq_file.open(errors="replace") as handle:
        for line in handle:
            # Imaginary modes are printed as ``f/i=`` and are not thermodynamic
            # vibrational modes.
            if " f  =" not in line:
                continue
            match = WAVENUMBER_RE.search(line)
            if match:
                wavenumbers.append(float(match.group(1)))

    if not wavenumbers:
        raise ValueError(f"no real vibrational modes found in {freq_file}")

    # VASP output can occasionally repeat a frequency block.  Preserve order
    # while removing exact duplicate values.
    wavenumbers = list(dict.fromkeys(wavenumbers))
    return [max(number, min_frequency) * h * c * 100.0 / e for number in wavenumbers]


def atoms_from(calc_dir: Path):
    for filename in ("CONTCAR", "POSCAR"):
        path = calc_dir / filename
        if path.is_file():
            atoms = read(path)
            # VASP structures are periodic by default, but an isolated molecule
            # passed to IdealGasThermo must be non-periodic.
            atoms.set_pbc(False)
            return atoms
    raise FileNotFoundError(f"neither CONTCAR nor POSCAR found in {calc_dir}")


def gas_name(calc_dir: Path) -> str:
    """Return the gas species name from the nearest ``*_gas`` directory."""
    for part in reversed(calc_dir.parts):
        if part.endswith("_gas"):
            return part[: -len("_gas")]
    raise ValueError(f"cannot determine gas species from {calc_dir}")


def thermochemistry(
    calc_dir: Path, temperature: float = TEMPERATURE,
    pressure: float = PRESSURE, min_frequency: float = 0.0,
) -> tuple[float, float, float, float, float, float]:
    energy = dft_energy(calc_dir / "OUTCAR")
    is_gas = any(part.endswith("_gas") for part in calc_dir.parts)
    if not is_gas and any(
        part == "slab" or part.startswith("slab_") or part.endswith("_slab")
        for part in calc_dir.parts
    ):
        return energy, 0.0, 0.0, 0.0, 0.0, energy

    if is_gas:
        species = gas_name(calc_dir)
        try:
            geometry, symmetry_number, spin = GAS_PROPERTIES[species]
        except KeyError as exc:
            known = ", ".join(GAS_PROPERTIES)
            raise ValueError(
                f"gas properties are not defined for {species!r}; known species: {known}"
            ) from exc

        # Monatomic gases do not require a frequency calculation.
        vib_energies = ([] if geometry == "monatomic"
                        else vibrational_energies(calc_dir, min_frequency))
        thermo = IdealGasThermo(
            vib_energies=vib_energies,
            potentialenergy=energy,
            atoms=atoms_from(calc_dir),
            geometry=geometry,
            symmetrynumber=symmetry_number,
            spin=spin,
        )
        zpe = thermo.get_ZPE_correction()
        entropy = thermo.get_entropy(temperature, pressure, verbose=False)
        free_energy = thermo.get_gibbs_energy(
            temperature, pressure, verbose=False
        )
    else:
        vib_energies = vibrational_energies(calc_dir, min_frequency)
        thermo = HarmonicThermo(
            vib_energies=vib_energies, potentialenergy=energy
        )
        zpe = thermo.get_ZPE_correction()
        entropy = thermo.get_entropy(temperature, verbose=False)
        # For an adsorbate ASE computes Helmholtz free energy.  The CSV keeps the
        # conventional, shared column name G for convenient downstream use.
        free_energy = thermo.get_helmholtz_energy(temperature, verbose=False)

    entropy_j_mol_k = entropy * e * Avogadro
    return (
        energy,
        zpe,
        temperature * entropy,
        entropy,
        entropy_j_mol_k,
        free_energy,
    )


def calculation_directories(root: Path) -> list[Path]:
    """Find calculation directories, excluding frequency subcalculations."""
    directories = []
    for outcar in root.rglob("OUTCAR"):
        if outcar.parent.name == "freq":
            continue
        directories.append(outcar.parent)
    return sorted(directories, key=lambda path: path.relative_to(root).as_posix())


def write_csv(
    root: Path, output: Path, temperature: float = TEMPERATURE,
    pressure: float = PRESSURE, min_frequency: float = 0.0,
) -> tuple[int, int]:
    rows_written = 0
    errors = 0
    with output.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["path", "T_K", "E_DFT", "ZPE", "TS", "S_eV/K", "S_J/mol/K", "G"]
        )
        for calc_dir in calculation_directories(root):
            relative_path = calc_dir.relative_to(root).as_posix()
            try:
                values = thermochemistry(calc_dir, temperature, pressure, min_frequency)
            except Exception as exc:
                errors += 1
                print(f"Warning: {relative_path}: {exc}", file=sys.stderr)
                try:
                    energy = f"{dft_energy(calc_dir / 'OUTCAR'):.10f}"
                except Exception:
                    energy = ""
                writer.writerow(
                    [relative_path, f"{temperature:.10f}", energy, "", "", "", "", ""]
                )
                continue
            writer.writerow(
                [
                    relative_path,
                    f"{temperature:.10f}",
                    *(f"{value:.10f}" for value in values),
                ]
            )
            rows_written += 1
    return rows_written, errors


def add_condition_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--temperature", type=float, default=TEMPERATURE,
                        help="temperature in K (default: 298.15)")
    parser.add_argument("--pressure", type=float, default=PRESSURE,
                        help="gas pressure in Pa (default: 101325)")
    parser.add_argument("--min-frequency", type=float, default=0.0,
                        help="real-mode floor in cm^-1 (default: no floor)")


def validate_conditions(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    import math

    for name in ("temperature", "pressure", "min_frequency"):
        value = getattr(args, name)
        if not math.isfinite(value) or value < 0 or (name != "min_frequency" and value == 0):
            parser.error(f"invalid --{name.replace('_', '-')}: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path("."), help="directory to scan (default: .)"
    )
    parser.add_argument(
        "--output", type=Path, default=Path("GS_species.csv"), help="output CSV"
    )
    add_condition_arguments(parser)
    args = parser.parse_args()
    validate_conditions(parser, args)

    root = args.root.resolve()
    output = args.output.resolve()
    written, errors = write_csv(root, output, args.temperature, args.pressure, args.min_frequency)
    print(
        f"Wrote {output} at T={args.temperature:g} K and P={args.pressure:g} Pa "
        f"({written} complete rows, {errors} rows with warnings)."
    )
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
