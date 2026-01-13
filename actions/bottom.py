import argparse
import sys
import os
from ase.io import read, write
import numpy as np

# ensure repo root on sys.path so brain.poscar can be imported when running script
script_dir = os.path.dirname(os.path.realpath(__file__))
repo_root = os.path.abspath(os.path.join(script_dir, '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
try:
    from brain.poscar import parse_atom_targets
except Exception:
    parse_atom_targets = None


def main():
    parser = argparse.ArgumentParser(description='Shift POSCAR so bottom at z=offset and optionally center selected atoms in XY')
    parser.add_argument('-i', '--input', default='POSCAR', help='Input POSCAR/CONTCAR file')
    parser.add_argument('--z-offset', type=float, default=0.1, help='Z coordinate after bottoming (default: 0.1 Å)')
    parser.add_argument('--center', nargs='*', help='Element symbols or 0-based indices to use for XY centering (default: Cu then Mn)')
    parser.add_argument('--out-bottom', default='POSCAR_bottomed.vasp', help='Output filename for bottomed structure')
    parser.add_argument('--out-centered', default='POSCAR_centered.vasp', help='Output filename for centered structure')
    args = parser.parse_args()

    infile = args.input
    if not os.path.exists(infile):
        print(f"Error: input file '{infile}' not found", file=sys.stderr)
        sys.exit(2)

    atoms = read(infile, format='vasp')

    # Bottoming: translate so minimum z becomes z_offset
    positions = atoms.get_positions()
    lowest_z = float(np.min(positions[:, 2]))
    dz = args.z_offset - lowest_z
    atoms.translate([0.0, 0.0, dz])
    write(args.out_bottom, atoms, format='vasp', vasp5=True)
    print(f"Wrote bottomed structure to {args.out_bottom} (translated by dz={dz:.4f} Å)")

    # Centering: determine which atoms to use for XY centering
    symbols = atoms.get_chemical_symbols()
    natoms = len(symbols)

    if args.center:
        if parse_atom_targets is None:
            print('Error: parse_atom_targets not available; install brain.poscar', file=sys.stderr)
            sys.exit(3)
        idxs0 = parse_atom_targets(args.center, infile)
        if not idxs0:
            print('No atoms matched center selection; aborting centering', file=sys.stderr)
            sys.exit(0)
        sel_indices = idxs0
    else:
        # default: try Cu, then Mn
        sel_indices = [i for i, s in enumerate(symbols) if s == 'Cu']
        if not sel_indices:
            sel_indices = [i for i, s in enumerate(symbols) if s == 'Mn']
        if not sel_indices:
            print('No Cu or Mn atoms found to center on; skipping centering', file=sys.stderr)
            return

    sel_positions = atoms.get_positions()[sel_indices]
    # select the atom with highest z among selection
    highest_idx_rel = int(np.argmax(sel_positions[:, 2]))
    highest_idx = sel_indices[highest_idx_rel]
    highest_pos = atoms.get_positions()[highest_idx]

    # compute slab center in XY using cell vectors a and b
    cell = atoms.get_cell()
    # cell rows are vectors a, b, c; take first two and average their XY components
    xy_center = (cell[0][:2] + cell[1][:2]) / 2.0

    translation_xy = xy_center - highest_pos[:2]
    atoms.translate([float(translation_xy[0]), float(translation_xy[1]), 0.0])
    atoms.wrap()
    write(args.out_centered, atoms, format='vasp', vasp5=True)
    print(f"Centered atom index {highest_idx} ({symbols[highest_idx]}) to XY center; wrote {args.out_centered}")


if __name__ == '__main__':
    main()

