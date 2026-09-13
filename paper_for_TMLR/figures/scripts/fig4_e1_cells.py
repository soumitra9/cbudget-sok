"""Fig. 4: E1 interaction plot (RTK x compaction, PT outcome)."""

from __future__ import annotations

import json

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from common import BLUE, ORANGE, RESULTS_ROOT, apply_style, bootstrap_mean_ci, load_run_summary, save_figure, set_error_ylim


def main() -> None:
    apply_style()
    analysis = json.loads((RESULTS_ROOT / "e1" / "analysis.json").read_text(encoding="utf-8"))
    boot = analysis["raw_interaction_bootstrap"]
    rows = load_run_summary("e1")

    cell_values: dict[str, list[float]] = {}
    for row in rows:
        key = f"Y{int(row['rtk_on'])}{int(row['factor_b_on'])}"
        cell_values.setdefault(key, []).append(float(row["pt"]))

    def get_mean_errs(key: str) -> tuple[float, float, float]:
        mean, lo, hi = bootstrap_mean_ci(cell_values[key])
        return mean, mean - lo, hi - mean

    y00_mean, y00_elo, y00_ehi = get_mean_errs("Y00")
    y01_mean, y01_elo, y01_ehi = get_mean_errs("Y01")
    y10_mean, y10_elo, y10_ehi = get_mean_errs("Y10")
    y11_mean, y11_elo, y11_ehi = get_mean_errs("Y11")

    x = np.array([0, 1])
    fig, ax = plt.subplots(figsize=(3.5, 2.8))

    ax.plot(x, [y00_mean, y01_mean], "o-", color=BLUE, label="RTK off", linewidth=1.4, markersize=5)
    ax.errorbar(x, [y00_mean, y01_mean],
                yerr=[[y00_elo, y01_elo], [y00_ehi, y01_ehi]],
                fmt="none", ecolor=BLUE, capsize=3, linewidth=0.9)

    ax.plot(x, [y10_mean, y11_mean], "s--", color=ORANGE, label="RTK on", linewidth=1.4, markersize=5)
    ax.errorbar(x, [y10_mean, y11_mean],
                yerr=[[y10_elo, y11_elo], [y10_ehi, y11_ehi]],
                fmt="none", ecolor=ORANGE, capsize=3, linewidth=0.9)

    ax.set_xticks(x)
    ax.set_xticklabels(["Compaction off", "Compaction on"])
    ax.set_ylabel("Mean cumulative PT")
    ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f"{v / 1000:.0f}k"))
    set_error_ylim(
        ax,
        [y00_mean, y01_mean, y10_mean, y11_mean],
        [y00_elo, y01_elo, y10_elo, y11_elo],
        [y00_ehi, y01_ehi, y10_ehi, y11_ehi],
        ymin_floor=0.0,
    )
    ax.legend(frameon=False, loc="upper right", fontsize=6.5)
    ax.text(
        0.03, 0.05,
        f"$\\hat{{\\Delta}}={boot['point_estimate']:,.0f}$ PT\n"
        f"95% CI [{boot['ci_low']:,.0f},\u2009{boot['ci_high']:,.0f}]",
        transform=ax.transAxes, va="bottom", ha="left", fontsize=6,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="0.7", linewidth=0.5),
    )

    path = save_figure(fig, "Fig4.pdf")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
