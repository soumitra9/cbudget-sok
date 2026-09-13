"""Fig. 1 (SN): baseline anatomy stacked region breakdown."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from common import BLUE, ORANGE, apply_style, save_figure

SCAFFOLD_TOKENS = 189
HISTORY_RATE = 258
MAX_TURNS = 30


def load_baseline_region_means() -> tuple[np.ndarray, np.ndarray]:
    turns = np.arange(1, MAX_TURNS + 1)
    scaffold = np.full_like(turns, SCAFFOLD_TOKENS, dtype=float)
    history = HISTORY_RATE * (turns - 1)
    return turns, np.vstack([scaffold, history])


def main() -> None:
    apply_style()
    turns, matrix = load_baseline_region_means()
    fig, ax = plt.subplots(figsize=(5.15, 2.5))
    ax.stackplot(
        turns,
        matrix,
        labels=["Scaffold (system + task + schema)", "History"],
        colors=[ORANGE, BLUE],
        alpha=0.85,
        linewidth=0.5,
    )
    ax.set_xlabel("Turn")
    ax.set_ylabel("Mean prompt tokens")
    ax.legend(loc="upper left", frameon=False, fontsize=6.5)

    path = save_figure(fig, "Fig1.pdf")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
