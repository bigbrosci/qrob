from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
from ase.io import read


SCRIPT = Path(__file__).resolve().parents[1] / "actions_py" / "dire2cart.py"


@pytest.mark.parametrize("mode", ["Direct", "Cartesian"])
@pytest.mark.parametrize("scale", ["2.0", "-480.0"])
def test_conversion_preserves_geometry_and_fixes_layers(tmp_path, mode, scale):
    path = tmp_path / "POSCAR"
    original = (
        f"Si O\n{scale}\n4 0 0\n1 5 0\n0.5 0.2 6\nSi O\n2 2\n"
        f"Selective dynamics\n{mode}\n"
        "0.2 0.3 0.8 F T F\n0.1 0.2 0.0 T T T\n"
        "0.4 0.1 0.3 T T T\n0.3 0.2 0.01 T T T\n"
    )
    path.write_text(original)
    before = read(path, format="vasp")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "-i", str(path), "-s", "2", "-t", "0.2"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    after = read(path, format="vasp")
    np.testing.assert_allclose(after.positions, before.positions)
    np.testing.assert_allclose(after.cell, before.cell)
    assert after.get_chemical_symbols() == before.get_chemical_symbols()
    assert set(after.constraints[0].get_indices()) == {1, 2, 3}
    assert "Cartesian" in path.read_text()
    assert Path(str(path) + "_back").read_text() == original


def test_no_fixed_layers(tmp_path):
    path = tmp_path / "POSCAR"
    path.write_text("H\n1\n1 0 0\n0 1 0\n0 0 1\nH\n1\nDirect\n0 0 0\n")
    result = subprocess.run([sys.executable, str(SCRIPT), "-i", str(path)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert not read(path, format="vasp").constraints
    assert "Found 1 layers" in result.stdout
