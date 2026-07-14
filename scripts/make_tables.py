"""Generate paper tables from analysis results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True)
    args = parser.parse_args()
    results = Path(args.results)
    results.mkdir(parents=True, exist_ok=True)

    lines = ["# SoK Context Budget — Results Tables", ""]
    for name in ("e1", "e1b", "e0_anatomy"):
        path = results / name
        if path.exists():
            lines.append(f"## {name}")
            for csv_file in sorted(path.glob("*.csv")):
                lines.append(f"- {csv_file.name}")
            for json_file in sorted(path.glob("*.json")):
                data = json.loads(json_file.read_text(encoding="utf-8"))
                lines.append(f"- {json_file.name}: {json.dumps(data, indent=2)[:500]}")
            lines.append("")

    if (results / "c2_metrics.csv").exists():
        lines.append("## C2 metrics")
        lines.append("- c2_metrics.csv (documented)")
    if (results / "c4_temporal.csv").exists():
        lines.append("## C4 temporal")
        lines.append("- c4_temporal.csv (counterfactual_illustration)")

    out = results / "TABLES.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
