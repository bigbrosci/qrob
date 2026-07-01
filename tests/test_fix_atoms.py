from __future__ import annotations

from pathlib import Path

from ase import Atoms
from ase.constraints import FixScaled
from ase.io import read, write

from qrob.actions_py import fix_atoms


def test_fix_atoms_writes_selective_dynamics(tmp_path: Path) -> None:
    atoms = Atoms(
        "H2",
        positions=[[0.0, 0.0, 0.0], [0.0, 0.0, 1.0]],
        pbc=True,
        cell=[[10.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 10.0]],
    )
    atoms.set_constraint(FixScaled([0], mask=(True, False, True)))

    infile = tmp_path / "POSCAR"
    write(infile, atoms, format="vasp", direct=True, vasp5=True)

    output = tmp_path / "POSCAR_fixed"
    exit_code = fix_atoms.main(["-i", str(infile), "--indices", "0", "--flags", "FFF", "-o", str(output)])

    assert exit_code == 0
    assert output.exists()

    written = read(output, format="vasp")
    assert len(written.constraints) == 1
    assert written.constraints[0].__class__.__name__ == "FixAtoms"
