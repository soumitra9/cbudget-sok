"""Fig. 1: taxonomy intervention-point diagram."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from common import BLUE, BROWN, GREEN, ORANGE, PURPLE, RED, apply_style, save_figure


def main() -> None:
    apply_style()
    fig, ax = plt.subplots(figsize=(5.1, 2.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")

    categories = [
        ("1: Schema\nprovisioning", ["RAG-MCP", "MCP-Zero"], BLUE),
        ("2: Output\nfiltering", ["RTK"], ORANGE),
        ("3: Context\ncompression", ["Headroom", "lean-ctx", "Compaction"], GREEN),
        ("4: Reasoning\ncompression", ["TokenSkip", "CoD", "SEER"], RED),
        ("5: Behavioral\nprevention", ["Ponytail", "karpathy-skills"], PURPLE),
    ]
    xs = [1.0, 3.0, 5.0, 7.0, 9.0]
    for x, (title, methods, color) in zip(xs, categories):
        box = FancyBboxPatch(
            (x - 0.75, 2.2), 1.5, 1.0,
            boxstyle="round,pad=0.05", linewidth=1.0,
            facecolor=color, edgecolor=color, alpha=0.25,
        )
        ax.add_patch(box)
        ax.text(x, 2.7, title, ha="center", va="center", fontsize=7, color="#111111")
        for i, method in enumerate(methods):
            ax.text(x, 1.5 - 0.35 * i, method, ha="center", va="center", fontsize=6.5)

    ax.annotate("", xy=(9.3, 3.5), xytext=(0.7, 3.5),
                arrowprops=dict(arrowstyle="->", linewidth=1.0, color=BROWN))
    ax.text(5.0, 3.75, "Representative intervention locations across the agent lifecycle",
            ha="center", va="center", fontsize=8)
    for i, (x, (_, methods, _)) in enumerate(zip(xs, categories)):
        pop_labels = ["schemas", "tool output", "any prior content", "CoT tokens", "GT tokens"]
        ax.text(x, 0.35, pop_labels[i], ha="center", va="center",
                fontsize=7, style="italic", color="#555555")

    path = save_figure(fig, "Fig2.pdf")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
