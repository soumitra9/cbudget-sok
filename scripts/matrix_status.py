"""Live progress summary for factorial experiment matrices."""

from __future__ import annotations

import argparse
import itertools
import json
from enum import Enum
from pathlib import Path
from typing import Any

from cbudget.models.server_config import load_experiment_config, load_seeds, load_task_set
from cbudget.runner import PROJECT_ROOT, RUNS_ROOT, build_run_id, resolve_treatment
from cbudget.run_resume import load_status
from cbudget.state_machine import FailureState


DEFAULT_SEED_SETS = {
    "calibration_baseline": "seeds_smoke",
    "e1_rtk_compaction": "seeds_confirmatory_v1",
    "e1b_rtk_cod": "seeds_confirmatory_v1",
}

INFRA_FAILURES = {
    FailureState.INFRASTRUCTURE_ERROR.value,
    FailureState.MODEL_ERROR.value,
    FailureState.TOOL_RUNNER_FAILURE.value,
    FailureState.GRADER_ERROR.value,
    FailureState.COMPACTION_ENDPOINT_ERROR.value,
}


class RunStateLabel(str, Enum):
    PENDING = "pending"
    RESUME = "resume"
    SUCCESS = "success"
    FAILED = "failed"
    INFRA = "infra"


SYMBOL = {
    RunStateLabel.SUCCESS: "✓",
    RunStateLabel.FAILED: "✗",
    RunStateLabel.INFRA: "!",
    RunStateLabel.RESUME: "◐",
    RunStateLabel.PENDING: "○",
}


def _cell_sort_key(treatment: dict[str, Any]) -> tuple[int, int, str]:
    rtk = 0 if treatment.get("rtk") == "off" else 1
    if "compaction" in treatment:
        factor = 0 if treatment.get("compaction") == "off" else 1
        return (rtk, factor, "compaction")
    reasoning = 0 if treatment.get("reasoning", "standard") == "standard" else 1
    return (rtk, reasoning, "reasoning")


def expected_runs(
    experiment_id: str,
    *,
    task_set: str | None = None,
    seed_set: str | None = None,
    matrix: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    experiment = load_experiment_config(experiment_id)
    task_set = task_set or experiment.get("task_set", "coding_confirmatory_v1")
    seed_set = seed_set or DEFAULT_SEED_SETS.get(experiment_id, "seeds_confirmatory_v1")
    matrix = matrix if matrix is not None else experiment.get("matrix", {})

    tasks = load_task_set(task_set)["tasks"]
    seeds = load_seeds(seed_set)

    if matrix:
        keys = list(matrix.keys())
        values = [matrix[k] for k in keys]
        cells = [dict(zip(keys, combo)) for combo in itertools.product(*values)]
    else:
        cells = [{}]

    runs: list[dict[str, Any]] = []
    for task_id, seed, cell in itertools.product(tasks, seeds, cells):
        treatment = resolve_treatment(experiment, cell)
        run_id = build_run_id(experiment_id, task_id, seed, treatment)
        runs.append(
            {
                "run_id": run_id,
                "task_id": task_id,
                "seed": seed,
                "cell": cell,
                "treatment": treatment,
            }
        )
    return runs


def classify_run(run_dir: Path) -> RunStateLabel:
    status = load_status(run_dir)
    checkpoint = run_dir / "checkpoint.json"
    if status is None and not checkpoint.exists():
        return RunStateLabel.PENDING

    if status is not None:
        if status.get("task_success"):
            return RunStateLabel.SUCCESS
        failure = status.get("failure_state")
        if failure in INFRA_FAILURES or status.get("status") == "INFRASTRUCTURE_ERROR":
            return RunStateLabel.INFRA
        if failure or status.get("task_success") is False:
            return RunStateLabel.FAILED

    if checkpoint.exists():
        data = json.loads(checkpoint.read_text(encoding="utf-8"))
        if data.get("state_machine", {}).get("state") == "RUNNING":
            return RunStateLabel.RESUME

    return RunStateLabel.PENDING


def summarize_experiment(
    experiment_id: str,
    *,
    task_set: str | None = None,
    seed_set: str | None = None,
    runs_root: Path = RUNS_ROOT,
) -> dict[str, Any]:
    expected = expected_runs(experiment_id, task_set=task_set, seed_set=seed_set)
    counts = {label: 0 for label in RunStateLabel}
    run_rows: list[dict[str, Any]] = []

    for spec in expected:
        run_dir = runs_root / experiment_id / spec["run_id"]
        label = classify_run(run_dir)
        counts[label] += 1
        run_rows.append({**spec, "state": label.value, "symbol": SYMBOL[label]})

    blocks: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for row in run_rows:
        blocks.setdefault((row["task_id"], row["seed"]), []).append(row)

    block_lines: list[str] = []
    for (task_id, seed), rows in sorted(blocks.items()):
        ordered = sorted(rows, key=lambda row: _cell_sort_key(row["treatment"]))
        symbols = "".join(row["symbol"] for row in ordered)
        block_lines.append(f"  {task_id} x seed{seed:02d}: {symbols}")

    total = len(expected)
    complete = counts[RunStateLabel.SUCCESS]
    failed = counts[RunStateLabel.FAILED]
    infra = counts[RunStateLabel.INFRA]
    resume = counts[RunStateLabel.RESUME]
    pending = counts[RunStateLabel.PENDING]

    return {
        "experiment_id": experiment_id,
        "total": total,
        "complete": complete,
        "failed": failed,
        "infra": infra,
        "resume": resume,
        "pending": pending,
        "summary_line": (
            f"{experiment_id}: {complete}/{total} complete, "
            f"{failed} failed, {infra} infra, {resume} resume, {pending} pending"
        ),
        "block_lines": block_lines,
        "runs": run_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Show matrix run progress for an experiment.")
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--task-set", default=None)
    parser.add_argument("--seed-set", default=None)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    report = summarize_experiment(
        args.experiment,
        task_set=args.task_set,
        seed_set=args.seed_set,
    )

    if args.json:
        payload = {key: value for key, value in report.items() if key != "block_lines"}
        payload["blocks"] = report["block_lines"]
        print(json.dumps(payload, indent=2))
        return

    print(report["summary_line"])
    for line in report["block_lines"]:
        print(line)


if __name__ == "__main__":
    main()
