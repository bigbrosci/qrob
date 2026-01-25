# Atom Selection Workflow Diagram

## Visual Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    STREAMLIT APP INTERFACE                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   3D STRUCTURE VIEWER                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  [3D Molecular Structure with atom labels]              │   │
│  │                                                          │   │
│  │     5      ← Atom index labels (white on black)        │   │
│  │    /|\  3                                               │   │
│  │   / | \/ ← Yellow highlighted = selected atoms        │   │
│  │  1  2  4                                                │   │
│  │         6                                               │   │
│  │                                                          │   │
│  │  Rotate: click+drag  Zoom: scroll  Pan: right+drag    │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              ATOM SELECTION CONTROLS                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  💡 How to select atoms: Look at the atom numbers in the       │
│     3D viewer above, then use the selection controls below     │
│     to pick atoms by their index.                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Mode: ◉ Single  ○ Multiple                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  SINGLE MODE:                                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Atom Index: [————●————————] 3                            │  │
│  │                                                           │  │
│  │ ℹ️  Selected: Atom 3 (N)                                 │  │
│  │    Position: x=1.234  y=2.567  z=3.891 Å               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  MULTIPLE MODE:                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Select atoms: ▼ Search: [_______]                       │  │
│  │   ☑ 0: C                                                │  │
│  │   ☑ 2: H                                                │  │
│  │   ☑ 5: O                                                │  │
│  │   ☐ 1: H                                                │  │
│  │   ☐ 3: N                                                │  │
│  │   ☐ 4: C                                                │  │
│  │   ☐ 6: O                                                │  │
│  │                                                          │  │
│  │ ℹ️  Selected 3 atoms: [0, 2, 5]                         │  │
│  │    Atom 0 (C): x=0.000  y=0.000  z=0.000 Å            │  │
│  │    Atom 2 (H): x=1.089  y=1.089  z=0.000 Å            │  │
│  │    Atom 5 (O): x=2.178  y=0.000  z=0.000 Å            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    EDIT TOOLS                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✏️ Edit ▼                                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Operation: ◉ Translate  ○ Scale  ○ Delete  ○ ...        │  │
│  │                                                           │  │
│  │ TRANSLATE (Moves selected atoms):                       │  │
│  │   dx: [0.000]    dy: [0.000]    dz: [1.000]            │  │
│  │   [Apply]                                                │  │
│  │   ✓ Translated 3 atoms                                  │  │
│  │                                                           │  │
│  │ DELETE (Removes selected atoms):                        │  │
│  │   ⚠️  Delete 3 selected atoms? This cannot be undone!   │  │
│  │   [⚠️  Confirm Delete]                                   │  │
│  │                                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   SAVE & DOWNLOAD                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [📥 Download POSCAR]  [🔄 Reload]  [💾 Save Path]            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
User Action                  Internal State                Output
═══════════════════════════════════════════════════════════════════

1. Load POSCAR
   │
   ├──→ Read positions         st.session_state.structure  ┐
   │    Read lattice                                        ├──→ Display
   │    Read elements                                       │    Structure
   │                                                        ┐
   │                                                  View renderer
   │
2. Select Atoms (Single Mode)
   │
   ├──→ Move slider            st.session_state.selected   ┐
   │    slider value = 3       atoms_list = [3]            ├──→ Highlight
   │                                                        │    Atom #3
   │                                                  view.setStyle()
   │
3. View Yellow Highlight
   │
   ├──→ Atom #3 shows          Yellow sphere at scale 0.5  ┐
   │    in yellow                                          ├──→ Visual
   │    Coordinates displayed                              │    Feedback
   │                                                        ┐
   │                                                    py3Dmol
   │
4. Translate Selected Atoms
   │
   ├──→ Input: dx=1.0          Get cartesian positions    ┐
   │          dy=0.0           Add [1.0, 0.0, 0.0] to    ├──→ Update
   │          dz=0.0           selected atoms only         │    Structure
   │    Click [Apply]          Convert back to Direct     │
   │                                                       │
   │                         st.session_state.structure
   │
5. Viewer Re-renders
   │
   └──→ Show updated           New xyz coordinates         Atom #3 moved
        positions              Re-render labels            1 Å in X
        Re-show labels         Reset highlighting


═══════════════════════════════════════════════════════════════════
```

## State Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    STREAMLIT SESSION STATE                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  st.session_state = {                                           │
│      'structure': {                                              │
│          'lattice': [[a1, a2, a3], ...],                        │
│          'positions': [[x, y, z], ...],         (N_atoms × 3)   │
│          'elements': ['C', 'H', 'O', ...],                      │
│          'counts': [2, 3, 1, ...],                              │
│          'total_atoms': 6,                                       │
│          'coord_type': 'Direct'/'Cartesian',                    │
│          'constraints': {...},                                   │
│      },                                                          │
│      'selected_atoms': [0, 2, 5],    ← Updated by slider/       │
│      'custom_colors': {'C': '#909090', ...},    multiselect     │
│      'file_path': '/path/to/POSCAR'                             │
│  }                                                               │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
        │
        ├──→ show_viewer_interactive(structure, selected_atoms)
        │
        ├──→ For each selected atom in list:
        │    view.setStyle({"index": idx}, {"sphere": 
        │                  {"color": "yellow", "scale": 0.5}})
        │
        ├──→ For each atom in structure:
        │    view.addLabel(f"{idx}", {...})
        │
        └──→ Return py3Dmol view object
             Display in st.components.v1.html()
```

## Interaction Timeline

```
TIME    USER ACTION           COMPONENT          STATE CHANGE
────────────────────────────────────────────────────────────────────
T0      Click Upload POSCAR   File Input         load_poscar()
        ↓
T1      Load complete         Streamlit          st.session_state.
                                                  structure populated
        ↓
T2      View renders          py3Dmol Viewer     Display atoms
        with atom labels      HTML Component     with numbers
        ↓
T3      Read atom #3          Check labels       Identify atom #3
        on structure          visually           at position (x,y,z)
        ↓
T4      Move slider to 3      Streamlit Slider   selected_atoms_list
                                                  = [3]
        ↓
T5      Rerun triggered       Streamlit          show_viewer_
                              Session State      interactive()
                                                  called with [3]
        ↓
T6      Atom #3 highlighted   py3Dmol            setStyle() with
        in yellow             View Renderer      yellow color
        ↓
T7      Show coordinates      Streamlit UI       Display "Atom 3
                              Text Component     (N): x=... y=..."
        ↓
T8      Enter translate       Streamlit          dx=1.0, dy=0,
        values dx=1.0         Number Input       dz=0
        ↓
T9      Click [Apply]         Button             translate_atoms()
        ↓
T10     Calculate new         Python Math        cartesian_pos[3] +=
        position                                 [1.0, 0, 0]
        ↓
T11     Rerun                 Streamlit          New structure
        triggered             Renderer           state saved
        ↓
T12     Display updated       py3Dmol View       Atom #3 moved
        viewer                                   1 Å in X direction
        ↓
T13     Label updates         Atom Label         Label position
                              Renderer           updated to new XYZ
        ↓
T14     Show new coords       Streamlit UI       Display updated
                                                 coordinates
        ↓
T15     Ready for next        Idle               Await user input
        operation
```

## Color & Highlighting Logic

```
┌─────────────────────────────────────────────────────────────────┐
│              ATOM COLORING & STYLING LOGIC                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  For each atom in structure:                                    │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ 1. Get element (e.g., 'C', 'H', 'O')              │      │
│  │                                                     │      │
│  │ 2. Look up color from scheme:                      │      │
│  │    ┌──────────────────────────────────────┐        │      │
│  │    │ color_scheme = "jmol" (default)     │        │      │
│  │    │ colors = get_color_scheme("jmol")   │        │      │
│  │    │ color = colors.get('C') = '#909090' │        │      │
│  │    └──────────────────────────────────────┘        │      │
│  │                                                     │      │
│  │ 3. Apply color to atom via setStyle():            │      │
│  │    view.setStyle({"elem": 'C'},                  │      │
│  │                  {"sphere": {"color": color}})    │      │
│  │                                                     │      │
│  │ 4. Check if atom is selected:                      │      │
│  │    if idx in selected_atoms_list:                 │      │
│  │       OVERRIDE with yellow                         │      │
│  │       view.setStyle({"index": idx},              │      │
│  │                     {"sphere": {"color": "yellow",│      │
│  │                                 "scale": 0.5}})   │      │
│  │                                                     │      │
│  │ 5. Result:                                         │      │
│  │    ┌─ Selected atoms:   ◉ Yellow                   │      │
│  │    ├─ Unselected C:     ◉ Gray (#909090)          │      │
│  │    ├─ Unselected H:     ◉ Light gray (#EFEFEF)    │      │
│  │    └─ Hidden elements:  (invisible, scale=0)      │      │
│  └──────────────────────────────────────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

RENDERING ORDER (Important!):
  1. Apply element-based colors to all atoms
  2. Apply hidden element filtering
  3. Override selected atoms with yellow (on top)
  4. Add atom index labels
  5. Draw unit cell lines
  6. Zoom/center to fit
```

---

## Reference: Selection Modes

### Single Atom Selection Flow

```
User moves slider to 3
  │
  ├──→ Streamlit detects change
  │
  ├──→ selected_atoms_list = [3]
  │
  ├──→ show_viewer_interactive(structure, selected_atoms=[3])
  │    is called
  │
  ├──→ Inside function:
  │    for idx in [3]:
  │        view.setStyle({"index": 3}, 
  │                      {"sphere": {"color": "yellow", "scale": 0.5}})
  │
  ├──→ Atom #3 renders in yellow
  │
  └──→ Coordinates displayed:
       Atom 3 (N): x=1.234 y=2.567 z=3.891 Å
```

### Multiple Atom Selection Flow

```
User clicks dropdown, selects items 0, 2, 5
  │
  ├──→ Streamlit detects changes
  │
  ├──→ selected_atoms_list = [0, 2, 5]
  │
  ├──→ show_viewer_interactive(structure, selected_atoms=[0, 2, 5])
  │    is called
  │
  ├──→ Inside function:
  │    for idx in [0, 2, 5]:
  │        view.setStyle({"index": idx}, 
  │                      {"sphere": {"color": "yellow", "scale": 0.5}})
  │
  ├──→ Atoms #0, #2, #5 render in yellow
  │
  └──→ Coordinates displayed:
       Atom 0 (C): x=0.000 y=0.000 z=0.000 Å
       Atom 2 (H): x=1.089 y=1.089 z=0.000 Å
       Atom 5 (O): x=2.178 y=0.000 z=0.000 Å
```

---

This diagram shows how all the pieces fit together!
