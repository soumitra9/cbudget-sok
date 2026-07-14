"""Factorial matrix runner for E1 / E1b."""

from __future__ import annotations

import argparse
import itertools

from cbudget.runner import build_run_id, iter_runs, orchestrate_run, resolve_treatment
from cbudget.models.server_config import load_experiment_config, load_seeds, load_task_set
from scripts.run_cli import add_orchestration_args, maybe_preflight, orchestration_kwargs


def _parse_matrix_value(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a factorial matrix experiment.")
    parser.add_argument("kv", nargs="*", help="experiment=e1_rtk_compaction rtk=off,on compaction=off,on")
    add_orchestration_args(parser)
    args = parser.parse_args()
    maybe_preflight(args)
    orch = orchestration_kwargs(args)

    overrides: dict[str, str] = {}
    for item in args.kv:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        overrides[key.strip()] = value.strip()

    experiment_id = overrides.pop("experiment", "e1_rtk_compaction")
    task_set = overrides.pop("task_set", "coding_confirmatory_v1")
    seed_set = overrides.pop("seed_set", "seeds_confirmatory_v1")

    matrix = {key: _parse_matrix_value(value) for key, value in overrides.items()}
    experiment = load_experiment_config(experiment_id)

    tasks = load_task_set(task_set)["tasks"]
    seeds = load_seeds(seed_set)
    keys = list(matrix.keys())
    values = [matrix[k] for k in keys]
    cells = [dict(zip(keys, combo)) for combo in itertools.product(*values)]

    for task_id, seed, cell in itertools.product(tasks, seeds, cells):
        treatment = resolve_treatment(experiment, cell)
        run_id = build_run_id(experiment_id, task_id, seed, treatment)
        result = orchestrate_run(experiment_id, task_id, seed, treatment, run_id, **orch)
        print(f"{run_id}: success={result.get('task_success')} pt={result.get('total_serialized_pt')}")


if __name__ == "__main__":
    main()
