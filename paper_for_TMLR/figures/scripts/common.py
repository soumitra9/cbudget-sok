"""Shared matplotlib style for paper figures."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

DRAFT_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS_ROOT = Path(__file__).resolve().parents[4]
RESULTS_ROOT = EXPERIMENTS_ROOT / "results"
FIGURES_OUT = DRAFT_ROOT
SAVE_DPI = 600
FIGURE_DPI = 600

# Seaborn deep palette (matches Project_AnomalyDetectionSurvey paper figures).
PALETTE = ["#4c72b0", "#dd8452", "#55a868", "#c44e52", "#8172b3", "#937860", "#da8bc3", "#8c8c8c"]
BLUE = PALETTE[0]
ORANGE = PALETTE[1]
GREEN = PALETTE[2]
RED = PALETTE[3]
PURPLE = PALETTE[4]
BROWN = PALETTE[5]
PINK = PALETTE[6]
GRAY = PALETTE[7]
ERROR = "#333333"


def apply_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Nimbus Sans", "Liberation Sans", "Helvetica", "Arial"],
            "font.size": 8,
            "mathtext.fontset": "custom",
            "mathtext.rm": "Helvetica",
            "mathtext.it": "Helvetica:italic",
            "mathtext.bf": "Helvetica:bold",
            "axes.labelsize": 8,
            "axes.titlesize": 8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "figure.dpi": FIGURE_DPI,
            "savefig.dpi": SAVE_DPI,
            "savefig.format": "pdf",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.prop_cycle": mpl.cycler(color=PALETTE),
        }
    )


def bootstrap_mean_ci(values: list[float], n_boot: int = 1000, alpha: float = 0.05, seed: int = 42) -> tuple[float, float, float]:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    boots = [rng.choice(arr, size=arr.size, replace=True).mean() for _ in range(n_boot)]
    return float(arr.mean()), float(np.quantile(boots, alpha / 2)), float(np.quantile(boots, 1 - alpha / 2))


def bootstrap_sac_ci(rows: list[tuple[float, bool]], n_boot: int = 1000, alpha: float = 0.05, seed: int = 42) -> tuple[float, float, float]:
    if not rows:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    sacs: list[float] = []
    for _ in range(n_boot):
        sample = [rows[rng.integers(len(rows))] for __ in range(len(rows))]
        pt = sum(pt for pt, _ in sample)
        succ = sum(1 for _, ok in sample if ok)
        if succ:
            sacs.append(pt / succ)
    pt = sum(pt for pt, _ in rows)
    succ = sum(1 for _, ok in rows if ok)
    mean = pt / succ if succ else float("nan")
    return mean, float(np.quantile(sacs, alpha / 2)), float(np.quantile(sacs, 1 - alpha / 2))


def load_run_summary(experiment: str) -> list[dict[str, str]]:
    import csv

    path = RESULTS_ROOT / experiment / "run_summary.csv"
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def group_cells_by_y(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = f"Y{int(row['rtk_on'])}{int(row['factor_b_on'])}"
        grouped[key].append(row)
    return grouped


def set_error_ylim(
    ax: plt.Axes,
    means: list[float],
    err_lo: list[float],
    err_hi: list[float],
    *,
    label_headroom: float = 0.0,
    ymin_floor: float = 0.0,
    pad_lo: float = 0.08,
    pad_hi: float = 0.12,
) -> None:
    """Set y limits so error bars, caps, and optional labels stay inside the axes."""
    finite = [
        (mean, lo, hi)
        for mean, lo, hi in zip(means, err_lo, err_hi)
        if np.isfinite(mean) and np.isfinite(lo) and np.isfinite(hi)
    ]
    if not finite:
        return
    bottom = min(mean - lo for mean, lo, _ in finite)
    top = max(mean + hi for mean, _, hi in finite) + label_headroom
    ymin = max(ymin_floor, bottom * (1.0 - pad_lo) if bottom > 0 else ymin_floor)
    ymax = top * (1.0 + pad_hi) if top > 0 else 1.0
    if ymax <= ymin:
        ymax = ymin + 1.0
    ax.set_ylim(ymin, ymax)


def save_figure(fig: plt.Figure, name: str) -> Path:
    FIGURES_OUT.mkdir(parents=True, exist_ok=True)
    path = FIGURES_OUT / name
    fig.savefig(path, bbox_inches="tight", pad_inches=0.04, dpi=SAVE_DPI, format="pdf")
    plt.close(fig)
    return path
