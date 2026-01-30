# Available Calculation Tasks

The Q-robot INCAR Generator includes 25 pre-configured calculation tasks. Select any task from the dropdown menu or task buttons in the web interface.

## Complete Task List

| Task Name | Key | Description | Key Parameters |
|-----------|-----|-------------|-----------------|
| **Single** | d_cal_single | Single point energy calculation | NSW = 0 |
| **DOS** | d_cal_dos | Density of states calculation | ISMEAR = 0, SIGMA = 0.05, NEDOS = 1000 |
| **Electronic** | d_cal_electronic | Electronic structure analysis | LAECHG = T, LCHARG = T, LELF = T, LWAVE = T, LORBIT = 11 |
| **Workfunction** | d_cal_workfunction | Workfunction calculation | LVHAR = T, LDIPOL = T, IDIPOL = 3 |
| **MD** | d_cal_md | Molecular dynamics simulation | IBRION = 0, TEBEG = 273, TEEND = 273, NSW = 50000 |
| **Gas** | d_cal_gas | Gas phase calculation | ISMEAR = 0, SIGMA = 0.01 |
| **Bulk** | d_cal_bulk | Bulk material properties | ISIF = 3, ENCUT = 700, LDIPOL = F |
| **DFT+U** | d_cal_dftu | DFT+U correlation method | LDAU = T, LDAUTYPE = 2, LASPH = T |
| **Dipole** | d_cal_dipole | Dipole moment calculation | LDIPOL = T, IDIPOL = 3 |
| **TS-OPT** | d_cal_tsopt | Transition state optimization | IBRION = 1, POTIM = 0.05 |
| **NEB** | d_cal_neb | Nudged elastic band | LCLIMB = T, SPRING = -10, IBRION = 1 |
| **Dimer** | d_cal_dimer | Dimer method for saddle points | IBRION = 44, NSW = 500 |
| **Freq** | d_cal_freq | Frequency/vibrational analysis | IBRION = 5, POTIM = 0.015, NFREE = 2 |
| **IsPin** | d_cal_ispin | Spin-polarized calculation | ISPIN = 2 |
| **PBE0** | d_cal_pbe0 | PBE0 hybrid functional | LHFCALC = T, GGA = PE, AEXX = 0.25 |
| **HSE03** | d_cal_hse03 | HSE03 hybrid functional | LHFCALC = T, GGA = PE, AEXX = 0.25, HFSCREEN = 0.3 |
| **HSE06** | d_cal_hse06 | HSE06 hybrid functional | LHFCALC = T, GGA = PE, AEXX = 0.25, HFSCREEN = 0.2 |
| **B3LYP** | d_cal_b3lyp | B3LYP hybrid functional | LHFCALC = T, GGA = B3, AEXX = 0.20 |
| **HF** | d_cal_hf | Hartree-Fock method | LHFCALC = T, AEXX = 1.0 |
| **vdW-D3-Zero** | d_cal_vdwD3zero | van der Waals D3 (zero-damping) | IVDW = 11 |
| **vdW-D3-BJ** | d_cal_vdwD3bj | van der Waals D3 (Becke-Johnson) | IVDW = 12 |
| **ML-Train** | d_cal_mltrain | Machine learning model training | ML_LMLFF = T, ML_MODE = train |
| **ML-Select** | d_cal_mlselect | Machine learning sample selection | ML_LMLFF = T, ML_MODE = select |
| **ML-Refit** | d_cal_mlrefit | Machine learning model refinement | ML_LMLFF = T, ML_MODE = refit |
| **ML-MD** | d_cal_mlmd | Machine learning molecular dynamics | ML_MODE = run, NSW = 500000 |

## How to Use

### Using the Dropdown Menu
1. Open the web interface at http://localhost:5000
2. Click the **task dropdown** at the top
3. Select a task from the list
4. The task parameters will automatically load

### Using Task Buttons
1. Scroll through the task buttons
2. Click any button to select it
3. The task parameters appear below

## Standard Parameters

In addition to task-specific parameters, you can select standard parameter sections:

- **System**: System size and computational settings
- **Start**: Initial conditions and convergence
- **Electronic**: Electronic structure parameters
- **Ionic**: Ionic relaxation settings
- **Smearing**: Smearing and band structure
- **Write**: Output file options
- **LAPACK**: Linear algebra settings
- **ncore**: Parallelization parameters

## Custom Parameters

You can add custom parameters beyond the task-specific and standard sections:

1. Scroll to the **Custom Parameters** section
2. Click **+ Add Parameter**
3. Enter parameter name (e.g., ISPIN)
4. Enter parameter value (e.g., 2)
5. Click **Generate INCAR** to include them

## Example Workflow

1. Select **MD** task
2. Check **Electronic** and **Ionic** standard sections
3. Add custom parameter: ISPIN = 2
4. Click **Generate INCAR**
5. Download the INCAR file or copy to clipboard

## API Endpoints

All tasks are accessible via REST API:

```bash
# Get task parameters
curl -X POST http://localhost:5000/api/task-params \
  -H "Content-Type: application/json" \
  -d '{"task": "Single"}'

# Generate INCAR
curl -X POST http://localhost:5000/api/generate-incar \
  -H "Content-Type: application/json" \
  -d '{
    "task": "MD",
    "include_sections": {"d_ionic": true, "d_elec": true},
    "custom_params": {"ISPIN": "2"}
  }'
```

## Notes

- All task parameters are pre-configured for common calculations
- Combine with standard sections for complete INCAR files
- Modify parameters as needed for your specific calculations
- Machine learning (ML) tasks require special VASP compilation
- Hybrid functionals (PBE0, HSE03, HSE06, HF, B3LYP) are computationally expensive
