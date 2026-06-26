#!/usr/bin/env python3 
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from actions_py.bootstrap import ensure_repo_root

ensure_repo_root()
import sys
from ase.io import read, write

def switch_atoms(input_file, output_file, index_a, element_a, index_b, element_b):
    # Read the structure
    atoms = read(input_file, format="vasp")

    # Get current symbols and modify them
    symbols = atoms.get_chemical_symbols()
    symbols[index_a] = element_a
    symbols[index_b] = element_b
    atoms.set_chemical_symbols(symbols)

    # Save the modified structure
    write(output_file, atoms, format="vasp")
    print(f"Switched atom {index_a} to {element_a} and atom {index_b} to {element_b}")
    print(f"Updated structure saved to: {output_file}")

# Main logic for command-line execution
if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(len(sys.argv))
        print("Usage: python atom_switch.py INDEX_A ELE_B INDEX_B ELE_A")
        print("Example: python atom_switch.py 7 Mo 19 Ni")
        sys.exit(1)

    # Read command-line arguments
    input_file = "POSCAR"  # Default input file
    output_file = "POSCAR_switched"  # Default output file
    index_a = int(sys.argv[1])  # Atom index A (0-based)
    element_b = sys.argv[2]     # Element to switch to at index A
    index_b = int(sys.argv[3])  # Atom index B (0-based)
    element_a = sys.argv[4]     # Element to switch to at index B

    # Run the switching function
    switch_atoms(input_file, output_file, index_a, element_a, index_b, element_b)
