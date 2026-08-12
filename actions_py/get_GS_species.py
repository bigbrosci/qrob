#!/usr/bin/env python3
"""Collect DFT and thermochemical energies for gas and surface species."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

from ase.io import read
from ase.thermochemistry import HarmonicThermo, IdealGasThermo
from scipy.constants import Avogadro, c, e, h


# Conditions requested for every calculation.
TEMPERATURE = 298.15  # K
PRESSURE = 101_325.0  # Pa (1 atm)

# IdealGasThermo needs the molecular geometry and external rotational symmetry
# number.  Keys are directory names with the ``_gas`` suffix removed.
GAS_PROPERTIES = {
    "CO": ("linear", 1),
    "CO2": ("linear", 2),
    "H2": ("linear", 2),
    "H2O": ("nonlinear", 2),
    "CH2O": ("nonlinear", 2),
    "HCOOH": ("nonlinear", 1),
    "CH3OH": ("nonlinear", 1),
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


def vibrational_energies(calc_dir: Path) -> list[float]:
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
    return [number * h * c * 100.0 / e for number in wavenumbers]


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


def thermochemistry(calc_dir: Path) -> tuple[float, float, float, float, float, float]:
    energy = dft_energy(calc_dir / "OUTCAR")
    is_gas = any(part.endswith("_gas") for part in calc_dir.parts)
    vib_energies = vibrational_energies(calc_dir)

    if is_gas:
        species = gas_name(calc_dir)
        try:
            geometry, symmetry_number = GAS_PROPERTIES[species]
        except KeyError as exc:
            known = ", ".join(GAS_PROPERTIES)
            raise ValueError(
                f"gas properties are not defined for {species!r}; known species: {known}"
            ) from exc

        thermo = IdealGasThermo(
            vib_energies=vib_energies,
            potentialenergy=energy,
            atoms=atoms_from(calc_dir),
            geometry=geometry,
            symmetrynumber=symmetry_number,
            spin=0,
        )
        zpe = thermo.get_ZPE_correction()
        entropy = thermo.get_entropy(TEMPERATURE, PRESSURE, verbose=False)
        free_energy = thermo.get_gibbs_energy(
            TEMPERATURE, PRESSURE, verbose=False
        )
    else:
        thermo = HarmonicThermo(
            vib_energies=vib_energies, potentialenergy=energy
        )
        zpe = thermo.get_ZPE_correction()
        entropy = thermo.get_entropy(TEMPERATURE, verbose=False)
        # For an adsorbate ASE computes Helmholtz free energy.  The CSV keeps the
        # conventional, shared column name G for convenient downstream use.
        free_energy = thermo.get_helmholtz_energy(TEMPERATURE, verbose=False)

    entropy_j_mol_k = entropy * e * Avogadro
    return (
        energy,
        zpe,
        TEMPERATURE * entropy,
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


def write_csv(root: Path, output: Path) -> tuple[int, int]:
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
                values = thermochemistry(calc_dir)
            except Exception as exc:
                errors += 1
                print(f"Warning: {relative_path}: {exc}", file=sys.stderr)
                try:
                    energy = f"{dft_energy(calc_dir / 'OUTCAR'):.10f}"
                except Exception:
                    energy = ""
                writer.writerow(
                    [relative_path, f"{TEMPERATURE:.10f}", energy, "", "", "", "", ""]
                )
                continue
            writer.writerow(
                [
                    relative_path,
                    f"{TEMPERATURE:.10f}",
                    *(f"{value:.10f}" for value in values),
                ]
            )
            rows_written += 1
    return rows_written, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path("."), help="directory to scan (default: .)"
    )
    parser.add_argument(
        "--output", type=Path, default=Path("GS_species.csv"), help="output CSV"
    )
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output.resolve()
    written, errors = write_csv(root, output)
    print(
        f"Wrote {output} at T={TEMPERATURE:g} K and P={PRESSURE:g} Pa "
        f"({written} complete rows, {errors} rows with warnings)."
    )
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
