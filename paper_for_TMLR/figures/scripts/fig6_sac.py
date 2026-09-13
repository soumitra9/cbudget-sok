"""Fig. 6: cost-of-pass (prompt tokens per success) by E1 treatment cell."""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from common import ERROR, PALETTE, RESULTS_ROOT, apply_style, bootstrap_sac_ci, load_run_summary, save_figure, set_error_ylim


def main() -> None:
    apply_style()
    rows = load_run_summary("e1")

    keys = ["Y00", "Y01", "Y10", "Y11"]
    labels = ["$Y_{00}$", "$Y_{01}$", "$Y_{10}$", "$Y_{11}$"]
    colors = PALETTE[:4]

    cell_rows: dict[str, list[tuple[float, bool]]] = {}
    for row in rows:
        key = f"Y{int(row['rtk_on'])}{int(row['factor_b_on'])}"
        success = str(row["success"]).lower() == "true"
        cell_rows.setdefault(key, []).append((float(row["pt"]), success))

    means, err_lo, err_hi = [], [], []
    success_counts: list[str] = []
    for key in keys:
        mean, lo, hi = bootstrap_sac_ci(cell_rows[key])
        means.append(mean)
        err_lo.append(mean - lo)
        err_hi.append(hi - mean)
        n_succ = sum(1 for _, ok in cell_rows[key] if ok)
        n_total = len(cell_rows[key])
        success_counts.append(f"{n_succ}/{n_total}")

    fig, ax = plt.subplots(figsize=(3.5, 2.8))
    x = np.arange(len(labels))
    bars = ax.bar(x, means, color=colors, edgecolor="white", linewidth=0.5, width=0.65)
    ax.errorbar(x, means, yerr=[err_lo, err_hi], fmt="none", ecolor=ERROR, capsize=3, linewidth=0.9)

    label_offset = max(m + e for m, e in zip(means, err_hi) if np.isfinite(m) and np.isfinite(e)) * 0.04
    for xi, (mean, ehi, label) in enumerate(zip(means, err_hi, success_counts)):
        if np.isfinite(mean) and np.isfinite(ehi):
            ax.text(xi, mean + ehi + label_offset, label, ha="center", va="bottom", fontsize=6.5)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Cost-of-pass (PT per success)")
    ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f"{v / 1000:.0f}k"))
    set_error_ylim(
        ax,
        means,
        err_lo,
        err_hi,
        label_headroom=label_offset * 1.6,
        ymin_floor=0.0,
        pad_hi=0.10,
    )

    path = save_figure(fig, "Fig6.pdf")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
