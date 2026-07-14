"""Estimate 2x2 interaction effects with fixed blocking factors."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def load_runs(runs_dir: Path) -> pd.DataFrame:
    rows = []
    for run_dir in sorted(runs_dir.iterdir()):
        status_path = run_dir / "status.json"
        manifest_path = run_dir / "manifest.json"
        if not status_path.exists() or not manifest_path.exists():
            continue
        status = json.loads(status_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        treatment = manifest.get("treatment", {})
        rows.append(
            {
                "run_id": manifest.get("run_id", run_dir.name),
                "task_id": manifest.get("task_id"),
                "seed": manifest.get("seed"),
                "rtk": treatment.get("rtk", "off"),
                "factor_b": treatment.get("compaction", treatment.get("reasoning", "off")),
                "pt": status.get("total_serialized_pt", 0),
                "gt": status.get("total_gt", 0),
                "success": bool(status.get("task_success", False)),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    df = load_runs(Path(args.runs))
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "run_summary.csv", index=False)

    if df.empty:
        print("No runs found.")
        return

    pivot = df.groupby(["rtk", "factor_b"])["pt"].mean().unstack(fill_value=np.nan)
    pivot.to_csv(out / "cell_means_pt.csv")
    print(f"Wrote summaries to {out}")


if __name__ == "__main__":
    main()
