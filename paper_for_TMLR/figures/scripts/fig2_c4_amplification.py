"""Fig. 2: C4 temporal amplification (counterfactual)."""

from __future__ import annotations

import csv

import matplotlib.pyplot as plt

from common import BLUE, GREEN, ORANGE, RESULTS_ROOT, apply_style, save_figure


def main() -> None:
    apply_style()
    rows = list(csv.DictReader((RESULTS_ROOT / "c4_temporal.csv").open(encoding="utf-8")))
    scenarios: dict[str, list[tuple[int, float]]] = {}
    base = None
    gamma = None
    for row in rows:
        if row["method"] != "TokenSkip":
            continue
        base = float(row["base_tokens"])
        gamma = float(row["gamma"])
        scenarios.setdefault(row["retention_scenario"], []).append(
            (int(row["turns"]), float(row["amplified_tokens"]))
        )

    style_map = {
        "full":            ("-",  BLUE,   "Full retention"),
        "final_only":      ("--", ORANGE, "Final turn only"),
        "hidden_reasoning":("-.", GREEN,  "Hidden reasoning"),
    }

    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    for scenario, (ls, color, label) in style_map.items():
        if scenario not in scenarios:
            continue
        pts = sorted(scenarios[scenario])
        xs, ys = zip(*pts)
        ax.plot(xs, ys, linestyle=ls, color=color, linewidth=1.4, label=label)

    ax.set_xlabel("Session turns ($T$)")
    ax.set_ylabel("Simulated cumulative PT")
    ax.legend(frameon=False, loc="upper left", fontsize=6.5)

    path = save_figure(fig, "Fig3.pdf")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
