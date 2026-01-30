# 🚀 GET STARTED IN 30 SECONDS

## The Fastest Way to See Your Enhanced 3D Viewer

### Copy & Paste This Command

```bash
cd /Users/qiang_li/bin && streamlit run qrob/actions/qview.py
```

### Then Do This

1. **Wait for app to load** (opens in browser at http://localhost:8501)
2. **Upload POSCAR file** or enter file path
3. **Look at the 3D viewer** - you'll see atom numbers (0, 1, 2, ...)
4. **Use the slider below** to select an atom (or use dropdown for multiple)
5. **Watch it highlight yellow** - that's your selected atom!
6. **View the coordinates** displayed below
7. **Try Edit → Translate** to move atoms
8. **Try Edit → Delete** to remove atoms

### That's It! 

You now have a working interactive 3D structure viewer with atom selection.

---

## What You'll See

```
[3D VIEWER WITH ATOM LABELS]
    5
   /|\  3
  / | \ ◆ ← Yellow = selected
 1  2  4
     6

[SLIDER BELOW]
Atom Index: [————●————] 3

[INFO]
Selected: Atom 3 (N)
x=1.234 y=2.567 z=3.891 Å

[TOOLS]
[Edit ▼] → [Translate/Delete/...]
```

---

## Next Level: Read the Guide

Once you've played with it, read one of these:

- **Quick Summary** → [START_HERE.md](START_HERE.md) (2 min)
- **Getting Started** → [README_ATOM_SELECTION.md](README_ATOM_SELECTION.md) (5 min)  
- **Step-by-Step** → [ATOM_SELECTION_GUIDE.md](ATOM_SELECTION_GUIDE.md) (15 min)
- **Visual Examples** → [VISUAL_GUIDE.md](VISUAL_GUIDE.md) (10 min)
- **Quick Reference** → [QVIEW_QUICK_REFERENCE.md](QVIEW_QUICK_REFERENCE.md) (anytime)

---

## One More Thing

The key to using this viewer:

1. **Atom numbers are visible on the structure** (0, 1, 2, ...)
2. **Use the slider/dropdown to select by that number**
3. **Selected atoms turn yellow**
4. **Perform operations on the highlighted atoms**

That's the workflow!

---

## Common First-Time Tasks

### See atom 2
→ Move slider to 2 → Verify it highlights

### Select atoms 0, 2, 5
→ Switch to Multiple mode → Click dropdown → Check boxes

### Move atom 3 by 1 Angstrom
→ Select atom 3 → Edit → Translate → dx=1.0 → Apply

### Remove atom 4
→ Select atom 4 → Edit → Delete → Confirm

### Save my changes
→ Click "Download POSCAR" button

---

## Stuck?

- See [QVIEW_QUICK_REFERENCE.md](QVIEW_QUICK_REFERENCE.md) Troubleshooting
- Check [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) to find answers

---

**That's it. Now go run it!** 🚀

```bash
streamlit run /Users/qiang_li/bin/qrob/actions/qview.py
```

Happy structure editing! 🧬✨
