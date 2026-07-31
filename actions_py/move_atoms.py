#!/usr/bin/env python3
import sys

from ase.io import read, write


"""
This script is used to copy the atoms (molecule) from file_from (template) to the file_to.
You can use this script for the following cases:
1) optimize the adsorbates on the smaller slab with 2 layers, and then move the atoms to the larger slab with 4 layers.    
2) optimize the adsorbates on Pt(111) surface, and copy the atoms to Pd(111) surface. 
3) the atoms are copied to the end of the file_to, No merging for duplicated elements.
4) if you want to merge the duplicate elements, use add.py action instead.
    
Remember:
The coordinates of the copied atoms need to be modified when the surface in two slabs are different.    
add.py can do the similar thing.

"""


def get_atom_indices(atoms, selections):
    """Expand element names and inclusive zero-based index ranges."""
    indices = []

    def append(index):
        if not 0 <= index < len(atoms):
            raise ValueError(
                f'Atom index {index} is outside the valid range 0-{len(atoms) - 1}.'
            )
        if index not in indices:
            indices.append(index)

    symbols = atoms.get_chemical_symbols()
    for selection in selections:
        if selection.isdigit():
            append(int(selection))
        elif '-' in selection:
            start_text, end_text = selection.split('-', 1)
            if not start_text.isdigit() or (end_text and not end_text.isdigit()):
                raise ValueError(f'Invalid atom range: {selection}')
            start = int(start_text)
            end = int(end_text) if end_text else len(atoms) - 1
            if end < start:
                raise ValueError(f'Invalid descending atom range: {selection}')
            for index in range(start, end + 1):
                append(index)
        else:
            for index, symbol in enumerate(symbols):
                if symbol == selection:
                    append(index)

    if not indices:
        raise ValueError('The atom selection did not match any atoms.')
    return indices


def group_indices_by_element(atoms, indices):
    """Keep each copied element in one contiguous POSCAR block."""
    symbols = atoms.get_chemical_symbols()
    element_order = list(dict.fromkeys(symbols[index] for index in indices))
    return [
        index
        for element in element_order
        for index in indices
        if symbols[index] == element
    ]


def copy_atoms_cartesian(source, destination, indices):
    """Append a PBC-unwrapped selection using Cartesian positions in Angstrom."""
    anchor = indices[0]
    indices = group_indices_by_element(source, indices)
    copied = source[indices]
    copied.set_positions([
        source.positions[anchor]
        + source.get_distance(anchor, index, mic=True, vector=True)
        for index in indices
    ])

    # Copied atoms are free to move, matching the previous T T T behavior.
    copied.set_constraint()
    destination.extend(copied)


def main():
    if len(sys.argv) <= 3:
        print('Command: move_atoms.py file_from file_to atoms')
        print('Example: move_atoms.py POSCAR1 POSCAR2 C H 12')
        return 1

    _, file_from, file_to, *selections = sys.argv
    source = read(file_from, format='vasp')
    destination = read(file_to, format='vasp')

    indices = get_atom_indices(source, selections)
    copy_atoms_cartesian(source, destination, indices)

    out_name = 'POSCAR_move'
    write(
        out_name,
        destination,
        format='vasp',
        direct=False,
        sort=False,
        vasp5=True,
    )
    print(f'\nThe output file is:\t{out_name}')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except ValueError as error:
        sys.exit(f'Error: {error}')
