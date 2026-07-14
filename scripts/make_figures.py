"""Generate figures from analysis results (CSV summaries)."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True)
    args = parser.parse_args()
    results = Path(args.results)
    fig_dir = results / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    anatomy = results / "e0_anatomy" / "region_breakdown.csv"
    if anatomy.exists():
        rows = list(csv.DictReader(anatomy.open(encoding="utf-8")))
        svg = ["<svg xmlns='http://www.w3.org/2000/svg' width='600' height='300'>"]
        for i, row in enumerate(rows[:6]):
            val = float(row.get("mean_pt", 0) or 0)
            h = min(200, val / 50)
            svg.append(f"<rect x='{40 + i*80}' y='{250-h}' width='60' height='{h}' fill='#4472C4'/>")
            svg.append(f"<text x='{50 + i*80}' y='270' font-size='10'>{row.get('cell','')}</text>")
        svg.append("</svg>")
        (fig_dir / "e0_region_breakdown.svg").write_text("\n".join(svg), encoding="utf-8")

    manifest = fig_dir / "FIGURES.md"
    manifest.write_text("# Figures\n\n- e0_region_breakdown.svg (if anatomy data present)\n", encoding="utf-8")
    print(f"Wrote figures to {fig_dir}")


if __name__ == "__main__":
    main()
