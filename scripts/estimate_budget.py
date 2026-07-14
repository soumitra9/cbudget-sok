"""Budget estimator from pilot runtime CSV."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot-results", required=True)
    parser.add_argument("--planned-runs", type=int, required=True)
    parser.add_argument("--gpu-hour-rate", type=float, default=0.90)
    args = parser.parse_args()

    minutes = []
    with Path(args.pilot_results).open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            minutes.append(float(row.get("wall_minutes", 0)))

    if not minutes:
        print("No pilot data; cannot estimate.")
        return

    median = sorted(minutes)[len(minutes) // 2]
    hours = args.planned_runs * (median / 60.0) * 1.15
    cost = hours * args.gpu_hour_rate
    print(f"median_session_min={median:.2f} planned_runs={args.planned_runs} est_gpu_hours={hours:.2f} est_cost_usd={cost:.2f}")


if __name__ == "__main__":
    main()
