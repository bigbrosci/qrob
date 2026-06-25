from ase.io import read, write
from ase.build import surface
from ase.visualize import view

# 1. Read bulk structure (VASP CONTCAR)
bulk = read('CONTCAR')

# 2. Create (111) surface
# indices = (1,1,1)
# layers = number of atomic layers in slab
# vacuum = vacuum thickness (Å)
slab = surface(bulk, (1, 1, 1), layers=6, vacuum=15)

# Optional: repeat slab in x,y directions (remove repeat() for 1x1)
# slab = slab.repeat((2, 2, 1))  # Use this line to create (2x2)

# 3. Optional: center slab (adds symmetric vacuum)
slab.center(axis=2)

# 4. Save slab
write('MgO_111.vasp', slab, format='vasp')

# 5. Visualize (optional)
view(slab)
