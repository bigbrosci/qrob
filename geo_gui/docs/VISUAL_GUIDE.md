# Visual Guide: What You'll See

## The Complete User Interface

### Screenshot Simulation

```
╔════════════════════════════════════════════════════════════════════════════╗
║                       QVIEW - Interactive 3D Viewer                       ║
║                                                                            ║
║  [📥 Upload POSCAR]  [📂 Enter Path]  [🔄 Reload]  [💾 Save Path]        ║
║                                                                            ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌── STYLE ─────────────────────┐  ┌─ SELECT ATOMS ─────────────┐        ║
║  │                              │  │                             │        ║
║  │ Shape: ◉ Ballstick           │  │ 💡 How to select atoms:     │        ║
║  │        ○ Stick                │  │ Look at the atom numbers in │        ║
║  │        ○ Cartoon              │  │ the 3D viewer above, then  │        ║
║  │        ○ VDW                  │  │ use the selection controls │        ║
║  │                              │  │ below to pick atoms by     │        ║
║  │ ✓ Show Unit Cell            │  │ their index.                │        ║
║  │                              │  │                             │        ║
║  │ Colors:                      │  │ Mode: ◉ Single ○ Multiple  │        ║
║  │ ◉ Jmol     ○ CPK  ○ Custom  │  │                             │        ║
║  │                              │  │ SINGLE MODE:                │        ║
║  │ [Reset Colors]              │  │                             │        ║
║  │                              │  │ Atom Index:                 │        ║
║  │                              │  │ [——●——————————————————] 3   │        ║
║  │                              │  │  0                      5   │        ║
║  │                              │  │                             │        ║
║  │                              │  │ ℹ️ Selected: Atom 3 (N)     │        ║
║  │                              │  │                             │        ║
║  └── 3D VIEWER ─────────────────┘  │ ATOM INFO:                  │        ║
║  │                              │  │ Atom 3 (N):                 │        ║
║  │       5                       │  │ x = 1.23400 Å              │        ║
║  │      /|\  3                   │  │ y = 2.56700 Å              │        ║
║  │     / | \ ◆ ← Yellow highlight │ │ z = 3.89100 Å              │        ║
║  │    1  2  4                   │  │                             │        ║
║  │        6                      │  │ [Copy Coords]              │        ║
║  │                              │  │                             │        ║
║  │  Numbers = Atom indices      │  │ INFO:                       │        ║
║  │  Yellow = Selected atom(s)   │  │ Atoms: 6                    │        ║
║  │  Gray lines = Unit cell      │  │ Volume: 45.3 Ų             │        ║
║  │                              │  │ Formula: C2H3NO             │        ║
║  │ [Rotate: click+drag]         │  │                             │        ║
║  │ [Zoom: scroll]               │  │ TOOLS:                      │        ║
║  │ [Pan: right+drag]            │  │ ✏️ Edit ▼                  │        ║
║  │ [Reset: double-click]        │  │   [Translate] [Scale]      │        ║
║  │                              │  │   [Delete]   [More...]     │        ║
║  │ ▶ _make_html()              │  │                             │        ║
║  │     [Height: 500]            │  │                             │        ║
║  │                              │  │                             │        ║
║  └──────────────────────────────┘  └─────────────────────────────┘        ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

---

## Atom Labels (Close-Up)

```
What you see in the 3D viewer:

    ┌─────────────────────────────┐
    │ ┌────────────┐   ┌────────┐ │
    │ │ 0: Carbon  │   │ 2 ◄──┐ │ │
    │ │ ◉ Gray     │   │ ├─   │ │ │
    │ │            │   │ 1    │ │ │
    │ │ ┌────────┐ │   │ ◉ Light │ │
    │ │ │ 1: H   │ │   │ gray    │ │
    │ │ │ ◉ Light│ │   │ (Hydro) │ │
    │ │ │ gray   │ │   │         │ │
    │ │ └────────┘ │   └────────┘ │
    │ │            │   ┌────────┐ │
    │ │ ┌────────┐ │   │ 3      │ │
    │ │ │ 3:  N  │ │   │ ◉      │ │ ← Yellow (SELECTED)
    │ │ │ ◉      │ │   │ Yellow │ │
    │ │ │ Yellow │ │   │ (SELEC)│ │
    │ │ │ SEL!   │ │   └────────┘ │
    │ │ └────────┘ │               │
    │ │            │   ┌────────┐ │
    │ │ ┌────────┐ │   │ 5      │ │
    │ │ │ 4: C   │ │   │ ◉      │ │
    │ │ │ ◉ Gray │ │   │ Gray   │ │
    │ │ └────────┘ │   └────────┘ │
    │ └────────────┘               │
    └─────────────────────────────┘

Each label shows:
- White text (high contrast)
- Black background (readable)
- Atom index number (0, 1, 2, 3, 4, 5)
- Positioned at atom's 3D coordinate
- Stays with atom during rotation/zoom
```

---

## Selection UI Examples

### Single Atom Mode

```
┌─────────────────────────────────────┐
│ Mode: ◉ Single  ○ Multiple          │
│                                     │
│ Atom Index:                         │
│ [————————●─────────────────] 3      │
│ 0                              5    │
│                                     │
│ ℹ️  Selected: Atom 3 (N)            │
│                                     │
│ Atom 3 (N):                         │
│ x =  1.23400 Å                      │
│ y =  2.56700 Å                      │
│ z =  3.89100 Å                      │
│                                     │
│ [Copy Coordinates]                  │
└─────────────────────────────────────┘

User Action: Move slider left/right
  ↓
Updates to different atom index (0-5)
  ↓
Viewer updates with yellow highlight
  ↓
Coordinates display below
```

### Multiple Atom Mode

```
┌─────────────────────────────────────┐
│ Mode: ◉ Single  ○ Multiple          │
│                                     │
│ Select atoms:                       │
│ ▼ Search: [Type atom number...]   │
│   ☑ 0: C       ← Selected           │
│   ☐ 1: H                           │
│   ☑ 2: H       ← Selected           │
│   ☐ 3: N                           │
│   ☑ 5: O       ← Selected           │
│   ☐ 4: C                           │
│                                     │
│ ℹ️  Selected 3 atoms: [0, 2, 5]     │
│                                     │
│ Atom 0 (C):                         │
│ x =  0.00000 Å  y =  0.00000 Å     │
│ z =  0.00000 Å                      │
│                                     │
│ Atom 2 (H):                         │
│ x =  1.08900 Å  y =  1.08900 Å     │
│ z =  0.00000 Å                      │
│                                     │
│ Atom 5 (O):                         │
│ x =  2.17800 Å  y =  0.00000 Å     │
│ z =  0.00000 Å                      │
│                                     │
│ [Copy All Coordinates]              │
└─────────────────────────────────────┘

User Action: Click dropdown, select atoms
  ↓
All selected atoms highlight yellow
  ↓
Coordinates for all atoms display
```

---

## Edit Tools - Translate

```
┌─────────────────────────────────────┐
│ ✏️ Edit ▼                           │
│                                     │
│ Operation:                          │
│ ◉ Translate                         │
│ ○ Scale                             │
│ ○ Delete                            │
│ ○ Fix Z                             │
│ ○ Center                            │
│ ○ Convert                           │
│                                     │
│ TRANSLATE (Moves selected atoms)    │
│                                     │
│ dx: [1.000]                         │
│ dy: [0.000]                         │
│ dz: [0.000]                         │
│                                     │
│ [Apply]                             │
│                                     │
│ ✓ Translated 3 atoms                │
│   (Success message)                 │
│                                     │
└─────────────────────────────────────┘

User Workflow:
1. Select atoms (slider/dropdown)
2. Enter dx, dy, dz values
3. Click [Apply]
4. Watch atoms move in 3D view
5. Confirm coordinates changed
6. Download POSCAR to save
```

### Before & After Translate

```
BEFORE TRANSLATE:

    3 (N) at 1.234, 2.567, 3.891 Å
    ◉
    
AFTER TRANSLATE (dx=1.0, dy=0, dz=0):

                        3 (N) at 2.234, 2.567, 3.891 Å
                        ◉  ← Moved 1.0 Å in X direction
```

---

## Edit Tools - Delete

```
┌─────────────────────────────────────┐
│ ✏️ Edit ▼                           │
│                                     │
│ Operation:                          │
│ ○ Translate                         │
│ ○ Scale                             │
│ ◉ Delete                            │
│ ○ Fix Z                             │
│ ○ Center                            │
│ ○ Convert                           │
│                                     │
│ DELETE (Removes selected atoms)     │
│                                     │
│ ⚠️  Delete 3 selected atoms?        │
│     This cannot be undone!          │
│                                     │
│ [⚠️  Confirm Delete]                │
│                                     │
│ ✓ Deleted 3 atoms                   │
│   (Success message)                 │
│   Structure now has 3 atoms         │
│   (was 6 atoms)                     │
│                                     │
└─────────────────────────────────────┘

User Workflow:
1. Select atoms to delete
2. Click Edit → Delete
3. Warning appears with atom count
4. Click "Confirm Delete"
5. Atoms removed from structure
6. Viewer updates (fewer atoms)
7. Download POSCAR to save
```

### Before & After Delete

```
BEFORE DELETE (6 atoms):

    5
   /|\  3
  / | \ ◆
 1  2  4
     6

AFTER DELETE (removed atoms 0, 2, 5):

    1     (was atom 1, still atom 1)
    ◉
    
    2     (was atom 3, now atom 2)
    ◉
    
    3     (was atom 4, now atom 3)
    ◉

Total: 3 atoms remaining
```

---

## Color Schemes

### Jmol (Default)

```
Jmol colors (ASE/VESTA standard):

C  ◉ Gray (#909090)
H  ◉ Light gray (#EFEFEF)
N  ◉ Blue (#3050F8)
O  ◉ Red (#FF0D0D)
S  ◉ Yellow (#FFFF30)
P  ◉ Orange (#FF8000)
...and 83 more elements
```

### CPK (Alternative)

```
CPK colors (classic):

C  ◉ Dark gray (#CCCCCC)
H  ◉ White (#FFFFFF)
N  ◉ Light blue (#ADD8E6)
O  ◉ Bright red (#FF0000)
S  ◉ Yellow (#FFFF00)
P  ◉ Light brown (#D4A574)
...and ~14 more elements
```

### Custom (User-Defined)

```
When you select "Custom" color scheme:

Color Picker for each element:
┌──────────────────────────┐
│ C [●] #909090            │
│ H [●] #EFEFEF            │
│ N [●] #3050F8            │
│ O [●] #FF0D0D            │
│ ...                      │
└──────────────────────────┘

Click the color box to pick new color
Changes apply immediately
```

---

## Real Example: Methane Molecule

### Initial View

```
Load CH4 (methane):

       1 (H)
       ◉
      /
     /
    0 (C) ── 2 (H)
    ◉
     \
      \
       3 (H)
       ◉
       
Plus 1 H at different angle (atom 4)
```

### Select Central Carbon (Atom 0)

```
Single mode, slider at 0:

       1 (H)
       ◉
      /
     /
    0 (C) ── 2 (H)
    ◉◆ ← YELLOW (SELECTED)
     \
      \
       3 (H)
       ◉

Info shows:
"Selected: Atom 0 (C)"
x = 0.000 y = 0.000 z = 0.000 Å
```

### Select All Hydrogens (Atoms 1, 2, 3, 4)

```
Multiple mode, select 1, 2, 3, 4:

       1 (H)
       ◆
      /
     /
    0 (C) ── 2 (H)
    ◉         ◆
     \
      \
       3 (H)
       ◆
       
Plus atom 4 (H) ◆

Info shows:
"Selected 4 atoms: [1, 2, 3, 4]"
Atom 1 (H): x = 0.629, y = 0.629, z = 0.629 Å
Atom 2 (H): x = -0.629, y = -0.629, z = 0.629 Å
... etc
```

---

## Keyboard & Mouse Controls (In 3D Viewer)

```
┌──────────────────────────────────────┐
│         3D VIEWER CONTROLS           │
├──────────────────────────────────────┤
│                                      │
│ Rotate Structure:                    │
│   Click and drag with mouse          │
│   Left-click: ← → rotate around Y    │
│   Left-click: ↑ ↓ rotate around X    │
│                                      │
│ Zoom In/Out:                         │
│   Scroll wheel up:    Zoom in        │
│   Scroll wheel down:  Zoom out       │
│                                      │
│ Pan (Move) Structure:                │
│   Right-click and drag               │
│   Moves structure around viewport    │
│                                      │
│ Reset View:                          │
│   Double-click anywhere              │
│   Auto-centers and fits structure    │
│                                      │
│ Highlight Selection:                 │
│   (No direct clicking on atoms)      │
│   Use slider/dropdown below viewer   │
│                                      │
└──────────────────────────────────────┘
```

---

## File Operations

### Load POSCAR

```
┌──────────────────────────────────┐
│ 📥 UPLOAD POSCAR FILE:           │
│ [Choose file from computer...]   │
│ (or)                             │
│ 📂 ENTER FILE PATH:              │
│ [/path/to/POSCAR________]        │
│ [Load]                           │
│                                  │
│ ✓ Loaded: /home/structures/...  │
│   6 atoms found                  │
│                                  │
└──────────────────────────────────┘
```

### Save POSCAR

```
After editing structure:

┌──────────────────────────────────┐
│ [💾 Save Path]  [🔄 Reload]     │
│                                  │
│ Current file: /home/structures/  │
│ POSCAR                           │
│                                  │
│ ✓ Downloaded: POSCAR (modified)  │
│                                  │
│ File saved to Downloads folder   │
│                                  │
└──────────────────────────────────┘
```

---

## Summary of What You'll See

| Element | What It Shows | Why It Matters |
|---------|---------------|----------------|
| **Atom labels** | Numbers (0, 1, 2, ...) on atoms | Identifies each atom visually |
| **White text** | High contrast labels | Easy to read |
| **Black boxes** | Label backgrounds | Numbers stand out |
| **Yellow glow** | Selected atoms highlighted | Shows what you chose |
| **Gray structure** | Bonds and atoms | Jmol coloring (C, H, N, O, etc.) |
| **Gray lines** | Unit cell outline | Shows periodic boundaries |
| **Slider** | Move to select one atom | Intuitive single selection |
| **Dropdown** | Pick multiple atoms | Easy multi-selection with search |
| **Coordinates** | x, y, z values | Confirms atom position |
| **Info box** | "Selected: Atom 3 (N)" | Verifies correct selection |

---

You now know exactly what you'll see when you run the viewer! 🧬✨
