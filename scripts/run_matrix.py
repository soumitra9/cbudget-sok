"""Factorial matrix runner for E1 / E1b."""

from __future__ import annotations

import argparse
import itertools
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from cbudget.runner import PROJECT_ROOT, build_run_id, orchestrate_run, resolve_treatment
from cbudget.models.server_config import load_experiment_config, load_seeds, load_task_set
from scripts.run_cli import (
    add_orchestration_args,
    maybe_preflight,
    orchestrate_run_with_infra_retry,
    orchestration_kwargs,
)


def _parse_matrix_value(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


YAML_BOOL_TO_STR = {True: "on", False: "off"}
MATRIX_LOG_DIR = PROJECT_ROOT / "results" / "matrix_logs"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log_matrix_cell(log_path: Path, *, experiment_id: str, run_id: str, result: dict) -> None:
    entry = {
        "timestamp": _utc_now(),
        "experiment_id": experiment_id,
        "run_id": run_id,
        **result,
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")
        handle.flush()


def _write_matrix_summary(
    summary_path: Path,
    *,
    experiment_id: str,
    results: list[dict],
) -> None:
    success = sum(1 for row in results if row.get("task_success"))
    infra = sum(1 for row in results if row.get("status") == "INFRASTRUCTURE_ERROR")
    summary = {
        "experiment_id": experiment_id,
        "finished_at": _utc_now(),
        "n_cells": len(results),
        "n_success": success,
        "n_infra_error": infra,
        "cells": results,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def _normalize_matrix(matrix: dict) -> dict[str, list[str]]:
    return {
        key: [YAML_BOOL_TO_STR.get(v, str(v)) for v in vals]
        for key, vals in matrix.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a factorial matrix experiment.")
    parser.add_argument("kv", nargs="*", help="experiment=e1_rtk_compaction rtk=off,on compaction=off,on")
    add_orchestration_args(parser)
    args = parser.parse_args()

    overrides: dict[str, str] = {}
    for item in args.kv:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        overrides[key.strip()] = value.strip()

    experiment_id = overrides.pop("experiment", "e1_rtk_compaction")
    task_set = overrides.pop("task_set", "coding_confirmatory_v1")
    seed_set = overrides.pop("seed_set", "seeds_confirmatory_v1")

    tasks = load_task_set(task_set)["tasks"]
    maybe_preflight(args, task_ids=tasks)
    orch = orchestration_kwargs(args)

    matrix = {key: _parse_matrix_value(value) for key, value in overrides.items() if key in {"rtk", "compaction", "reasoning"}}
    experiment = load_experiment_config(experiment_id)
    if not matrix and "matrix" in experiment:
        matrix = experiment["matrix"]
    matrix = _normalize_matrix(matrix)

    seeds = load_seeds(seed_set)
    keys = list(matrix.keys())
    values = [matrix[k] for k in keys]
    cells = [dict(zip(keys, combo)) for combo in itertools.product(*values)]

    log_path = MATRIX_LOG_DIR / f"{experiment_id}.jsonl"
    summary_path = MATRIX_LOG_DIR / f"{experiment_id}_summary.json"
    cell_results: list[dict] = []

    print(f"Matrix log: {log_path}", flush=True)
    for task_id, seed in itertools.product(tasks, seeds):
        block_cells = list(cells)
        rng = random.Random(f"{experiment_id}:{task_id}:{seed}")
        rng.shuffle(block_cells)
        for cell in block_cells:
            treatment = resolve_treatment(experiment, cell)
            run_id = build_run_id(experiment_id, task_id, seed, treatment)
            result = orchestrate_run_with_infra_retry(
                orchestrate_run,
                run_id=run_id,
                experiment_id=experiment_id,
                task_id=task_id,
                seed=seed,
                treatment=treatment,
                **orch,
            )
            row = {
                "task_id": task_id,
                "seed": seed,
                "treatment": cell,
                "task_success": result.get("task_success"),
                "status": result.get("status"),
                "total_serialized_pt": result.get("total_serialized_pt"),
                "failure_state": result.get("failure_state"),
            }
            cell_results.append({"run_id": run_id, **row})
            _log_matrix_cell(log_path, experiment_id=experiment_id, run_id=run_id, result=row)
            print(
                f"{run_id}: success={result.get('task_success')} pt={result.get('total_serialized_pt')}",
                flush=True,
            )

    _write_matrix_summary(summary_path, experiment_id=experiment_id, results=cell_results)
    print(f"Matrix summary: {summary_path}", flush=True)


if __name__ == "__main__":
    main()
