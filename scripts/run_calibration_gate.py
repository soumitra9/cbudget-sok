"""Stage 3 calibration runner with go/no-go gate."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

import yaml

from cbudget.models.server_config import load_experiment_config, load_task_set
from cbudget.runner import iter_runs, orchestrate_run
from scripts.run_cli import (
    add_orchestration_args,
    maybe_preflight,
    orchestrate_run_with_infra_retry,
    orchestration_kwargs,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS = PROJECT_ROOT / "results"


def evaluate_gate(runs_dir: Path, task_set_cfg: dict) -> dict:
    gate = task_set_cfg.get("go_no_go", {})
    statuses = [p for p in runs_dir.rglob("status.json") if ".attempt" not in str(p)]
    if not statuses:
        return {"pass": False, "reason": "no runs found"}

    total = len(statuses)
    successes = 0
    parser_errors = 0
    compaction_fires = 0
    compaction_runs = 0

    for path in statuses:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("task_success"):
            successes += 1
        sm = data.get("state_machine", {})
        if sm.get("failure_state") == "PARSER_ERROR":
            parser_errors += 1
        events = path.parent / "events.jsonl"
        if events.exists():
            text = events.read_text(encoding="utf-8")
            if "compaction_completed" in text:
                compaction_fires += 1
            # Only count runs where compaction treatment was enabled.
            manifest_path = path.parent / "manifest.json"
            compaction_on = False
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                compaction_on = manifest.get("treatment", {}).get("compaction") not in (None, "off", False)
            if compaction_on:
                compaction_runs += 1

    baseline_rate = successes / total if total else 0.0
    parser_rate = parser_errors / total if total else 0.0
    compaction_rate = compaction_fires / compaction_runs if compaction_runs else 0.0

    checks = {
        "baseline_success_rate": baseline_rate >= gate.get("minimum_baseline_success_rate", 0.70),
        "parser_error_rate": parser_rate <= gate.get("maximum_parser_error_rate", 0.20),
        "compaction_fire_rate": compaction_rate >= gate.get("minimum_compaction_fire_rate", 0.30) if compaction_runs else True,
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "baseline_success_rate": baseline_rate,
        "parser_error_rate": parser_rate,
        "compaction_fire_rate": compaction_rate,
        "n_runs": total,
        "backend": os.environ.get("CBUDGET_BACKEND", "mock"),
        "note": "Mock-backend gate results are not valid for go/no-go; re-run with CBUDGET_BACKEND=vllm.",
    }


def write_pilot_csv(runs_dir: Path, output: Path) -> None:
    rows = []
    for status_path in [p for p in runs_dir.rglob("status.json") if ".attempt" not in str(p)]:
        data = json.loads(status_path.read_text(encoding="utf-8"))
        rows.append(
            {
                "run_id": status_path.parent.name,
                "task_success": data.get("task_success"),
                "total_serialized_pt": data.get("total_serialized_pt"),
                "total_gt": data.get("total_gt"),
                "peak_occupancy": data.get("peak_occupancy"),
            }
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["run_id"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="Run smoke matrix only")
    parser.add_argument("--pilot", action="store_true", help="Run pilot matrix")
    add_orchestration_args(parser)
    args = parser.parse_args()

    experiment_id = "calibration_baseline"
    task_set = "coding_calibration_v1"
    seed_set = "seeds_smoke"

    os.environ["CBUDGET_MODEL_CONFIG"] = load_experiment_config(experiment_id).get(
        "model", "qwen2.5_7b_instruct"
    )

    tasks = load_task_set(task_set)["tasks"]
    maybe_preflight(args, task_ids=tasks)
    orch = orchestration_kwargs(args)

    for _, task_id, seed, treatment, run_id in iter_runs(experiment_id, task_set, seed_set):
        result = orchestrate_run_with_infra_retry(
            orchestrate_run,
            run_id=run_id,
            experiment_id=experiment_id,
            task_id=task_id,
            seed=seed,
            treatment=treatment,
            **orch,
        )
        print(f"{run_id}: success={result.get('task_success')} pt={result.get('total_serialized_pt')}")

    runs_dir = PROJECT_ROOT / "runs" / experiment_id
    write_pilot_csv(runs_dir, RESULTS / "pilot_runtime.csv")

    task_set_cfg = yaml.safe_load((PROJECT_ROOT / "configs/tasks/coding_calibration_v1.yaml").read_text())
    gate = evaluate_gate(runs_dir, task_set_cfg)
    (RESULTS / "calibration_gate.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
    print(json.dumps(gate, indent=2))
    if not gate["pass"]:
        raise SystemExit("Go/no-go gate FAILED")


if __name__ == "__main__":
    main()
