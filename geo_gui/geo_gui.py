#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEO GUI: POSCAR viewer and editor for VASP calculations with p4vasp-like features.

Features:
- Structure visualization (3D & properties)
- Electronic structure analysis (band structure, DOS)
- Charge density visualization
- Convergence analysis
- Structure editing and manipulation
- Multiple file format support

Usage (Command-line mode): 
    python geo_gui.py POSCAR         # View structure info
    python geo_gui.py -v POSCAR      # Verbose mode with atom positions

Usage (GUI mode):
    streamlit run geo_gui.py
"""

import sys
import os
import argparse
import numpy as np
from pathlib import Path
import json

# Check if running in Streamlit mode
def _is_streamlit():
    """Check if we're running under Streamlit."""
    # Check if streamlit is in command line args
    if any('streamlit' in arg for arg in sys.argv):
        return True
    # Check by inspecting the call stack for streamlit modules
    try:
        import inspect
        for frame in inspect.stack():
            if 'streamlit' in frame.filename:
                return True
    except:
        pass
    # Check for streamlit environment
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        ctx = get_script_run_ctx()
        if ctx is not None:
            return True
    except ImportError:
        pass
    return False

STREAMLIT_MODE = _is_streamlit()

# Only import streamlit if in streamlit mode
if STREAMLIT_MODE:
    try:
        import streamlit as st
    except ImportError:
        STREAMLIT_MODE = False


# ---------- POSCAR I/O functions ----------
def read_poscar(filename="POSCAR"):
    """Read VASP POSCAR/CONTCAR file."""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    comment = lines[0].strip()
    scale = float(lines[1].strip())
    
    lattice = np.zeros((3, 3))
    for i in range(3):
        lattice[i] = [float(x) for x in lines[2 + i].split()]
    lattice *= scale
    
    line6 = lines[5].split()
    try:
        counts = [int(x) for x in line6]
        elements = None
        count_line_idx = 5
    except ValueError:
        elements = line6
        counts = [int(x) for x in lines[6].split()]
        count_line_idx = 6
    
    total_atoms = sum(counts)
    
    next_line_idx = count_line_idx + 1
    selective = False
    if lines[next_line_idx].strip()[0].upper() == 'S':
        selective = True
        next_line_idx += 1
    
    coord_line = lines[next_line_idx].strip()
    coord_type = 'Direct' if coord_line[0].upper() in ['D', 'F'] else 'Cartesian'
    next_line_idx += 1
    
    positions = np.zeros((total_atoms, 3))
    constraints = []
    
    for i in range(total_atoms):
        parts = lines[next_line_idx + i].split()
        positions[i] = [float(parts[j]) for j in range(3)]
        if selective and len(parts) >= 6:
            constraints.append([parts[j] for j in range(3, 6)])
        elif selective:
            constraints.append(['T', 'T', 'T'])
    
    return {
        'comment': comment,
        'scale': 1.0,
        'lattice': lattice,
        'elements': elements,
        'counts': counts,
        'total_atoms': total_atoms,
        'selective': selective,
        'coord_type': coord_type,
        'positions': positions,
        'constraints': constraints if constraints else None
    }


def write_poscar(structure, filename="POSCAR_new"):
    """Write structure to POSCAR format."""
    lines = []
    lines.append(structure['comment'])
    lines.append(f"  {structure['scale']:.10f}")
    
    for vec in structure['lattice']:
        lines.append(f"  {vec[0]:18.10f}  {vec[1]:18.10f}  {vec[2]:18.10f}")
    
    if structure['elements']:
        lines.append("  " + "  ".join(structure['elements']))
    lines.append("  " + "  ".join(map(str, structure['counts'])))
    
    if structure['selective']:
        lines.append("Selective dynamics")
    
    lines.append(structure['coord_type'])
    
    for i, pos in enumerate(structure['positions']):
        line = f"  {pos[0]:18.10f}  {pos[1]:18.10f}  {pos[2]:18.10f}"
        if structure['selective'] and structure['constraints']:
            line += f"  {structure['constraints'][i][0]}  {structure['constraints'][i][1]}  {structure['constraints'][i][2]}"
        lines.append(line)
    
    with open(filename, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    
    return '\n'.join(lines)


def get_cartesian_positions(structure):
    """Convert fractional to Cartesian coordinates."""
    if structure['coord_type'] == 'Direct':
        return structure['positions'] @ structure['lattice']
    return structure['positions'].copy()


def get_fractional_positions(structure):
    """Convert Cartesian to fractional coordinates."""
    if structure['coord_type'] == 'Cartesian':
        return structure['positions'] @ np.linalg.inv(structure['lattice'])
    return structure['positions'].copy()


def get_atom_list(structure):
    """Get list of element symbols for each atom."""
    atoms = []
    if structure['elements']:
        for elem, count in zip(structure['elements'], structure['counts']):
            atoms.extend([elem] * count)
    else:
        atoms = [f"X" for _ in range(structure['total_atoms'])]
    return atoms


def calc_lattice_params(lattice):
    """Calculate lattice parameters."""
    a = np.linalg.norm(lattice[0])
    b = np.linalg.norm(lattice[1])
    c = np.linalg.norm(lattice[2])
    alpha = np.degrees(np.arccos(np.clip(np.dot(lattice[1], lattice[2]) / (b * c), -1, 1)))
    beta = np.degrees(np.arccos(np.clip(np.dot(lattice[0], lattice[2]) / (a * c), -1, 1)))
    gamma = np.degrees(np.arccos(np.clip(np.dot(lattice[0], lattice[1]) / (a * b), -1, 1)))
    return a, b, c, alpha, beta, gamma


def calc_volume(lattice):
    """Calculate cell volume."""
    return abs(np.dot(lattice[0], np.cross(lattice[1], lattice[2])))


# ---------- Advanced Analysis Functions (p4vasp-like) ----------

def read_outcar(filename="OUTCAR"):
    """Parse VASP OUTCAR file for energy and force data."""
    if not os.path.exists(filename):
        return None
    
    data = {
        'energies': [],
        'max_forces': [],
        'avg_forces': [],
        'steps': []
    }
    
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            # Extract total energy
            if 'free  energy' in line.lower() and '=' in line:
                try:
                    energy = float(line.split()[-2])
                    data['energies'].append(energy)
                except:
                    pass
            
            # Extract forces
            if 'total drift' in line.lower():
                try:
                    parts = line.split()
                    force = float(parts[-1])
                    data['max_forces'].append(force)
                except:
                    pass
        
        data['steps'] = list(range(len(data['energies'])))
        return data if data['energies'] else None
    except:
        return None


def read_doscar(filename="DOSCAR"):
    """Parse VASP DOSCAR file for density of states."""
    if not os.path.exists(filename):
        return None
    
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        # Header information
        header = lines[0].split()
        n_atoms = int(header[0])
        
        # Parse DOS data
        dos_data = []
        reading_dos = False
        fermi_level = 0.0
        
        for i, line in enumerate(lines):
            if i >= 5:  # Skip header
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        e = float(parts[0])
                        dos_total = float(parts[1])
                        dos_data.append((e, dos_total))
                    except:
                        pass
        
        return {
            'energies': [d[0] for d in dos_data],
            'dos': [d[1] for d in dos_data],
            'n_atoms': n_atoms
        } if dos_data else None
    except:
        return None


def read_procar(filename="PROCAR"):
    """Parse PROCAR file for band structure and projections."""
    if not os.path.exists(filename):
        return None
    
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        # Extract basic info from header
        header = lines[0].split()
        data = {
            'n_kpoints': 0,
            'n_bands': 0,
            'n_ions': 0,
            'bands': [],
            'kpoints': []
        }
        
        # Look for structure info
        for line in lines:
            if 'Nkpoints' in line and 'Nband' in line:
                try:
                    parts = line.split('=')
                    data['n_kpoints'] = int(parts[1].split()[0])
                    data['n_bands'] = int(parts[2].split()[0])
                    data['n_ions'] = int(parts[3].split()[0])
                except:
                    pass
        
        return data if data['bands'] else None
    except:
        return None


def calc_distances(structure):
    """Calculate atomic distances and nearest neighbors."""
    cart_pos = get_cartesian_positions(structure)
    atoms = get_atom_list(structure)
    
    distances = {}
    for i in range(len(cart_pos)):
        distances[i] = []
        for j in range(len(cart_pos)):
            if i != j:
                dist = np.linalg.norm(cart_pos[i] - cart_pos[j])
                distances[i].append({
                    'index': j,
                    'element': atoms[j],
                    'distance': dist
                })
        # Sort by distance
        distances[i].sort(key=lambda x: x['distance'])
    
    return distances


def calc_interplanar_spacing(structure, miller_indices):
    """Calculate d-spacing for given Miller indices."""
    h, k, l = miller_indices
    a, b, c, _, _, _ = calc_lattice_params(structure['lattice'])
    
    # Cubic approximation (can be improved for other systems)
    try:
        d_spacing = 1.0 / np.sqrt((h/a)**2 + (k/b)**2 + (l/c)**2)
        return d_spacing
    except:
        return None


def calc_coordination(structure, cutoff=3.5):
    """Calculate coordination numbers based on cutoff distance."""
    cart_pos = get_cartesian_positions(structure)
    atoms = get_atom_list(structure)
    
    coordination = {}
    for i, atom in enumerate(atoms):
        coordination[i] = {'element': atom, 'neighbors': []}
        
        for j in range(len(cart_pos)):
            if i != j:
                dist = np.linalg.norm(cart_pos[i] - cart_pos[j])
                if dist < cutoff:
                    coordination[i]['neighbors'].append({
                        'index': j,
                        'element': atoms[j],
                        'distance': dist
                    })
    
    return coordination


def analyze_structure(structure):
    """Comprehensive structure analysis."""
    analysis = {
        'lattice_params': dict(zip(['a', 'b', 'c', 'alpha', 'beta', 'gamma'], 
                                    calc_lattice_params(structure['lattice']))),
        'volume': calc_volume(structure['lattice']),
        'density': structure['total_atoms'] / calc_volume(structure['lattice']),
        'elements': structure['elements'],
        'counts': structure['counts'],
        'symmetry': 'Unknown',  # Would need spglib for real symmetry
        'coordination': calc_coordination(structure)
    }
    return analysis


# ---------- Command-line mode functions ----------
def print_structure_info(structure, verbose=False):
    """Print structure information in a formatted way."""
    print("=" * 60)
    print(f"Comment: {structure['comment']}")
    print("=" * 60)
    
    a, b, c, alpha, beta, gamma = calc_lattice_params(structure['lattice'])
    volume = calc_volume(structure['lattice'])
    
    print("\n[Lattice Parameters]")
    print(f"  a = {a:.6f} Å")
    print(f"  b = {b:.6f} Å")
    print(f"  c = {c:.6f} Å")
    print(f"  α = {alpha:.4f}°")
    print(f"  β = {beta:.4f}°")
    print(f"  γ = {gamma:.4f}°")
    print(f"  Volume = {volume:.4f} Å³")
    
    print("\n[Lattice Vectors (Å)]")
    for i, vec in enumerate(structure['lattice']):
        print(f"  a{i+1} = [{vec[0]:12.6f}, {vec[1]:12.6f}, {vec[2]:12.6f}]")
    
    print("\n[Composition]")
    if structure['elements']:
        composition = "".join([f"{e}{c}" for e, c in zip(structure['elements'], structure['counts'])])
        print(f"  Formula: {composition}")
    print(f"  Total atoms: {structure['total_atoms']}")
    
    if structure['elements']:
        print("\n  Element  Count")
        print("  -------  -----")
        for elem, count in zip(structure['elements'], structure['counts']):
            print(f"  {elem:^7}  {count:^5}")
    
    print(f"\n[Coordinates]")
    print(f"  Type: {structure['coord_type']}")
    print(f"  Selective Dynamics: {'Yes' if structure['selective'] else 'No'}")
    
    if verbose:
        print("\n[Atomic Positions]")
        atoms = get_atom_list(structure)
        cart_pos = get_cartesian_positions(structure)
        
        print("  Index  Element      x(Å)        y(Å)        z(Å)     Constraints")
        print("  -----  -------  ----------  ----------  ----------  -----------")
        
        for i, (atom, pos) in enumerate(zip(atoms, cart_pos)):
            constraint_str = ""
            if structure['selective'] and structure['constraints']:
                constraint_str = " ".join(structure['constraints'][i])
            print(f"  {i:5d}  {atom:^7}  {pos[0]:10.6f}  {pos[1]:10.6f}  {pos[2]:10.6f}  {constraint_str}")
    
    print("\n" + "=" * 60)


def main_cli():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="POSCAR Viewer for VASP calculations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  geo_gui.py POSCAR            # View structure info
  geo_gui.py CONTCAR -v        # Verbose mode with atom positions
  streamlit run geo_gui.py     # Launch GUI mode
        """
    )
    parser.add_argument('file', nargs='?', default='POSCAR',
                        help='POSCAR file to read (default: POSCAR)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show detailed atomic positions')
    
    args = parser.parse_args()
    
    try:
        structure = read_poscar(args.file)
        print_structure_info(structure, verbose=args.verbose)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)


# ---------- Streamlit GUI mode ----------
def run_streamlit_app():
    """Run the Streamlit GUI application."""
    import streamlit as st
    
    try:
        import py3Dmol
    except ImportError:
        st.error("py3Dmol not installed. Run: pip install py3Dmol")
        st.stop()
    
    st.set_page_config(page_title="GEO GUI - VASP Structure Analyzer", layout="wide", initial_sidebar_state="collapsed")
    st.title("GEO GUI")
    st.markdown("*VASP Structure Analyzer - Compact Single-Page Interface*")
    
    # ---------- Color & Atom Selection Utilities ----------
    def get_element_colors():
        """Jmol color scheme for elements (ASE standard)."""
        return {
            'H': '#FFFFFF', 'C': '#909090', 'N': '#4C4CFF', 'O': '#FF0D0D',
            'F': '#90E050', 'P': '#FF8000', 'S': '#FFFF30', 'Cl': '#1FF01F',
            'Br': '#A62929', 'I': '#940094', 'Ca': '#3DFF00', 'Fe': '#FF6600',
            'Cu': '#C88033', 'Zn': '#7D80B0', 'Ag': '#C0C0C0', 'Au': '#FFD700',
            'Pt': '#E6E6FA', 'Pd': '#F0F0F0', 'Ni': '#C1C1C1', 'Co': '#EE82EE',
            'Ru': '#24B9B9', 'Rh': '#F0F0F0', 'Mo': '#54B5B5', 'W': '#191970',
            # Extended Jmol colors for more elements
            'He': '#D9FFFF', 'Li': '#CC80FF', 'Be': '#C2FF00', 'B': '#FFB5B5',
            'Ne': '#B3E3FF', 'Na': '#AB5CF2', 'Mg': '#FF92FF', 'Al': '#C8A2C8',
            'Si': '#F0C8A0', 'K': '#8F40D4', 'Ca': '#3DFF00', 'Sc': '#E6E6E6',
            'Ti': '#BFC2C7', 'V': '#A6A6AB', 'Cr': '#8A99C7', 'Mn': '#9C7AC7',
            'Ni': '#C1C1C1', 'Zn': '#A67573', 'Ga': '#C78033', 'Ge': '#8F8F8F',
            'As': '#BD80E3', 'Se': '#FFA100', 'Br': '#A62929', 'Kr': '#5CB8D1',
            'Rb': '#702EB0', 'Sr': '#00FF00', 'Y': '#94FFFF', 'Zr': '#94E0E0',
            'Nb': '#73C2C9', 'Mo': '#54B5B5', 'Tc': '#3B9E98', 'Ru': '#248F8F',
            'Rh': '#0A7D8C', 'Pd': '#7CA8A8', 'Ag': '#C0C0C0', 'Cd': '#FFD98F',
            'In': '#A6DBDB', 'Sn': '#668080', 'Sb': '#9E63B5', 'Te': '#D47A00',
            'I': '#940094', 'Xe': '#429EB0', 'Cs': '#57178F', 'Ba': '#00C900',
            'La': '#70D4FF', 'Ce': '#FFFFC7', 'Pr': '#D9FFC7', 'Nd': '#C7FFC7',
            'Pm': '#A3FFC7', 'Sm': '#8FFFC7', 'Eu': '#61FFC7', 'Gd': '#45FFC7',
            'Tb': '#30FFC7', 'Dy': '#1FFFC7', 'Ho': '#00FF9C', 'Er': '#00E675',
            'Tm': '#00D452', 'Yb': '#00BF38', 'Lu': '#00AB24', 'Hf': '#4DC2FF',
            'Ta': '#4DA6FF', 'W': '#2194D6', 'Re': '#267DAB', 'Os': '#266696',
            'Ir': '#175487', 'Pt': '#D0D0E8', 'Au': '#FFD123', 'Hg': '#B8B8D0',
            'Tl': '#A6544D', 'Pb': '#575961', 'Bi': '#9E4FB5', 'Po': '#AB5C00',
            'At': '#754F45', 'Rn': '#428296', 'Fr': '#420066', 'Ra': '#007D00',
        }
    
    def get_color_scheme(scheme_name="jmol"):
        """Get color scheme for atoms. Jmol is the default ASE standard."""
        if scheme_name == "jmol":
            # Default: Jmol/ASE standard colors
            return get_element_colors()
        elif scheme_name == "cpk":
            # Alternative: CPK (Corey-Pauling-Koltun) classic colors
            return {
                'H': '#FFFFFF', 'C': '#909090', 'N': '#3050F8', 'O': '#FF0D0D',
                'F': '#90E050', 'P': '#FF8000', 'S': '#FFFF30', 'Cl': '#1FF01F',
                'Br': '#A62929', 'I': '#940094', 'Ca': '#3DFF00', 'Fe': '#FF6600',
                'Cu': '#C88033', 'Zn': '#7D80B0', 'Ag': '#C0C0C0', 'Au': '#FFD700',
                'Pt': '#E6E6FA', 'Pd': '#F0F0F0', 'Ni': '#C1C1C1', 'Co': '#EE82EE',
                'Ru': '#24B9B9', 'Rh': '#F0F0F0', 'Mo': '#54B5B5', 'W': '#191970',
            }
        else:  # default to jmol
            return get_element_colors()
    
    def apply_color_scheme(view, structure, color_scheme, custom_colors=None):
        """Apply color scheme to 3D viewer."""
        atoms = get_atom_list(structure)
        colors = get_color_scheme(color_scheme)
        
        if custom_colors:
            colors.update(custom_colors)
        
        for atom in set(atoms):
            color = colors.get(atom, '#CCCCCC')  # Default gray
            view.setStyle({"elem": atom}, {"sphere": {"colorscheme": "Jmol"}} if not custom_colors else {"sphere": {"color": color}})
        
        return view
    
    # ---------- 3D Viewer ----------
    def structure_to_xyz(structure):
        """Convert structure to XYZ format string."""
        atoms = get_atom_list(structure)
        cart_pos = get_cartesian_positions(structure)
        
        lines = [str(structure['total_atoms']), structure['comment']]
        for atom, pos in zip(atoms, cart_pos):
            lines.append(f"{atom}  {pos[0]:.6f}  {pos[1]:.6f}  {pos[2]:.6f}")
        return '\n'.join(lines)
    
    def show_viewer_interactive(structure, style="ballstick", show_unitcell=True, hidden_elements=None, color_scheme="jmol", custom_colors=None, selected_atoms=None):
        """Create interactive 3D viewer with atom highlighting."""
        hidden_elements = hidden_elements or set()
        selected_atoms = selected_atoms or []
        xyz = structure_to_xyz(structure)
        atoms = get_atom_list(structure)
        cart_pos = get_cartesian_positions(structure)
        
        # Create viewer
        view = py3Dmol.view(width=800, height=500)
        view.addModel(xyz, "xyz")
        
        # Apply style
        if style == "stick":
            view.setStyle({"sphere": {"scale": 0.25}, "stick": {"radius": 0.15}})
        elif style == "ballstick":
            view.setStyle({"sphere": {"scale": 0.35}, "stick": {"radius": 0.12}})
        elif style == "vdw":
            view.setStyle({"sphere": {"scale": 1.0}})
        else:
            view.setStyle({"stick": {}})
        
        # Apply colors
        colors = get_color_scheme(color_scheme)
        if custom_colors:
            colors.update(custom_colors)
        
        for atom in set(atoms):
            color = colors.get(atom, '#CCCCCC')
            view.setStyle({"elem": atom}, {"sphere": {"color": color}})
        
        # Highlight selected atoms in yellow
        if selected_atoms:
            for idx in selected_atoms:
                if 0 <= idx < len(atoms):
                    view.setStyle({"index": idx}, {"sphere": {"color": "yellow", "scale": 0.5}})
        
        # Add atom labels (index and element) for easier identification
        for idx, atom in enumerate(atoms):
            pos = cart_pos[idx]
            view.addLabel(f"{idx}", {
                "position": {"x": pos[0], "y": pos[1], "z": pos[2]},
                "fontColor": "white",
                "fontSize": 12,
                "showBackground": True,
                "backgroundColor": "black",
                "backgroundOpacity": 0.8
            })
        
        # Hide elements
        for el in hidden_elements:
            view.setStyle({"elem": el}, {"sphere": {"scale": 0}, "stick": {"radius": 0}})
        
        # Draw unit cell
        if show_unitcell:
            cell = structure['lattice']
            corners = np.array([
                [0, 0, 0],
                cell[0],
                cell[1],
                cell[2],
                cell[0] + cell[1],
                cell[0] + cell[2],
                cell[1] + cell[2],
                cell[0] + cell[1] + cell[2]
            ])
            edges = [
                (0, 1), (0, 2), (0, 3),
                (1, 4), (1, 5),
                (2, 4), (2, 6),
                (3, 5), (3, 6),
                (4, 7), (5, 7), (6, 7)
            ]
            for i, j in edges:
                a, b = corners[i], corners[j]
                view.addLine({
                    "start": {"x": float(a[0]), "y": float(a[1]), "z": float(a[2])},
                    "end": {"x": float(b[0]), "y": float(b[1]), "z": float(b[2])},
                    "color": "gray",
                    "linewidth": 2
                })
        
        view.zoomTo()
        return view
    
    def show_viewer(structure, style="ballstick", show_unitcell=True, hidden_elements=None):
        """Create 3D viewer (legacy version)."""
        hidden_elements = hidden_elements or set()
        xyz = structure_to_xyz(structure)
        
        view = py3Dmol.view(width=800, height=600)
        view.addModel(xyz, "xyz")
        
        if style == "stick":
            view.setStyle({"sphere": {"scale": 0.25}, "stick": {"radius": 0.15}})
        elif style == "ballstick":
            view.setStyle({"sphere": {"scale": 0.35}, "stick": {"radius": 0.12}})
        elif style == "vdw":
            view.setStyle({"sphere": {"scale": 1.0}})
        else:
            view.setStyle({"stick": {}})
        
        for el in hidden_elements:
            view.setStyle({"elem": el}, {})
        
        if show_unitcell:
            cell = structure['lattice']
            corners = np.array([
                [0, 0, 0],
                cell[0],
                cell[1],
                cell[2],
                cell[0] + cell[1],
                cell[0] + cell[2],
                cell[1] + cell[2],
                cell[0] + cell[1] + cell[2]
            ])
            edges = [
                (0, 1), (0, 2), (0, 3),
                (1, 4), (1, 5),
                (2, 4), (2, 6),
                (3, 5), (3, 6),
                (4, 7), (5, 7), (6, 7)
            ]
            for i, j in edges:
                a, b = corners[i], corners[j]
                view.addLine({
                    "start": {"x": float(a[0]), "y": float(a[1]), "z": float(a[2])},
                    "end": {"x": float(b[0]), "y": float(b[1]), "z": float(b[2])},
                    "color": "gray",
                    "linewidth": 2
                })
        
        view.zoomTo()
        return view
    
    # ---------- Session State ----------
    if "structure" not in st.session_state:
        st.session_state.structure = None
    if "selected_atoms" not in st.session_state:
        st.session_state.selected_atoms = set()
    if "custom_colors" not in st.session_state:
        st.session_state.custom_colors = {}
    
    # ---------- Layout ----------
    # Top row: Load controls
    col_load1, col_load2, col_style1, col_style2 = st.columns([2, 2, 1.2, 1.2])
    
    with col_load1:
        up = st.file_uploader("📂 Upload POSCAR", type=None, label_visibility="collapsed")
        if up is not None:
            content = up.read().decode('utf-8')
            with open("/tmp/temp_poscar", 'w') as f:
                f.write(content)
            try:
                structure = read_poscar("/tmp/temp_poscar")
                st.session_state.structure = structure
                st.success(f"✓ {structure['total_atoms']} atoms")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col_load2:
        filepath = st.text_input("📁 Path", value="POSCAR", label_visibility="collapsed")
        if st.button("Load", use_container_width=True):
            try:
                structure = read_poscar(filepath)
                st.session_state.structure = structure
                st.success(f"✓ {structure['total_atoms']} atoms")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col_style1:
        style = st.selectbox("Style", ["ballstick", "stick", "vdw"], label_visibility="collapsed")
    
    with col_style2:
        show_cell = st.checkbox("Cell", value=True, label_visibility="collapsed")
    
    # Main content area
    if st.session_state.structure is None:
        st.info("👈 Upload or load a POSCAR file to start")
    else:
        structure = st.session_state.structure
        
        # Create 3-column layout for compact display
        col_viewer, col_info, col_tools = st.columns([2, 1.2, 1.3], gap="small")
        
        # Column 1: 3D Viewer
        with col_viewer:
            st.subheader("3D Structure", divider=False)
            hidden_elements = set()
            if structure['elements']:
                elems = sorted(set(structure['elements']))
                hide = st.multiselect("Hide:", elems, default=[], label_visibility="collapsed", key="hide_elems")
                hidden_elements = set(hide)
            
            # Color customization section
            st.markdown("**🎨 Colors**")
            color_cols = st.columns(2)
            with color_cols[0]:
                color_scheme = st.selectbox("Scheme", ["jmol", "cpk", "custom"], label_visibility="collapsed", key="color_scheme")
            with color_cols[1]:
                if st.button("Reset Colors", use_container_width=True, key="reset_colors"):
                    st.session_state.custom_colors = {}
                    st.rerun()
            
            # Custom color picker for each element
            if color_scheme == "custom" and structure['elements']:
                st.markdown("*Pick colors for elements*")
                color_cols_list = st.columns(3)
                for idx, elem in enumerate(structure['elements']):
                    with color_cols_list[idx % 3]:
                        custom_color = st.color_picker(
                            f"{elem}",
                            value=st.session_state.custom_colors.get(elem, "#808080"),
                            label_visibility="collapsed",
                            key=f"color_{elem}"
                        )
                        st.session_state.custom_colors[elem] = custom_color
            
            # Atom selection section
            st.markdown("**🎯 Select Atoms**")
            st.info("💡 **How to select atoms:** Look at the atom numbers in the 3D viewer above, then use the selection controls below to pick atoms by their index.")
            atoms = get_atom_list(structure)
            
            sel_cols = st.columns(3)
            with sel_cols[0]:
                select_mode = st.radio("Mode", ["Single", "Multiple"], horizontal=True, label_visibility="collapsed")
            
            if select_mode == "Single":
                atom_idx = st.slider("Atom Index", 0, structure['total_atoms']-1, 0, label_visibility="collapsed")
                selected_atoms_list = [atom_idx]
                st.info(f"Selected: Atom {atom_idx} ({atoms[atom_idx]})")
            else:
                selected_atoms_list = st.multiselect(
                    "Select atoms",
                    range(structure['total_atoms']),
                    format_func=lambda i: f"{i}: {atoms[i]}",
                    label_visibility="collapsed"
                )
                if selected_atoms_list:
                    st.info(f"Selected {len(selected_atoms_list)} atoms: {selected_atoms_list[:5]}{'...' if len(selected_atoms_list) > 5 else ''}")
            
            # Display viewer with selected atoms highlighted
            view = show_viewer_interactive(
                structure, 
                style=style, 
                show_unitcell=show_cell, 
                hidden_elements=hidden_elements,
                color_scheme=color_scheme,
                custom_colors=st.session_state.custom_colors if color_scheme == "custom" else None,
                selected_atoms=selected_atoms_list
            )
            st.components.v1.html(view._make_html(), height=500, scrolling=False)
            
            # Display selected atoms info
            if selected_atoms_list:
                st.markdown("**📋 Selected Atoms Info**")
                cart_pos = get_cartesian_positions(structure)
                for idx in selected_atoms_list[:10]:  # Show first 10
                    x, y, z = cart_pos[idx]
                    st.text(f"  Atom {idx:3d} ({atoms[idx]:2s}): x={x:9.5f}  y={y:9.5f}  z={z:9.5f} Å")
                if len(selected_atoms_list) > 10:
                    st.text(f"  ... and {len(selected_atoms_list)-10} more atoms")
        
        # Column 2: Structure Information
        with col_info:
            st.subheader("Info", divider=False)
            a, b, c, alpha, beta, gamma = calc_lattice_params(structure['lattice'])
            vol = calc_volume(structure['lattice'])
            
            st.metric("Atoms", structure['total_atoms'], label_visibility="collapsed")
            st.metric("Volume", f"{vol:.1f} Ų", label_visibility="collapsed")
            
            if structure['elements']:
                formula = "".join([f"{e}{c}" for e, c in zip(structure['elements'], structure['counts'])])
                st.markdown(f"**Formula:** {formula}")
            
            st.markdown("**Lattice (Å)**")
            st.text(f"a={a:.3f} b={b:.3f}\nc={c:.3f}\nα={alpha:.1f}° β={beta:.1f}°")
            
            st.markdown("**Angles**")
            st.text(f"γ={gamma:.1f}°")
            
            # Coordination
            try:
                coord = calc_coordination(structure, 3.8)
                n_neighbors = sum(len(c['neighbors']) for c in coord.values()) // 2
                st.metric("Avg Neighbors", f"{n_neighbors // structure['total_atoms']}", label_visibility="collapsed")
            except:
                pass
        
        # Column 3: Tools (Compact expanders)
        with col_tools:
            st.subheader("Tools", divider=False)
            
            with st.expander("✏️ Edit", expanded=False):
                edit_choice = st.radio("Operation", ["Translate", "Scale", "Delete", "Fix Z", "Center", "Convert"], label_visibility="collapsed", horizontal=False)
                
                if edit_choice == "Translate":
                    col_t1, col_t2, col_t3 = st.columns(3)
                    with col_t1:
                        dx = st.number_input("dx", value=0.0, format="%.3f")
                    with col_t2:
                        dy = st.number_input("dy", value=0.0, format="%.3f")
                    with col_t3:
                        dz = st.number_input("dz", value=0.0, format="%.3f")
                    
                    if st.button("Apply", use_container_width=True):
                        cart_pos = get_cartesian_positions(structure)
                        if selected_atoms_list:
                            # Translate only selected atoms
                            for idx in selected_atoms_list:
                                cart_pos[idx] += np.array([dx, dy, dz])
                        else:
                            # Translate all atoms
                            cart_pos += np.array([dx, dy, dz])
                        
                        if structure['coord_type'] == 'Direct':
                            structure['positions'] = cart_pos @ np.linalg.inv(structure['lattice'])
                        else:
                            structure['positions'] = cart_pos
                        st.session_state.structure = structure
                        if selected_atoms_list:
                            st.success(f"✓ Translated {len(selected_atoms_list)} atoms")
                        else:
                            st.success("✓ Translated all atoms")
                        st.rerun()
                
                elif edit_choice == "Scale":
                    scale = st.number_input("Factor", value=1.0, min_value=0.1, format="%.3f")
                    if st.button("Apply", use_container_width=True):
                        structure['lattice'] *= scale
                        st.session_state.structure = structure
                        st.success("✓ Scaled")
                        st.rerun()
                
                elif edit_choice == "Delete":
                    if selected_atoms_list:
                        st.warning(f"Delete {len(selected_atoms_list)} selected atoms? This cannot be undone!")
                        if st.button("⚠️ Confirm Delete", use_container_width=True, key="delete_selected"):
                            atoms = get_atom_list(structure)
                            # Delete in reverse order to maintain indices
                            for del_idx in sorted(selected_atoms_list, reverse=True):
                                elem = atoms[del_idx]
                                structure['positions'] = np.delete(structure['positions'], del_idx, axis=0)
                                if structure['constraints']:
                                    structure['constraints'].pop(del_idx)
                                elem_idx = structure['elements'].index(elem)
                                structure['counts'][elem_idx] -= 1
                                if structure['counts'][elem_idx] == 0:
                                    structure['elements'].pop(elem_idx)
                                    structure['counts'].pop(elem_idx)
                                structure['total_atoms'] -= 1
                                atoms = get_atom_list(structure)
                            st.session_state.structure = structure
                            st.success(f"✓ Deleted {len(selected_atoms_list)} atoms")
                            st.rerun()
                    else:
                        st.info("Select atoms first using the selector above")
                
                elif edit_choice == "Fix Z":
                    z_thresh = st.number_input("Z threshold", value=5.0, format="%.2f")
                    fix_mode = st.radio("Fix:", ["below", "above"], label_visibility="collapsed", horizontal=True)
                    if st.button("Apply", use_container_width=True):
                        structure['selective'] = True
                        cart_pos = get_cartesian_positions(structure)
                        constraints = []
                        for i, pos in enumerate(cart_pos):
                            if (fix_mode == "below" and pos[2] < z_thresh) or (fix_mode == "above" and pos[2] > z_thresh):
                                constraints.append(['F', 'F', 'F'])
                            else:
                                constraints.append(['T', 'T', 'T'])
                        structure['constraints'] = constraints
                        st.session_state.structure = structure
                        st.success(f"✓ Fixed atoms")
                        st.rerun()
                
                elif edit_choice == "Center":
                    axes = st.multiselect("Axes", ["x", "y", "z"], default=["z"], label_visibility="collapsed")
                    if st.button("Apply", use_container_width=True):
                        cart_pos = get_cartesian_positions(structure)
                        cell_center = np.sum(structure['lattice'], axis=0) / 2
                        atom_center = np.mean(cart_pos, axis=0)
                        shift = np.zeros(3)
                        if "x" in axes:
                            shift[0] = cell_center[0] - atom_center[0]
                        if "y" in axes:
                            shift[1] = cell_center[1] - atom_center[1]
                        if "z" in axes:
                            shift[2] = cell_center[2] - atom_center[2]
                        cart_pos += shift
                        if structure['coord_type'] == 'Direct':
                            structure['positions'] = cart_pos @ np.linalg.inv(structure['lattice'])
                        else:
                            structure['positions'] = cart_pos
                        st.session_state.structure = structure
                        st.success("✓ Centered")
                        st.rerun()
                
                elif edit_choice == "Convert":
                    current = structure['coord_type']
                    target = "Cartesian" if current == "Direct" else "Direct"
                    st.write(f"Convert {current} → {target}")
                    if st.button("Apply", use_container_width=True):
                        if target == "Cartesian":
                            structure['positions'] = get_cartesian_positions(structure)
                        else:
                            structure['positions'] = get_fractional_positions(structure)
                        structure['coord_type'] = target
                        st.session_state.structure = structure
                        st.success("✓ Converted")
                        st.rerun()
            
            with st.expander("📊 Analyze", expanded=False):
                analyze_choice = st.radio("Type", ["Structure", "Neighbors", "DOS"], label_visibility="collapsed")
                
                if analyze_choice == "Structure":
                    analysis = analyze_structure(structure)
                    lp = analysis['lattice_params']
                    st.text(f"Density: {analysis['density']:.5f}")
                    st.text(f"a={lp['a']:.3f} b={lp['b']:.3f}")
                    st.text(f"c={lp['c']:.3f}")
                
                elif analyze_choice == "Neighbors":
                    atom_idx = st.number_input("Atom", min_value=0, max_value=structure['total_atoms']-1)
                    cutoff = st.slider("Cutoff (Å)", 1.0, 10.0, 3.8, 0.1)
                    if st.button("Calculate", use_container_width=True):
                        coord = calc_coordination(structure, cutoff)
                        neighbors = coord[atom_idx]['neighbors']
                        st.write(f"**{len(neighbors)} neighbors**")
                        for i, nb in enumerate(neighbors[:5]):
                            st.text(f"{i+1}. Atom {nb['index']} ({nb['element']}) - {nb['distance']:.3f} Å")
                        if len(neighbors) > 5:
                            st.text(f"... +{len(neighbors)-5} more")
                
                elif analyze_choice == "DOS":
                    if st.button("Load DOSCAR", use_container_width=True):
                        dos = read_doscar()
                        if dos:
                            st.success(f"✓ {len(dos['energies'])} points")
                        else:
                            st.info("DOSCAR not found")
            
            with st.expander("💾 Export", expanded=False):
                poscar_str = write_poscar(structure, "/tmp/POSCAR_export")
                st.download_button("📥 POSCAR", data=poscar_str, file_name="POSCAR_edited", use_container_width=True)
                
                save_path = st.text_input("Path", value="POSCAR_new", label_visibility="collapsed")
                if st.button("💿 Save", use_container_width=True):
                    write_poscar(structure, save_path)
                    st.success(f"✓ Saved")
        
        # Bottom: Atomic positions table
        st.divider()
        st.subheader("Atomic Positions", divider=False)
        
        with st.expander("View Atoms", expanded=True):
            atoms = get_atom_list(structure)
            cart_pos = get_cartesian_positions(structure)
            frac_pos = get_fractional_positions(structure)
            
            data = []
            for i, (atom, cart, frac) in enumerate(zip(atoms, cart_pos, frac_pos)):
                constraint = ""
                if structure['selective'] and structure['constraints']:
                    constraint = " ".join(structure['constraints'][i])
                data.append({
                    "i": i,
                    "E": atom,
                    "x(Å)": f"{cart[0]:.4f}",
                    "y(Å)": f"{cart[1]:.4f}",
                    "z(Å)": f"{cart[2]:.4f}",
                    "Fx": f"{frac[0]:.4f}",
                    "Fy": f"{frac[1]:.4f}",
                    "Fz": f"{frac[2]:.4f}",
                })
            
            st.dataframe(data, use_container_width=True, height=200)


# ---------- Main Entry Point ----------
# When using streamlit, it will directly call the script without __name__ check
if STREAMLIT_MODE:
    run_streamlit_app()
elif __name__ == "__main__":
    main_cli()
