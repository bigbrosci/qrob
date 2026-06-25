"""
Generate HCP Ruthenium bulk structure using ASE
"""

from ase.build import bulk
from ase.io import write
from ase.visualize import view

# Create HCP Ruthenium bulk structure
ru_hcp = bulk('Ru', 'hcp', a=2.706, c=4.282)

# Display basic structure information
print("HCP Ruthenium Structure")
print("=" * 40)
print(f"Number of atoms: {len(ru_hcp)}")
print(f"Cell parameters:\n{ru_hcp.cell}")
print(f"Positions:\n{ru_hcp.positions}")
print(f"Chemical symbols: {ru_hcp.get_chemical_symbols()}")

# Save structure to file
write('Ru_hcp.cif', ru_hcp)  # CIF format
write('Ru_hcp.vasp', ru_hcp)  # VASP format
print("\nStructure saved to:")
print("  - Ru_hcp.cif")
print("  - Ru_hcp.vasp")

# Optional: Visualize the structure (requires X11 or display)
# Uncomment the line below if you have a graphical environment
# view(ru_hcp)