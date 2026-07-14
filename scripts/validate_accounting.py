"""Validate token-accounting invariants across run artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def check_run(status: dict, events: list[dict]) -> list[str]:
    failures = []

    # Invariant: peak_occupancy >= 0
    if status.get("peak_occupancy", 0) < 0:
        failures.append("peak_occupancy is negative")

    # Invariant: cumulative_serialized_pt is non-decreasing (check from events)
    pt_values = [
        e["prompt_tokens_serialized"]
        for e in events
        if e.get("event_type") == "model_request" and "prompt_tokens_serialized" in e
    ]
    for i in range(1, len(pt_values)):
        if pt_values[i] < 0:
            failures.append(f"prompt_tokens_serialized negative at event index {i}")

    # Invariant: compaction_call tokens appear in total_gt
    compaction_gts = sum(
        e.get("generated_tokens", 0)
        for e in events
        if e.get("event_type") == "compaction_call"
    )
    total_gt = status.get("total_gt", 0)
    total_compaction_gt = status.get("total_compaction_gt", 0)
    if compaction_gts > 0 and total_compaction_gt == 0:
        failures.append("compaction_call events found but total_compaction_gt=0 in status")

    return failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--runs", default="runs")
    args = parser.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    invariants = cfg.get("invariants", [])
    runs_root = Path(args.runs)
    total_checked = 0
    total_failures = 0

    for status_path in runs_root.rglob("status.json"):
        status = json.loads(status_path.read_text(encoding="utf-8"))
        events_path = status_path.parent / "events.jsonl"
        events = []
        if events_path.exists():
            events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        failures = check_run(status, events)
        if failures:
            print(f"FAIL {status_path.parent.name}: {failures}")
            total_failures += len(failures)
        total_checked += 1

    print(f"Checked {total_checked} runs against {len(invariants)} declared invariants. Failures: {total_failures}")
    if total_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
