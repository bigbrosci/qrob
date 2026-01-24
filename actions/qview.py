#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POSCAR Viewer and Editor for VASP calculations.

Usage (Command-line mode): 
    python qview.py POSCAR           # View structure info
    python qview.py -v POSCAR        # Verbose mode with atom positions

Usage (GUI mode):
    streamlit run qview.py
"""

import sys
import os
import argparse
import numpy as np

# Check if running in Streamlit mode
STREAMLIT_MODE = False
try:
    import streamlit as st
    # Check if actually running under streamlit
    if hasattr(st, 'session_state'):
        try:
            # This will work only when running under streamlit
            _ = st.session_state
            STREAMLIT_MODE = True
        except:
            pass
except ImportError:
    pass

# Only import GUI dependencies if in streamlit mode
if STREAMLIT_MODE:
    try:
        import py3Dmol
    except ImportError:
        st.error("py3Dmol not installed. Run: pip install py3Dmol")
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
  qview.py POSCAR              # View structure info
  qview.py CONTCAR -v          # Verbose mode with atom positions
  streamlit run qview.py       # Launch GUI mode
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
    import py3Dmol
    
    st.set_page_config(page_title="POSCAR Viewer & Editor", layout="wide")
    st.title("POSCAR Viewer & Editor")
    
    # ---------- 3D Viewer ----------
    def structure_to_xyz(structure):
        """Convert structure to XYZ format string."""
        atoms = get_atom_list(structure)
        cart_pos = get_cartesian_positions(structure)
        
        lines = [str(structure['total_atoms']), structure['comment']]
        for atom, pos in zip(atoms, cart_pos):
            lines.append(f"{atom}  {pos[0]:.6f}  {pos[1]:.6f}  {pos[2]:.6f}")
        return '\n'.join(lines)
    
    def show_viewer(structure, style="ballstick", show_unitcell=True, hidden_elements=None):
        """Create 3D viewer."""
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
    
    # ---------- Layout ----------
    left, right = st.columns([1, 2], gap="large")
    
    with left:
        st.subheader("📂 Load Structure")
        
        up = st.file_uploader("Upload POSCAR/CONTCAR", type=None)
        if up is not None:
            content = up.read().decode('utf-8')
            with open("/tmp/temp_poscar", 'w') as f:
                f.write(content)
            try:
                structure = read_poscar("/tmp/temp_poscar")
                st.session_state.structure = structure
                st.success(f"Loaded: {structure['total_atoms']} atoms")
            except Exception as e:
                st.error(f"Error: {e}")
        
        with st.expander("Load from path"):
            filepath = st.text_input("File path", value="POSCAR")
            if st.button("Load"):
                try:
                    structure = read_poscar(filepath)
                    st.session_state.structure = structure
                    st.success(f"Loaded: {structure['total_atoms']} atoms")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        st.divider()
        
        if st.session_state.structure:
            structure = st.session_state.structure
            st.subheader("📊 Structure Info")
            
            a, b, c, alpha, beta, gamma = calc_lattice_params(structure['lattice'])
            vol = calc_volume(structure['lattice'])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Atoms", structure['total_atoms'])
                st.metric("Volume", f"{vol:.2f} Å³")
            with col2:
                if structure['elements']:
                    formula = "".join([f"{e}{c}" for e, c in zip(structure['elements'], structure['counts'])])
                    st.metric("Formula", formula)
            
            with st.expander("Lattice Parameters"):
                st.write(f"a = {a:.4f} Å, b = {b:.4f} Å, c = {c:.4f} Å")
                st.write(f"α = {alpha:.2f}°, β = {beta:.2f}°, γ = {gamma:.2f}°")
        
        st.divider()
        
        st.subheader("🎨 Display Settings")
        style = st.selectbox("Style", ["ballstick", "stick", "vdw"])
        show_cell = st.checkbox("Show unit cell", value=True)
        
        hidden_elements = set()
        if st.session_state.structure and st.session_state.structure['elements']:
            elems = sorted(set(st.session_state.structure['elements']))
            hide = st.multiselect("Hide elements", elems, default=[])
            hidden_elements = set(hide)
        
        st.divider()
        
        st.subheader("🔧 Edit Tools")
        
        if st.session_state.structure is None:
            st.info("Load a structure first.")
        else:
            structure = st.session_state.structure
            
            with st.expander("🔀 Translate All Atoms"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    dx = st.number_input("dx (Å)", value=0.0, format="%.4f", key="dx")
                with col2:
                    dy = st.number_input("dy (Å)", value=0.0, format="%.4f", key="dy")
                with col3:
                    dz = st.number_input("dz (Å)", value=0.0, format="%.4f", key="dz")
                
                if st.button("Apply Translation"):
                    cart_pos = get_cartesian_positions(structure)
                    cart_pos += np.array([dx, dy, dz])
                    if structure['coord_type'] == 'Direct':
                        structure['positions'] = cart_pos @ np.linalg.inv(structure['lattice'])
                    else:
                        structure['positions'] = cart_pos
                    st.session_state.structure = structure
                    st.success("Translated!")
                    st.rerun()
            
            with st.expander("📐 Scale Lattice"):
                scale_factor = st.number_input("Scale factor", value=1.0, min_value=0.1, format="%.4f")
                if st.button("Apply Scale"):
                    structure['lattice'] *= scale_factor
                    st.session_state.structure = structure
                    st.success(f"Scaled by {scale_factor}")
                    st.rerun()
            
            with st.expander("❌ Delete Atom"):
                max_idx = structure['total_atoms'] - 1
                del_idx = st.number_input("Atom index (0-based)", min_value=0, max_value=max_idx, value=0, step=1)
                if st.button("Delete Atom"):
                    atoms = get_atom_list(structure)
                    elem_to_delete = atoms[del_idx]
                    
                    structure['positions'] = np.delete(structure['positions'], del_idx, axis=0)
                    if structure['constraints']:
                        structure['constraints'].pop(del_idx)
                    
                    elem_idx = structure['elements'].index(elem_to_delete)
                    structure['counts'][elem_idx] -= 1
                    
                    if structure['counts'][elem_idx] == 0:
                        structure['elements'].pop(elem_idx)
                        structure['counts'].pop(elem_idx)
                    
                    structure['total_atoms'] -= 1
                    st.session_state.structure = structure
                    st.success(f"Deleted atom {del_idx}")
                    st.rerun()
            
            with st.expander("🔒 Fix Atoms by Z"):
                z_threshold = st.number_input("Z threshold (Å)", value=5.0, format="%.4f")
                fix_mode = st.radio("Fix atoms with z", ["below threshold", "above threshold"])
                
                if st.button("Apply Constraints"):
                    structure['selective'] = True
                    cart_pos = get_cartesian_positions(structure)
                    constraints = []
                    
                    for i, pos in enumerate(cart_pos):
                        if (fix_mode == "below threshold" and pos[2] < z_threshold) or \
                           (fix_mode == "above threshold" and pos[2] > z_threshold):
                            constraints.append(['F', 'F', 'F'])
                        else:
                            constraints.append(['T', 'T', 'T'])
                    
                    structure['constraints'] = constraints
                    st.session_state.structure = structure
                    fixed_count = sum(1 for c in constraints if c[0] == 'F')
                    st.success(f"Fixed {fixed_count} atoms")
                    st.rerun()
            
            with st.expander("🎯 Center Atoms"):
                center_axis = st.multiselect("Center along", ["x", "y", "z"], default=["z"])
                if st.button("Center"):
                    cart_pos = get_cartesian_positions(structure)
                    cell_center = np.sum(structure['lattice'], axis=0) / 2
                    atom_center = np.mean(cart_pos, axis=0)
                    
                    shift = np.zeros(3)
                    if "x" in center_axis:
                        shift[0] = cell_center[0] - atom_center[0]
                    if "y" in center_axis:
                        shift[1] = cell_center[1] - atom_center[1]
                    if "z" in center_axis:
                        shift[2] = cell_center[2] - atom_center[2]
                    
                    cart_pos += shift
                    if structure['coord_type'] == 'Direct':
                        structure['positions'] = cart_pos @ np.linalg.inv(structure['lattice'])
                    else:
                        structure['positions'] = cart_pos
                    st.session_state.structure = structure
                    st.success("Centered!")
                    st.rerun()
            
            with st.expander("🔄 Convert Coordinates"):
                current_type = structure['coord_type']
                st.write(f"Current: {current_type}")
                target_type = "Cartesian" if current_type == "Direct" else "Direct"
                
                if st.button(f"Convert to {target_type}"):
                    if target_type == "Cartesian":
                        structure['positions'] = get_cartesian_positions(structure)
                    else:
                        structure['positions'] = get_fractional_positions(structure)
                    structure['coord_type'] = target_type
                    st.session_state.structure = structure
                    st.success(f"Converted to {target_type}")
                    st.rerun()
        
        st.divider()
        
        st.subheader("💾 Export")
        if st.session_state.structure:
            poscar_str = write_poscar(st.session_state.structure, "/tmp/POSCAR_export")
            st.download_button(
                "Download POSCAR",
                data=poscar_str,
                file_name="POSCAR_edited",
                mime="text/plain"
            )
            
            save_path = st.text_input("Save to path", value="POSCAR_new")
            if st.button("Save"):
                write_poscar(st.session_state.structure, save_path)
                st.success(f"Saved to {save_path}")
    
    with right:
        st.subheader("🔬 3D Structure Viewer")
        
        if st.session_state.structure is None:
            st.info("Load a POSCAR file to visualize the structure.")
        else:
            view = show_viewer(
                st.session_state.structure,
                style=style,
                show_unitcell=show_cell,
                hidden_elements=hidden_elements
            )
            st.components.v1.html(view._make_html(), height=650, scrolling=False)
            
            with st.expander("📋 Atom List"):
                structure = st.session_state.structure
                atoms = get_atom_list(structure)
                cart_pos = get_cartesian_positions(structure)
                frac_pos = get_fractional_positions(structure)
                
                data = []
                for i, (atom, cart, frac) in enumerate(zip(atoms, cart_pos, frac_pos)):
                    constraint = ""
                    if structure['selective'] and structure['constraints']:
                        constraint = " ".join(structure['constraints'][i])
                    data.append({
                        "Index": i,
                        "Element": atom,
                        "x (Å)": f"{cart[0]:.4f}",
                        "y (Å)": f"{cart[1]:.4f}",
                        "z (Å)": f"{cart[2]:.4f}",
                        "Frac x": f"{frac[0]:.4f}",
                        "Frac y": f"{frac[1]:.4f}",
                        "Frac z": f"{frac[2]:.4f}",
                        "Fix": constraint
                    })
                
                st.dataframe(data, use_container_width=True)


# ---------- Main Entry Point ----------
if __name__ == "__main__":
    if STREAMLIT_MODE:
        run_streamlit_app()
    else:
        main_cli()
