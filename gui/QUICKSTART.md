# 🚀 Quick Start Guide - Q-robot INCAR Generator

## 30-Second Setup

### Option 1: Direct Run (Recommended)
```bash
cd /home/qli/Dropbox/bin/qrob/gui
pip install flask
python3 app.py
```

Then open: **http://localhost:5000** in your browser

### Option 2: Using the Launcher
```bash
cd /home/qli/Dropbox/bin/qrob/gui
pip install flask
python3 run.py
```

This will automatically try to open your browser.

## What You'll See

When you access the interface, you'll see:

```
┌─────────────────────────────────────────────────────────────┐
│           🤖 Q-robot INCAR Generator                        │
│  Create VASP INCAR files with an intuitive interface        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────┬──────────────────────────────────┐
│    LEFT PANEL           │      RIGHT PANEL                 │
│  • Task Selection       │  • INCAR Preview                 │
│  • Standard Parameters  │  • Statistics                    │
│  • Task Parameters      │  • Save & Export                 │
│  • Custom Parameters    │  • Help Information              │
└─────────────────────────┴──────────────────────────────────┘
```

## Basic Workflow (3 Steps)

### Step 1: Select a Task
Click on any of the pre-configured calculation tasks:
- **Single** - Single point calculation
- **Dos** - Density of States
- **Electronic** - Electronic structure analysis
- **Workfunction** - Work function calculation
- **Md** - Molecular Dynamics
- And 20 more...

### Step 2: Configure Parameters
- **Standard Parameters**: Check/uncheck standard parameter sections
- **Task Parameters**: Automatically added based on selected task
- **Custom Parameters**: Add your own parameters as needed

### Step 3: Generate & Save
1. Click **"Generate INCAR"** to preview
2. Click **"Download INCAR File"** to save
   - Or use **"Copy to Clipboard"** to paste elsewhere

## Common Tasks

### Generate an MD INCAR
1. Click "Md" task button
2. Click "Generate INCAR"
3. Click "Download INCAR File"

### Add Custom Parameters
1. In the "Custom Parameters" section, click "+ Add Parameter"
2. Enter parameter name (e.g., `ENCUT`)
3. Enter value (e.g., `500`)
4. Click "Generate INCAR"

### Start Fresh
Click **"Reset Form"** to clear all selections

## Available Calculation Tasks (25 total)

| Task | Purpose |
|------|---------|
| Single | Single point calculation |
| Dos | Density of States |
| Electronic | Electronic structure analysis |
| Workfunction | Work function calculation |
| Md | Molecular Dynamics |
| Gas | Gas phase calculations |
| Bulk | Bulk structure optimization |
| Dftu | DFT+U calculations |
| Dipole | Dipole moment calculation |
| Tsopt | Transition State Optimization |
| Neb | Nudged Elastic Band |
| Dimer | Dimer method transition state search |
| Freq | Vibrational frequency analysis |
| Ispin | Spin-polarized calculations |
| Pbe0 | PBE0 hybrid functional |
| Hse03 | HSE03 hybrid functional |
| Hse06 | HSE06 hybrid functional |
| B3lyp | B3LYP hybrid functional |
| Hf | Hartree-Fock calculation |
| Vdwd3zero | van der Waals D3 correction |
| Vdwd3bj | van der Waals D3 with BJ damping |
| Mltrain | ML model training |
| Mlselect | ML structure selection |
| Mlrefit | ML model retraining |
| Mlmd | ML molecular dynamics |

## Standard Parameter Sections

The interface includes 8 standard parameter groups:

| Section | Parameters |
|---------|-----------|
| System | SYSTEM description |
| Start | PREC, ISTART, ICHARG, GGA |
| Electronic | ISPIN, ENCUT, NELM, EDIFF, LREAL, ALGO |
| Ionic | EDIFFG, NSW, IBRION, POTIM, ISIF, ISYM |
| Smearing | ISMEAR, SIGMA |
| Write | LWAVE, LCHARG, LVHAR, LORBIT, NWRITE |
| Lapack | LSCALAPACK setting |
| NCORE | Parallel computing setting |

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Click task | Select calculation task |
| Click checkbox | Toggle parameter section |
| Ctrl+A in preview | Select all INCAR content |
| Ctrl+C | Copy to clipboard (after clicking button) |

## Troubleshooting

### Port 5000 Already in Use
If you get "Address already in use" error:

1. Edit `app.py` and change the port:
```python
app.run(debug=True, host='127.0.0.1', port=5001)
```

2. Then start: `python3 app.py`

3. Access at: http://localhost:5001

### Flask Not Installed
```bash
pip install flask
```

Or with conda:
```bash
conda install flask
```

### Can't Import Brain Module
Make sure you're running from the correct directory:
```bash
cd /home/qli/Dropbox/bin/qrob/gui
python3 app.py
```

### Browser Won't Open
Manually open: http://localhost:5000

## Advanced: API Endpoints

The interface provides REST API endpoints:

```bash
# Get all standard parameters
curl http://localhost:5000/api/standard-params

# Get parameters for a specific task
curl -X POST http://localhost:5000/api/task-params \
  -H "Content-Type: application/json" \
  -d '{"task":"md"}'

# Generate INCAR
curl -X POST http://localhost:5000/api/generate-incar \
  -H "Content-Type: application/json" \
  -d '{"task":"single","include_sections":{"d_start":true}}'
```

## Customization

### Add a New Task
1. Edit `/home/qli/Dropbox/bin/qrob/brain/incar.py`
2. Add to `tasks_incar` dictionary:
```python
'd_cal_mytask' : {'PARAM1':'value1', 'PARAM2':'value2'}
```
3. Refresh the web page - new task appears automatically!

### Change Styling
Edit `/home/qli/Dropbox/bin/qrob/gui/static/css/style.css`

### Modify Layout
Edit `/home/qli/Dropbox/bin/qrob/gui/templates/index.html`

## Tips & Tricks

1. **Combine Tasks**: Use custom parameters to override task defaults
2. **Template**: Generate one INCAR and use it as a template
3. **Backup**: Download INCAR files and keep them organized
4. **Version Control**: Add generated INCARs to git for reproducibility

## Need Help?

- Check the full README.md for detailed documentation
- Look at example INCAR files in your VASP installations
- Consult VASP manual: https://www.vasp.at/wiki/index.php/Main_Page

---

**Enjoy using Q-robot INCAR Generator!** 🚀
