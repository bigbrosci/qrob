# Quick Reference: geo_gui.py Atom Selection

## Running the Viewer

```bash
cd /Users/qiang_li/bin
source .venv/bin/activate
streamlit run qrob/geo_gui/geo_gui.py
```

## Visual Cues

| Feature | What It Means |
|---------|---------------|
| White text on black labels | Atom index numbers (0, 1, 2, ...) |
| Yellow highlighted atoms | Currently selected atoms |
| Gray lines | Unit cell boundaries |
| Element colors | Jmol standard colors (or CPK, or custom) |

## Selection Workflow

### Single Atom Selection
```
1. Choose "Single" mode
2. Move slider to desired atom index
3. Atom highlights in yellow
4. Coordinates appear below
```

### Multiple Atom Selection
```
1. Choose "Multiple" mode
2. Click dropdown, search for atoms
3. Select multiple atoms (Ctrl+click or Cmd+click)
4. All selected atoms highlight in yellow
```

## Operations on Selected Atoms

| Operation | Effect | Notes |
|-----------|--------|-------|
| **Translate** | Move selected atoms by (dx, dy, dz) | If no atoms selected, moves all atoms |
| **Delete** | Remove selected atoms permanently | Cannot be undone - requires confirmation |
| **Scale** | Scale lattice vectors | Affects all atoms, not just selected |
| **Fix Z** | Fix z-coordinates of atoms | Requires single atom selection |
| **Center** | Center structure | Affects all atoms |
| **Convert** | Toggle Direct/Cartesian coords | Affects all atoms |

## Atom Index Numbering

- **0-indexed**: First atom is index 0, last is N-1
- **Persistent**: Numbers don't change when you rotate/zoom
- **Position-based**: Numbers stay with their atoms during edits

## Customization Options

### Style
- **Shape**: Stick, Ball-Stick, Van der Waals, Cartoon
- **Unit Cell**: Toggle on/off
- **Color Scheme**: Jmol (default), CPK, Custom
- **Color Picker**: Pick custom colors for each element

### View Control
- **Rotate**: Click + drag in viewer
- **Zoom**: Scroll wheel
- **Pan**: Right-click + drag
- **Reset**: Double-click to fit structure

## File Operations

| Action | Process |
|--------|---------|
| **Load** | Upload POSCAR file or enter path |
| **Save** | After editing, use "Download POSCAR" |
| **Copy Path** | Click copy icon next to file path |

## Common Issues & Solutions

### "I don't see atom numbers"
- ✓ Zoom in (scroll) - labels are small by default
- ✓ Rotate view - some atoms may be behind others
- ✓ Check "Show Unit Cell" isn't blocking view

### "Atoms aren't highlighting"
- ✓ Make sure atoms are selected (check info box)
- ✓ Try switching between Single/Multiple modes
- ✓ Reload the file if stuck

### "Selected atoms aren't moving"
- ✓ Check selected_atoms_list isn't empty
- ✓ Verify dx, dy, dz values aren't all zero
- ✓ Use "Translate" (not Scale or other tools)

### "Viewer looks distorted"
- ✓ Click on viewer and double-click to reset view
- ✓ Try different Style (Ball-Stick usually clearest)
- ✓ Reduce "Show Unit Cell" scale if too large

## Color Schemes

### Jmol (Default, Recommended)
- Standard ASE/VESTA colors
- Covers all 89+ elements
- Scientifically accurate

### CPK (Alternative)
- Classic CPK colors (~20 elements)
- If element not defined, shows gray

### Custom
- Pick your own colors
- Color picker appears for each unique element
- Saved for current session

## Tips & Tricks

1. **Find an atom quickly**: Use dropdown search in Multiple mode (e.g., type "2:" to find atoms starting with index 2)
2. **Select a range**: Use Multiple mode and Ctrl/Cmd+click first and last
3. **See atom types**: Hover over dropdown entries to see "index: element" format
4. **Batch delete**: Select all atoms of one type, delete in one operation
5. **Undo**: Download backup first, or reload original file
