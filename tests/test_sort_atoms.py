from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
from ase import Atoms
from ase.io import read, write


SCRIPT = Path(__file__).resolve().parents[1] / "actions_py" / "sort_atoms.py"


@pytest.mark.parametrize("positional", [True, False])
def test_custom_element_order(tmp_path, positional):
    path = tmp_path / "POSCAR"
    atoms = Atoms("OHCuCH", positions=[[0, 0, z] for z in range(5)],
                  cell=[10, 10, 10], pbc=True)
    write(path, atoms, format="vasp")
    original = path.read_bytes()
    elements = ["Cu", "C", "H", "O"]
    args = [str(path), *elements] if positional else ["-i", str(path), "--elements", *elements]
    result = subprocess.run([sys.executable, str(SCRIPT), *args],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    sorted_atoms = read(str(path) + "_sorted", format="vasp")
    assert sorted_atoms.get_chemical_symbols() == ["Cu", "C", "H", "H", "O"]
    np.testing.assert_allclose(sorted_atoms.positions, atoms.positions[[2, 3, 1, 4, 0]])
    assert path.read_bytes() == original


@pytest.mark.parametrize("extra", [["-i", "other"], ["--elements", "O", "Cu"]])
def test_conflicting_arguments(extra):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "POSCAR", "Cu", "O", *extra],
        capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert "not both" in result.stderr
