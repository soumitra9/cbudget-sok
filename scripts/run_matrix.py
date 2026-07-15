"""Factorial matrix runner for E1 / E1b."""

from __future__ import annotations

import argparse
import itertools
import random

from cbudget.runner import build_run_id, orchestrate_run, resolve_treatment
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
            print(f"{run_id}: success={result.get('task_success')} pt={result.get('total_serialized_pt')}")


if __name__ == "__main__":
    main()
