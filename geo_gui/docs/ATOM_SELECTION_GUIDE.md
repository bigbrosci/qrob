# Atom Selection Guide

## How to Select Atoms in the 3D Viewer

The interactive viewer in `geo_gui.py` now supports easy atom selection. Here's how to use it:

### Step 1: Load Your Structure
```bash
streamlit run /Users/qiang_li/bin/qrob/geo_gui/geo_gui.py
```

### Step 2: Identify Atoms
When the viewer loads, **you'll see atom index numbers displayed on top of each atom in the 3D structure**. These numbers (0, 1, 2, 3, ...) identify each atom.

### Step 3: Select Atoms
There are two selection modes:

#### **Single Atom Selection**
- Choose **Single** mode
- Use the slider to select atom index (0 to N-1)
- The selected atom will be highlighted in **yellow**
- Info box shows: "Selected: Atom X (Element)"

#### **Multiple Atom Selection**
- Choose **Multiple** mode  
- Click the dropdown to select multiple atoms
- Format shows: "0: C", "1: H", "2: O", etc.
- Selected atoms will be highlighted in **yellow**
- Info box shows count and first 5 indices

### Step 4: Perform Operations
Once atoms are selected, use the **Tools** panel on the right:
- **Delete**: Remove selected atoms
- **Translate**: Move selected atoms (Note: all atoms move for now)
- **Scale**: Scale atomic positions
- **Fix Z**: Fix z-coordinates
- **Center**: Center structure
- **Convert**: Switch between Direct/Cartesian coordinates

## Visual Feedback

### Atom Labels
- **White text on black background** showing atom indices (0, 1, 2, ...)
- Displayed at each atom's position
- Font size 12pt for good visibility

### Selected Atoms
- Highlighted with **yellow sphere effect**
- Larger scale makes them stand out
- Selected atom coordinates shown below viewer

### Unit Cell
- Gray lines showing the unit cell boundaries
- Toggle with "Show Unit Cell" option

## Example Workflow

1. Load POSCAR file
2. Look at the 3D structure and find the atom you want (e.g., atom #5)
3. Select **Single** mode
4. Slide to index 5
5. Atom #5 highlights yellow and coordinates appear
6. Click "Edit" → "Delete" → "Confirm" to delete it
7. View updates showing structure without that atom

## Keyboard Shortcuts (In 3D Viewer)
- **Rotate**: Click + drag
- **Zoom**: Scroll wheel
- **Pan**: Right-click + drag

## Technical Notes

- Atom indices are 0-indexed (first atom is 0, not 1)
- Labels are positioned at each atom's Cartesian coordinates
- Streamlit widgets provide the selection interface (no mouse-click detection on atoms needed)
- Supports unlimited atoms - dropdown searchable for large structures
- Custom colors per element available in "Style" section

## Troubleshooting

**Q: I don't see atom numbers**
- A: Ensure "Show Unit Cell" is toggled in the Style section
- A: Try zooming in (scroll wheel) to see labels better
- A: Labels are at each atom's position - rotate viewer to see them

**Q: Selection doesn't highlight atoms**
- A: Verify you have atoms loaded (check "Atoms" count in Info panel)
- A: Check that selected_atoms_list is not empty
- A: Try switching between Single and Multiple modes

**Q: Multiple atom selection doesn't work**
- A: In Multiple mode, click the dropdown and search for atom indices
- A: Format is "index: element" (e.g., "3: N")
- A: Use Ctrl+click or Cmd+click to select multiple from dropdown

## Future Enhancements

Planned features:
- Distance calculations between selected atoms
- Angle calculations for 3+ atoms
- Translate operations on just selected atoms (not all atoms)
- Batch operations (e.g., delete all of element type X)
- Export selected atoms to new POSCAR
