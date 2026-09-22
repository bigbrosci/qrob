from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from brain import vasprun
from actions_py import update_incar

ROOT = Path(__file__).resolve().parents[1]
ATOMINFO = '<atominfo><array name="atoms"><set><rc><c>H</c></rc></set></array></atominfo>'


def xml_step(energy):
    return f'''<calculation><energy><i name="e_fr_energy">{energy}</i>
    <i name="e_0_energy">999</i></energy><structure><crystal><varray name="basis">
    <v>1 0 0</v><v>0 1 0</v><v>0 0 1</v></varray></crystal>
    <varray name="positions"><v>0.1 0.2 0.3</v></varray></structure>
    <varray name="forces"><v>1 2 3</v></varray><varray name="stress">
    <v>1 4 6</v><v>4 2 5</v><v>6 5 3</v></varray></calculation>'''


@pytest.mark.parametrize('stdlib', [False, True])
def test_stream_xml_and_refresh_after_append(tmp_path, monkeypatch, stdlib):
    if stdlib:
        monkeypatch.setattr(vasprun, 'LXML_ET', None)
    path = tmp_path / 'vasprun.xml'
    path.write_text('<modeling>' + ATOMINFO + xml_step(-1) + xml_step(-2) + '</modeling>')
    assert vasprun.get_atom_symbols(path) == ['H']
    assert [step.energy for step in vasprun.parse_calculation_steps(path)] == [-1, -2]
    final = vasprun.get_final_step(path)
    assert final.forces == [[1., 2., 3.]]
    assert final.stress == [1., 2., 3., 4., 5., 6.]
    path.write_text('<modeling>' + ATOMINFO + xml_step(-3) + '</modeling>')
    assert vasprun.get_final_energy(path) == -3


def test_interrupted_xml_recovery(tmp_path):
    if vasprun.LXML_ET is None:
        pytest.skip('lxml is optional')
    path = tmp_path / 'vasprun.xml'
    path.write_text('<modeling>' + ATOMINFO + xml_step(-1) + '<calculation><energy>')
    assert vasprun.get_atom_symbols(path) == ['H']
    assert vasprun.get_final_energy(path) == -1


def test_xml_to_mlab(tmp_path):
    pytest.importorskip('ase')
    from brain.ml_ab import parse_vasprun_to_mlab_configurations
    path = tmp_path / 'vasprun.xml'
    path.write_text('<modeling>' + ATOMINFO + xml_step(-1) + xml_step(-2) + '</modeling>')
    configurations = parse_vasprun_to_mlab_configurations(path)
    assert [item.total_energy for item in configurations] == [-1, -2]
    assert configurations[-1].atom_symbols == ['H']
    assert configurations[-1].atom_forces == [[1., 2., 3.]]


@pytest.mark.parametrize('spin', [1, 2])
def test_dcenter_numerical_result(tmp_path, spin):
    energies = np.linspace(-5, 5, 21)
    densities = np.ones_like(energies)
    data = np.column_stack([energies, densities] + ([2 * densities] if spin == 2 else []))
    path = tmp_path / 'dos.dat'
    np.savetxt(path, data)
    result = subprocess.run([sys.executable, str(ROOT / 'actions_py/dcenter.py'), str(path)],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    # Existing upper-bound-exclusive behavior is preserved: [-5, 4.5].
    if spin == 1:
        assert 'd-band center is -0.25' in result.stdout
        assert 'electron counting 9.5' in result.stdout
    else:
        assert 'd-band_average is  -0.250000' in result.stdout
        assert 'Total Electron is  28.500000' in result.stdout


def test_stream_database_aggregation(tmp_path, monkeypatch):
    case = tmp_path / 'case'
    case.mkdir()
    csv = update_incar.write_case_csv(case, ['Fe', 'Fe', 'O'], [2., 4., 0.1])
    summary = update_incar.summarize_by_element(update_incar.collect_case_rows([csv]))
    assert summary == {'Fe': 3., 'O': 0.1}
    counts = update_incar.collect_sample_counts([csv])
    assert counts['Fe'] == {'atom_count': 2, 'source_csv_count': 1}
    incar = tmp_path / 'incar.py'
    incar.write_text('# BEGIN MAG_VALUE_DATABASE\nmag_value_database = {}\n# END MAG_VALUE_DATABASE\n')
    monkeypatch.setattr(update_incar, 'INCAR_PATH', incar)
    update_incar.update_incar_py(summary, counts)
    values = {}
    exec(incar.read_text(), values)
    assert values['mag_value_database'] == summary
    assert values['mag_value_database_counts'] == counts


def test_md_streams_coordinates_and_first_break(tmp_path):
    pytest.importorskip('ase')
    from ase import Atoms
    from ase.io import write
    write(tmp_path / 'POSCAR', Atoms('OO', positions=[[0, 0, 0], [1, 0, 0]], cell=[10, 10, 10], pbc=True))
    (tmp_path / 'vasprun.xml').write_text('''<modeling>
<varray name="positions" >
<v>0 0 0</v>
<v>0.1 0 0</v>
</varray>
<varray name="positions" >
<v>0 0 0</v>
<v>0.3 0 0</v>
</varray>
</modeling>''')
    result = subprocess.run([sys.executable, str(ROOT / 'actions_py/md.py'), '1', '2'],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == '2'
    np.testing.assert_allclose(np.loadtxt(tmp_path / 'data_2'), [[1, 0, 0], [3, 0, 0]])


def test_frequency_geometry_commands(tmp_path):
    pytest.importorskip('ase')
    from ase import Atoms
    from ase.io import read, write
    atoms = Atoms('HH', positions=[[0, 0, 0], [1, 0, 0]], cell=[10, 10, 10], pbc=True)
    write(tmp_path / 'POSCAR', atoms)
    write(tmp_path / 'POSCAR_relax', atoms, format='vasp')
    (tmp_path / 'OUTCAR').write_text('''Eigenvectors after division by SQRT(mass)
1 f/i= 2 THz 3 2PiTHz 20 cm-1 2 meV
X Y Z dx dy dz
0 0 0 0.7 0.8 0.9
0 0 0 1.0 1.1 1.2
''')
    for script in ['frequency_correction.py', 'get_dimer.py']:
        result = subprocess.run([sys.executable, str(ROOT / 'actions_py' / script)],
                                cwd=tmp_path, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    corrected = read(tmp_path / 'POSCAR_corrected', format='vasp')
    np.testing.assert_allclose(corrected.positions, [[0.07, 0.08, 0.09], [1.1, 0.11, 0.12]])
    assert (tmp_path / 'POSCAR_dimer').read_text().endswith('0.7 0.8 0.9\n1.0 1.1 1.2\n')
