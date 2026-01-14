#!/usr/bin/env python3
"""
Adjust slab along z using ASE:
1) Read POSCAR
2) Find bottom/top atom z
3) Shift so bottom atom ends at z = 0.2 Å
4) Set cell c (z-length) = new z_top + 15 Å (=> 15 Å vacuum above slab)
5) Write POSCAR_new
"""

from ase.io import read, write

POSCAR_IN = "POSCAR"
POSCAR_OUT = "POSCAR_new"

BOTTOM_TARGET_Z = 0.2   # Å
VACUUM_ABOVE = 15.0     # Å

# 1) read POSCAR
atoms = read(POSCAR_IN)

# 2) bottom/top z (in Cartesian Å)
z = atoms.positions[:, 2]
z_bottom = z.min()
z_top = z.max()

# 3) shift so bottom becomes 0.2 Å
shift = BOTTOM_TARGET_Z - z_bottom
atoms.positions[:, 2] += shift

# recompute after shift
z2 = atoms.positions[:, 2]
new_z_top = z2.max()

# 4) set box length in z = top + 15 Å
cell = atoms.cell.array.copy()
cell[2, :] = [0.0, 0.0, new_z_top + VACUUM_ABOVE]  # keep orthorhombic z
atoms.set_cell(cell, scale_atoms=False)
atoms.set_pbc([True, True, True])

# 5) save
write(POSCAR_OUT, atoms, format="vasp", direct=True, vasp5=True)

print(f"Original z_bottom={z_bottom:.6f} Å, z_top={z_top:.6f} Å")
print(f"Shifted by {shift:.6f} Å -> new bottom={atoms.positions[:,2].min():.6f} Å")
print(f"New z_top={new_z_top:.6f} Å, new cell z={atoms.cell.lengths()[2]:.6f} Å")
print(f"Wrote: {POSCAR_OUT}")

