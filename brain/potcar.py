#!/usr/bin/env python3
"""Utilities for reading and handling POTCAR files.

This module expects POTCAR libraries under ~/bin/qrob/books/potpaw_PBE.<version>/
and provides helpers to concatenate POTCARs and extract metadata.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List, Tuple


def _default_potcar_base() -> Path:
    home = Path.home()
    return home / 'bin' / 'qrob' / 'books'


def get_potcar_data(version: str = '64') -> Dict:
    """Read the precomputed data_potcars file for the given POTPAW version.

    Returns an empty dict if the file does not exist.
    """
    data_file = _default_potcar_base() / f'potpaw_PBE.{version}' / 'data_potcar'
    # support both 'data_potcars' and older 'data_potcar'
    if not data_file.exists():
        data_file = _default_potcar_base() / f'potpaw_PBE.{version}' / 'data_potcars'
    if not data_file.exists():
        return {}
    text = data_file.read_text()
    try:
        return ast.literal_eval(text)
    except Exception:
        return eval(text)


def concatenate(ele_list: List[str], version: str = '64', out_path: str = 'POTCAR') -> None:
    """Concatenate POTCAR files for elements in ``ele_list`` into ``out_path``.

    The function looks under the default potcar base for a folder named
    ``potpaw_PBE.<version>`` and for each element directory copies its POTCAR.
    It will try both ``ELEMENT`` and ``ELEMENT_sv`` directories.
    """
    base = _default_potcar_base() / f'potpaw_PBE.{version}'
    if not base.exists():
        raise FileNotFoundError(f'POTPAW base path not found: {base}')

    out_file = Path(out_path)
    with out_file.open('w') as fout:
        for ele in ele_list:
            print(f'Add {ele} to {out_file.name}')
            candidates = [base / ele / 'POTCAR', base / f'{ele}_sv' / 'POTCAR']
            for p in candidates:
                if p.exists():
                    fout.write(p.read_text())
                    break
            else:
                raise FileNotFoundError(f'POTCAR for element {ele} not found in {base}')


def get_potcar_infor(potcar_file: str, titel_line_index: int) -> Dict[str, str]:
    """Extract metadata for a single POTCAR entry given the index of its TITEL line.

    ``titel_line_index`` is the 0-based line number where a line containing
    'TITEL' occurs in the concatenated POTCAR file. This function reads nearby
    lines to parse TYPE, NAME, DATE, ZVAL and other key=value pairs.
    """
    lines = Path(potcar_file).read_text().splitlines()
    i = titel_line_index
    info: Dict[str, str] = {}

    def safe_get(idx: int) -> str:
        return lines[idx].strip() if 0 <= idx < len(lines) else ''

    # First, try to parse a TITEL line at the given index (preferred source of NAME/DATE/TYPE)
    titel_line = safe_get(i)
    if 'TITEL' in titel_line or 'TITEL' in titel_line.upper():
        # Example: "TITEL  = PAW_PBE Mn_pv 02Aug2007"
        right = titel_line.split('=', 1)[1].strip() if '=' in titel_line else titel_line
        # remove surrounding quotes if present
        right = right.strip('"').strip()
        tparts = right.split()
        if len(tparts) >= 1:
            info['TYPE'] = tparts[0]
        if len(tparts) >= 2:
            info['NAME'] = tparts[1]
        if len(tparts) >= 3:
            info['DATE'] = tparts[2]

    # helper to parse key/value items; normalise keys to upper-case without spaces
    def parse_item(k: str, v: str) -> None:
        key = k.strip().upper()
        val = v.strip()
        if key == 'POMASS':
            # store as raw string but trim
            info['POMASS'] = val.split()[0]
        elif key == 'ZVAL':
            info['ZVAL'] = val.split()[0]
        elif key == 'VRHFIN':
            info['VRHFIN'] = val
        else:
            info[key] = val.split()[0] if val else ''

    # scan a small window around the TITEL line for key=value metadata
    for line in lines[max(i - 8, 0): i + 20]:
        if not line:
            continue
        # skip lines that are solely separators
        if line.strip().startswith('='):
            continue
        # lines can contain multiple items separated by ';'
        parts = [p.strip() for p in line.split(';') if p.strip()]
        for p in parts:
            if '=' in p:
                k, v = (s.strip() for s in p.split('=', 1))
                parse_item(k, v)

    return info


def get_multiple_potcar_infor(potcar_file: str) -> Tuple[Dict[str, Dict[str, str]], List[str]]:
    """Parse a concatenated POTCAR and return a dict of per-element info and the element order list."""
    text = Path(potcar_file).read_text().splitlines()
    dict_potcars: Dict[str, Dict[str, str]] = {}
    ele_list: List[str] = []
    for idx, line in enumerate(text):
        if 'TITEL' in line:
            titel_line = line.rstrip()
            # extract name from the TITEL line after '='; prefer last token
            pot_name = None
            if '=' in titel_line:
                right = titel_line.split('=', 1)[1].strip().strip('"')
                tokens = right.split()
                if tokens:
                    pot_name = tokens[-1]
            if not pot_name:
                parts = titel_line.split()
                pot_name = parts[3] if len(parts) >= 4 else f'UNKNOWN_{idx}'
            ele_list.append(pot_name)
            dict_potcars[pot_name] = get_potcar_infor(potcar_file, idx)
    return dict_potcars, ele_list


def get_potcars_infor(version: str) -> Dict[str, Dict[str, str]]:
    """Generate the data_potcars file for a given POTPAW version (e.g. '52','54','64')."""
    base = _default_potcar_base() / f'potpaw_PBE.{version}'
    if not base.exists():
        raise FileNotFoundError(f'POTPAW folder not found: {base}')
    elements = [p.name for p in base.iterdir() if p.is_dir()]
    dict_potcars: Dict[str, Dict[str, str]] = {}
    for ele in elements:
        potcar = base / ele / 'POTCAR'
        if not potcar.exists():
            continue
        # when building from individual POTCARs we don't have TITEL indices; use 7 as legacy default
        dict_potcars[ele] = get_potcar_infor(str(potcar), 7)
    data_file = base / 'data_potcars'
    data_file.write_text(str(dict_potcars))
    return dict_potcars


def read_potcar(potcar_file: str) -> None:
    """Print basic information of a POTCAR file (concatenated) to stdout.

    The output is an aligned table with columns: NAME, DATE, ZVAL, ENMAX,
    POMASS, TYPE, VRHFIN. Missing values are shown as empty strings.
    """
    dict_potcars, ele_list = get_multiple_potcar_infor(potcar_file)

    headers = ['NAME', 'TYPE', 'DATE', 'ZVAL', 'ENMAX', 'POMASS', 'VRHFIN']

    # Collect rows in display order
    rows: List[List[str]] = []
    for ele in ele_list:
        v = dict_potcars.get(ele, {})
        row = [str(v.get(h, '') or '') for h in headers]
        rows.append(row)

    # Compute column widths
    widths = [len(h) for h in headers]
    for r in rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(cell))

    # Print banner and header
    print('\n')
    banner = '%' * 25
    print(f"{banner} POTCAR Information {banner}\n")

    # Header line
    header_line = '  '.join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(header_line)
    print('-' * len(header_line))

    # Rows
    for r in rows:
        print('  '.join(r[i].ljust(widths[i]) for i in range(len(headers))))
    print('-' * len(header_line))
    print('\n' + '%' * 29 + ' Good Luck! ' + '%' * 29 + '\n')
