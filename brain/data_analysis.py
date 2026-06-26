#!/usr/bin/env python3
"""Shared data-analysis and plotting helpers."""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from scipy import stats
from scipy import interpolate


@dataclass
class LinearFitResult:
    slope: float
    intercept: float
    r_squared: float
    mae: float
    rmse: float


def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def fit_linear_series(x: np.ndarray, y: np.ndarray) -> LinearFitResult:
    slope, intercept, r_value, _p_value, _stderr = stats.linregress(x, y)
    y_pred = x * slope + intercept
    mae = float(np.mean(np.abs(y - y_pred)))
    rmse = _rmse(y, y_pred)
    return LinearFitResult(
        slope=float(slope),
        intercept=float(intercept),
        r_squared=float(r_value**2),
        mae=mae,
        rmse=rmse,
    )


def fit_linear_csv(csv_path: str, x_column: str = "IS", y_column: str = "TS") -> LinearFitResult:
    df = pd.read_csv(csv_path)
    x = np.array(df[x_column], dtype=float)
    y = np.array(df[y_column], dtype=float)
    return fit_linear_series(x, y)


def detect_linear_columns(df: pd.DataFrame) -> tuple[str, str]:
    if "De" in df.columns and "Ea" in df.columns:
        return "De", "Ea"
    if "IS" in df.columns and "TS" in df.columns:
        return "IS", "TS"
    raise ValueError("CSV must contain either ('De','Ea') or ('IS','TS') columns")


def plot_linear_fit(
    csv_path: str,
    out: str | None = None,
    x_column: str | None = None,
    y_column: str | None = None,
) -> str:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    data = pd.read_csv(csv_path)
    if x_column is None or y_column is None:
        x_column, y_column = detect_linear_columns(data)

    x = data[x_column].values.astype(float)
    y = data[y_column].values.astype(float)
    result = fit_linear_series(x, y)
    y_pred = result.slope * x + result.intercept

    equation = f"{y_column} = {result.slope:.2f} x + {result.intercept:.2f}"
    order = np.argsort(x)

    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, color="blue", label="DFT")
    plt.plot(x[order], y_pred[order], color="red", label="Reg.")
    textstr = (
        f"{equation}\n"
        f"MAE: {result.mae:.2f}\n"
        f"RMSE: {result.rmse:.2f}\n"
        f"R2: {result.r_squared:.2f}"
    )
    plt.gca().text(
        0.65,
        0.25,
        textstr,
        transform=plt.gca().transAxes,
        fontsize=12,
        verticalalignment="top",
        bbox=dict(facecolor="white", alpha=0),
    )
    plt.xlabel(x_column, fontsize=14)
    plt.ylabel(y_column, fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(loc="upper left", frameon=False, fontsize=12)
    plt.tight_layout()

    out_name = out or (os.path.splitext(os.path.basename(csv_path))[0] + ".png")
    plt.savefig(out_name, dpi=300)
    plt.close()
    return out_name


def plot_neb_profile(dirs: list[str] | None = None, name: str = "neb", out: str | None = None) -> str:
    if dirs is None:
        all_dirs = sorted([d for d in os.listdir(".") if os.path.isdir(d)])
        numeric = [d for d in all_dirs if d.isdigit()]
        dirs = numeric if numeric else all_dirs

    if not dirs:
        raise RuntimeError("No directories found for NEB plotting")

    energies: list[float] = []
    used_dirs: list[str] = []
    for directory in dirs:
        outcar = os.path.join(directory, "OUTCAR")
        if not os.path.exists(outcar):
            continue
        energy = None
        with open(outcar, "r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                if "  without" in line:
                    energy = line.rstrip().split()[-1]
        if energy is None:
            continue
        energies.append(float(energy))
        used_dirs.append(directory)

    if not energies:
        raise RuntimeError("No energies extracted for NEB")

    relative = [value - energies[0] for value in energies]
    try:
        x_vals = [int(d) for d in used_dirs]
    except Exception:
        x_vals = list(range(len(used_dirs)))

    xnew = np.linspace(min(x_vals), max(x_vals), 600)
    spline = interpolate.InterpolatedUnivariateSpline(x_vals, relative)
    ynew = spline(xnew)

    plt.figure()
    plt.plot(xnew, ynew)
    plt.plot(x_vals, relative, "o", alpha=0.6)
    plt.xlabel("Reaction Coordinates")
    plt.ylabel("Potential Energy / eV")
    plt.tight_layout()
    out_name = out or f"{name}.png"
    plt.savefig(out_name, dpi=300)
    plt.close()
    return out_name
