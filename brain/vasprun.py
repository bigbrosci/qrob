#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path


LOOK_VERSION = 'name="version"'
LOOK_NEDOS = 'NEDOS'
LOOK_FERMI = 'efermi'
LOOK_KPOINTS = 'kpoints>'


def _load_vasprun(path='vasprun.xml'):
    vasprun = Path(path)
    if not vasprun.is_file():
        raise FileNotFoundError(f'No vasprun.xml file found at {vasprun}')

    lines = vasprun.read_text().splitlines()
    dict_line = {
        LOOK_VERSION: [],
        LOOK_NEDOS: [],
        LOOK_FERMI: [],
        LOOK_KPOINTS: [],
    }
    for num, line in enumerate(lines):
        for key, bucket in dict_line.items():
            if key in line:
                bucket.append(num)
    return lines, dict_line


def get_version(path='vasprun.xml'):
    lines_vasprun, dict_line = _load_vasprun(path)
    line_num_version = dict_line[LOOK_VERSION][-1]
    return lines_vasprun[line_num_version].split()[2].split('>')[1]


def get_nedos(path='vasprun.xml'):
    lines_vasprun, dict_line = _load_vasprun(path)
    line_num_dos = dict_line[LOOK_NEDOS][-1]
    return lines_vasprun[line_num_dos].split()[3].split('<')[0]


def get_fermi(path='vasprun.xml'):
    lines_vasprun, dict_line = _load_vasprun(path)
    line_num_fermi = dict_line[LOOK_FERMI][-1]
    return float(lines_vasprun[line_num_fermi].split()[2])


def get_kpoints(path='vasprun.xml'):
    _, dict_line = _load_vasprun(path)
    return dict_line[LOOK_KPOINTS]
