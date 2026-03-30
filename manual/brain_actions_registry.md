# Brain ↔ Actions Registry

This document records how the `actions_py/` utilities depend on `brain/` helpers and introduces
the new `actions_py.registry` module that centralizes this metadata.

## Brain helpers consumed by actions

| Helper | Purpose | Calling actions |
| --- | --- | --- |
| `brain.poscar.parse_atom_targets(targets, poscar_path)` | Turn CLI-style selections (element symbols or 0-based indices) into canonical atom indices | `actions_py/delete_atoms.py`, `actions_py/fix_by_atoms.py`, `actions_py/bottom.py`, `actions_py/get_mag.py`, `actions_py/get_bader.py` |
| `brain.outcar.get_mag()` | Parse `OUTCAR` to extract per-atom magnetizations | `actions_py/get_mag.py` |
| `brain.potcar.concatenate(ele_list, version, out_path)` | Build a `POTCAR` from a list of elements | `actions_py/pp.py` |
| `brain.potcar.read_potcar(potcar_file)` | Pretty-print concatenated `POTCAR` metadata | `actions_py/pp.py` |

Use these helpers directly if you write new utilities that need atom selection, magnetization, or POTCAR management.

## Action registry overview

`actions_py.registry.ACTION_REGISTRY` maps a short identifier (`"delete_atoms"`, `"pp"`, etc.) to metadata describing:

- where the script sits (`script` path),
- a user-facing description and usage example,
- external dependencies (`ase`, `numpy`),
- which brain helpers it relies upon,
- the files it reads/writes, and
- an optional note about fallback behavior.

Example:

```python
from actions_py.registry import ACTION_REGISTRY, find_actions_by_helper

for helper in ("brain.poscar.parse_atom_targets", "brain.potcar.concatenate"):
    print(helper, "used by", find_actions_by_helper(helper))

info = ACTION_REGISTRY["delete_atoms"]
print("Run delete_atoms with", info["usage"])
```

## Action summaries (brain-aware subset)

| Action | Description | Brain helpers | Key files |
| --- | --- | --- | --- |
| `delete_atoms` | Delete atoms from a POSCAR using element names or indices and rewrite the file | `brain.poscar.parse_atom_targets` | `POSCAR`, `POSCAR_deleted` |
| `fix_by_atoms` | Set selective dynamics flags for a selection; writes `<POSCAR>_fixed` | `brain.poscar.parse_atom_targets` | `POSCAR`, `<POSCAR>_fixed` |
| `bottom` | Bottom the slab and optionally center an atom in XY | `brain.poscar.parse_atom_targets` | `POSCAR`, `POSCAR_bottomed.vasp`, `POSCAR_centered.vasp` |
| `get_mag` | Export per-atom magnetization from `OUTCAR` and publish `Magnetization.csv` | `brain.poscar.parse_atom_targets`, `brain.outcar.get_mag` | `OUTCAR`, `POSCAR/CONTCAR`, `Magnetization.csv` |
| `get_bader` | Compute Bader charges and optionally print a filtered selection | `brain.poscar.parse_atom_targets` | `ACF.dat`, `POTCAR`, `POSCAR`, `bader_all.csv` |
| `pp` | Generate a `POTCAR` either by reading `POSCAR` or accepting explicit element names | `brain.potcar.concatenate`, `brain.potcar.read_potcar` | `POSCAR`, `POTCAR` |

## Next steps

1. Import `actions_py.registry` from any tooling that needs to expose action metadata (e.g., the GUI modules or a CLI catalog).
2. Extend `ACTION_REGISTRY` as you add new scripts so the interface stays centralized.
3. When a helper evolves (e.g., `parse_atom_targets` signature changes), update this doc plus the registry so dependent scripts remain documented.
