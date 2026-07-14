"""E0 anatomy analysis over E1 traces."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

CELL_MAP = {
    "baseline": {"rtk": "off", "compaction": "off"},
    "compaction_only": {"rtk": "off", "compaction": "on"},
}


def _matches_cell(manifest: dict, spec: dict) -> bool:
    treatment = manifest.get("treatment", {})
    return treatment.get("rtk") == spec["rtk"] and treatment.get("compaction") == spec["compaction"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", required=True)
    parser.add_argument("--cells", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    runs_dir = Path(args.runs)
    selected_cells = [c.strip() for c in args.cells.split(",")]
    summaries = []
    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir() or ".attempt" in run_dir.name:
            continue
        status_path = run_dir / "status.json"
        manifest_path = run_dir / "manifest.json"
        if not status_path.exists() or not manifest_path.exists():
            continue
        status = json.loads(status_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for cell in selected_cells:
            spec = CELL_MAP.get(cell)
            if spec and _matches_cell(manifest, spec):
                summaries.append(
                    {
                        "cell": cell,
                        "run_id": run_dir.name,
                        "mean_pt": status.get("total_serialized_pt", 0),
                        "mean_gt": status.get("total_gt", 0),
                        "peak_occupancy": status.get("peak_occupancy", 0),
                        "task_success": status.get("task_success"),
                    }
                )
                break

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "anatomy.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")

    if summaries:
        with (out / "region_breakdown.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(summaries[0].keys()))
            writer.writeheader()
            writer.writerows(summaries)

    print(f"Wrote {len(summaries)} anatomy records to {out}")


if __name__ == "__main__":
    main()
