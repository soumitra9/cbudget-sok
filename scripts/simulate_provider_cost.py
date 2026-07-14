"""Post-hoc provider billing simulation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", required=True)
    parser.add_argument("--price-table", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    prices = yaml.safe_load(Path(args.price_table).read_text(encoding="utf-8"))
    rows = []
    for status_path in Path(args.runs).rglob("status.json"):
        status = json.loads(status_path.read_text(encoding="utf-8"))
        pt = status.get("total_serialized_pt", 0)
        gt = status.get("total_gt", 0)
        rate = prices["providers"]["anthropic_counterfactual"]
        cost = (pt / 1_000_000) * rate["input_per_mtok"] + (gt / 1_000_000) * rate["output_per_mtok"]
        rows.append({"run_id": status_path.parent.name, "simulated_cost_usd": round(cost, 4)})

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} cost rows to {out}")


if __name__ == "__main__":
    main()
