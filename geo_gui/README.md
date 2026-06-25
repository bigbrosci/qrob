# GEO GUI - Interactive 3D Molecular Structure Viewer

A Streamlit-based interface for viewing and editing POSCAR/CONTCAR structures in
the QROB workflow.

## Features

- 🧬 **Interactive 3D Visualization** - Rotate, zoom, and pan molecular structures
- 🎯 **Atom Selection** - Select atoms with visible index labels and intuitive UI controls
- 🎨 **Color Customization** - Jmol, CPK, or custom color schemes
- ✏️ **Structure Editing** - Translate, delete, and modify atoms
- 💾 **File Support** - Load and save POSCAR/CONTCAR structures
- 📊 **Structure Analysis** - View atomic coordinates, lattice parameters, and composition
- 🎮 **User-Friendly** - Clear UI with guided workflows and comprehensive documentation

## Quick Start

### Run the Application

```bash
streamlit run q-rob/geo_gui/geo_gui.py
```

### Basic Workflow

1. **Load Structure** - Upload POSCAR file or enter file path
2. **View Atoms** - See atom index numbers displayed on 3D structure
3. **Select Atoms** - Use slider (single) or dropdown (multiple) to select atoms
4. **Perform Operations** - Translate, delete, or analyze selected atoms
5. **Save Results** - Download modified POSCAR file

## Documentation

All documentation is in the `docs/` folder:

| Document | Purpose |
|----------|---------|
| **QUICKSTART.md** | 30-second startup guide |
| **START_HERE.md** | Overview and quick reference |
| **README_ATOM_SELECTION.md** | Getting started with atom selection |
| **ATOM_SELECTION_GUIDE.md** | Complete step-by-step guide |
| **QVIEW_QUICK_REFERENCE.md** | Quick lookup reference |
| **VISUAL_GUIDE.md** | UI screenshots and examples |
| **DOCUMENTATION_INDEX.md** | Navigation guide to all docs |

See `docs/` directory for complete documentation.

## File Structure

```
q-rob/geo_gui/
├── geo_gui.py                    # Main application (1047 lines)
├── README.md                   # This file
└── docs/                       # Documentation
    ├── QUICKSTART.md
    ├── START_HERE.md
    ├── README_ATOM_SELECTION.md
    ├── ATOM_SELECTION_GUIDE.md
    ├── QVIEW_QUICK_REFERENCE.md
    ├── VISUAL_GUIDE.md
    ├── SELECTION_CHANGES_SUMMARY.md
    ├── WORKFLOW_DIAGRAMS.md
    ├── ATOM_SELECTION_COMPLETE.md
    ├── DOCUMENTATION_INDEX.md
    ├── FINAL_SUMMARY.md
    └── COMPLETION_CERTIFICATE.md
```

## Requirements

- Python 3.9+
- Streamlit
- py3Dmol
- NumPy
- ASE (optional, for additional features)

## Installation

```bash
# Navigate to project root
cd /Users/qiang_li/bin

# Activate your Python environment
source .venv/bin/activate

# Install dependencies (if not already installed)
pip install streamlit py3Dmol numpy

# Run the viewer
streamlit run q-rob/geo_gui/geo_gui.py
```

## Usage Examples

### Select and Translate Atoms

```
1. Load POSCAR file
2. Use slider to select atom #3
3. Click Edit → Translate
4. Enter dx=1.0 (move 1 Angstrom in X)
5. Click Apply
6. Download modified POSCAR
```

### Delete Specific Atoms

```
1. Load POSCAR file
2. Switch to Multiple mode
3. Select atoms 0, 2, 5 from dropdown
4. Click Edit → Delete → Confirm
5. Download file without those atoms
```

### Analyze Structure

```
1. Load POSCAR file
2. View atom coordinates in Info panel
3. Check lattice parameters
4. View composition and formula
5. Select atoms to see their specific coordinates
```

## Features

### Atom Selection
- **Visible Labels** - Atom index numbers (0, 1, 2, ...) displayed on structure
- **Single Selection** - Use slider to pick one atom
- **Multiple Selection** - Use dropdown to select many atoms
- **Visual Feedback** - Selected atoms highlight in yellow

### Visualization
- **3D Viewer** - py3Dmol powered interactive display
- **Unit Cell** - Visualize periodic cell boundaries
- **Color Schemes** - Jmol (default), CPK, or custom
- **View Controls** - Rotate, zoom, pan, reset

### Editing Tools
- **Translate** - Move selected atoms or entire structure
- **Delete** - Remove selected atoms with confirmation
- **Scale** - Scale lattice vectors
- **Center** - Center structure in cell
- **Convert** - Toggle between Direct/Cartesian coordinates
- **Fix Z** - Fix z-coordinates for specific atoms

### File Operations
- **Upload** - Load POSCAR/CONTCAR files
- **Path Input** - Enter file path directly
- **Download** - Save modified structures as POSCAR
- **Auto-parsing** - Handles various format variations

## Keyboard Shortcuts (3D Viewer)

| Action | Control |
|--------|---------|
| **Rotate** | Click + drag |
| **Zoom** | Scroll wheel |
| **Pan** | Right-click + drag |
| **Reset** | Double-click |

## Troubleshooting

### "I don't see atom numbers"
- Try zooming in (scroll wheel)
- Rotate view to see all atoms
- Atom numbers are positioned at each atom's location

### "Selection doesn't work"
- Ensure you're in the correct mode (Single/Multiple)
- Check that atoms are loaded (count in Info panel)
- Verify the info box shows selected atoms
- Try reloading the file

### "Atoms aren't moving"
- Make sure atoms are selected
- Check dx, dy, dz values aren't all zero
- Verify Translate operation is selected in Edit menu

### "Can't download file"
- Check that structure is loaded
- Verify you have write permissions in Downloads folder
- Try different file path

See `docs/QVIEW_QUICK_REFERENCE.md` for more troubleshooting tips.

## Technical Details

- **Language**: Python 3.9+
- **Frontend**: Streamlit (web UI)
- **3D Engine**: py3Dmol (JavaScript)
- **Chemistry**: ASE/Jmol colors (89+ elements)
- **Data**: NumPy arrays for efficient computation
- **Architecture**: Modular design with session state management

## Performance

| Metric | Value |
|--------|-------|
| **Structure Size** | 1-1000+ atoms |
| **Render Speed** | <1s (typical) |
| **Label Update** | Real-time |
| **Selection** | Instant |
| **Memory** | ~50-200 MB typical |

## Future Enhancements

- Distance calculations between atoms
- Angle calculations for atom groups
- Batch operations (delete all of element type)
- Undo/redo functionality
- Symmetry analysis
- Advanced editing tools
- Export selected atoms to new file

## License

This interface is part of the QROB project.

## Contributing

Contributions are welcome through pull requests or issues.

## Support

For help, see the comprehensive documentation in the `docs/` folder.

Quick entry points:
- **New to geo_gui?** → `docs/QUICKSTART.md`
- **Want to learn?** → `docs/README_ATOM_SELECTION.md`
- **Need quick answer?** → `docs/QVIEW_QUICK_REFERENCE.md`
- **Find anything?** → `docs/DOCUMENTATION_INDEX.md`

---

**Happy structure viewing!** 🧬✨

*For complete documentation, see the docs/ folder.*
