from pathlib import Path
import subprocess
import sys

import pytest

from brain import outcar
from actions_py.check_converge import log_was_killed
from actions_py.update_incar import extract_total_moments
from actions_py.zpe import main as zpe_main

ROOT = Path(__file__).resolve().parents[1]


def incar_header(nsw=10, nelm=60):
    return ('vasp.6.4\n' + outcar.LOOK_SEPARATE + '\n' + '\n' * 19
            + f'Startparameter\n NSW = {nsw}; NELM = {nelm}\n IBRION = 2\n'
            + outcar.LOOK_SEPARATE + '\n')


@pytest.mark.parametrize('content', ['', '\n', '\n\n', 'last', 'a\nb\n', 'a\r\nb\r\n',
                                      'αβ\n中文\nlast', 'a' * 500 + '\nlast\n'])
@pytest.mark.parametrize('chunk_size', [1, 2, 7, 64, 65536])
def test_reverse_lines_across_chunks(tmp_path, content, chunk_size):
    path = tmp_path / 'OUTCAR'
    path.write_bytes(content.encode())
    assert list(outcar.reverse_lines(path, chunk_size)) == content.splitlines()[::-1]


def test_final_energy_and_live_file(tmp_path):
    path = tmp_path / 'OUTCAR'
    path.write_text('energy(sigma->0) = -1.5\n' + 'unrelated output\n' * 10000
                    + 'free  energy   TOTEN = -2.6 eV\n'
                    + 'energy without entropy = -2.4 energy(sigma->0) = -2.5\n')
    assert outcar.get_energy(path) == -2.5
    assert outcar.get_toten(path) == -2.6
    with path.open('a') as handle:
        handle.write('energy(sigma->0) = -3.25D+00')
    assert outcar.get_energy(path) == -3.25
    path.write_text('free energy TOTEN = -4.0 eV\n')
    assert outcar.get_energy(path, fallback_toten=True) == -4.0
    with pytest.raises(ValueError, match='No DFT energy'):
        outcar.get_energy(path)
    path.write_text('unfinished output\n')
    with pytest.raises(ValueError):
        outcar.get_energy(path, fallback_toten=True)


def test_final_reads_do_not_scan_file_start(tmp_path, monkeypatch):
    path = tmp_path / 'OUTCAR'
    path.write_text('prefix\n' * 100000 + 'energy(sigma->0) = -9.0\n')
    original_open = Path.open
    reads = []

    class TrackedFile:
        def __init__(self, handle):
            self.handle = handle
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.handle.close()
        def __getattr__(self, name):
            return getattr(self.handle, name)
        def read(self, size=-1):
            reads.append((self.handle.tell(), size))
            return self.handle.read(size)

    def tracked_open(self, *args, **kwargs):
        return TrackedFile(original_open(self, *args, **kwargs))

    monkeypatch.setattr(Path, 'open', tracked_open)
    assert outcar.get_energy(path) == -9.0
    assert sum(size for _, size in reads) <= 65536
    assert all(offset > 0 for offset, _ in reads)


def test_last_magnetization_table(tmp_path):
    path = tmp_path / 'OUTCAR'
    table = ('magnetization (x)\n\n# of ion s p d tot\n----------------\n'
             ' 1 0.1 0.2 0.3 0.6\n 2 -0.1 0.0 0.0 -0.1\n'
             '----------------\ntot 0.0 0.2 0.3 0.5\n')
    path.write_text(table.replace('0.6', '9.9') + 'padding\n' * 20000 + table)
    assert outcar.get_mag(path) == {1: [0.1, 0.2, 0.3, 0.6], 2: [-0.1, 0., 0., -0.1]}
    assert extract_total_moments(path) == [0.6, -0.1]
    path.write_text(table.split(' 2 ')[0])  # interrupted table
    assert outcar.get_mag(path) == {1: [0.1, 0.2, 0.3, 0.6]}


def test_frequencies_preserve_degenerate_modes(tmp_path, capsys):
    path = tmp_path / 'OUTCAR'
    mode = ' 1 f  = 3.0 THz 18.0 2PiTHz 100.0 cm-1 12.0 meV\n'
    path.write_text(mode + mode + ' 3 f/i= 1.0 THz 6.0 2PiTHz 20.0 cm-1 2.0 meV\n')
    assert outcar.get_frequencies(path) == ([100., 100.], [12., 12.], [20.], [2.])
    assert outcar.get_freq(path) == ([100., 100.], [12., 12.])
    assert outcar.get_freq_i(path) == ([20.], [2.])
    assert zpe_main(['-i', str(path), '--show-imag']) == 0
    output = capsys.readouterr().out
    # Preserve zpe.py's existing exact-pair deduplication policy.
    assert 'ZPE: 0.006000 eV' in output
    assert 'Imaginary modes detected: 1' in output


@pytest.mark.parametrize('nsw,ionic,electronic,markers,converged,action', [
    (0, 1, 5, outcar.LOOK_ELEC_CONVERGE, True, None),
    (10, 3, 5, outcar.LOOK_CONVERGE, True, None),
    (10, 3, 60, outcar.LOOK_CONVERGE, False, 'rerun'),
    (10, 1, 5, '', False, 'scratch'),
    (10, 3, 5, '', False, 'rerun'),
])
def test_convergence_and_automation(tmp_path, nsw, ionic, electronic, markers, converged, action):
    path = tmp_path / 'OUTCAR'
    path.write_text(incar_header(nsw) + f'--- Iteration {ionic}( {electronic}) ---\n'
                    + markers + '\nVoluntary context switches: 1\n')
    summary = outcar.summarize_convergence(path)
    assert (summary.nsw, summary.nelm) == (nsw, 60)
    assert (summary.ionic_step, summary.electronic_step) == (ionic, electronic)
    assert summary.converged == converged
    assert summary.action == action
    assert summary.finished
    command = [sys.executable, str(ROOT / 'actions_py/check_converge.py'),
               '--skip-slurm', '--automation', str(tmp_path)]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    expected = 12 if converged else (11 if action == 'rerun' else 10)
    assert result.returncode == expected, result.stderr


def test_missing_and_empty_files(tmp_path):
    assert outcar.summarize_convergence(tmp_path).action == 'scratch'
    path = tmp_path / 'OUTCAR'
    path.touch()
    assert outcar.get_incar(path) == {}
    assert outcar.get_last_iteration(path) == (0, 0)
    assert not outcar.summarize_convergence(path).converged
    with pytest.raises(ValueError):
        outcar.get_mag(path)
    with pytest.raises(FileNotFoundError):
        outcar.get_energy(tmp_path / 'missing')


def test_tail_kill_marker_window(tmp_path):
    path = tmp_path / 'vasp.log'
    path.write_text('KILLED BY SIGNAL: 9\n' + 'normal\n' * 100)
    assert not log_was_killed(path)
    with path.open('a') as handle:
        handle.write('KILLED BY SIGNAL: 9')
    assert log_was_killed(path)
    assert not log_was_killed(path, 0)


def test_geometry_and_imaginary_mode(tmp_path):
    path = tmp_path / 'OUTCAR'
    path.write_text('POSITION      TOTAL-FORCE\n----------------\n'
                    '1 2 3 4 5 6\n7 8 9 0 1 2\n----------------\n'
                    'Eigenvectors after division by SQRT(mass)\n'
                    '1 f/i= 1 THz 2 2PiTHz 10 cm-1 1 meV\nX Y Z dx dy dz\n'
                    '0 0 0 0.1 0.2 0.3\n0 0 0 0.4 0.5 0.6\n'
                    '2 f/i= 2 THz 3 2PiTHz 20 cm-1 2 meV\nX Y Z dx dy dz\n'
                    '0 0 0 0.7 0.8 0.9\n0 0 0 1.0 1.1 1.2\n')
    assert outcar.get_position(path) == [['1', '2', '3'], ['7', '8', '9']]
    expected = [['0.7', '0.8', '0.9'], ['1.0', '1.1', '1.2']]
    assert outcar.get_imaginary_mode(path, 2) == expected
    assert outcar.get_imaginary_mode(path, 2, mass_weighted=True) == expected
