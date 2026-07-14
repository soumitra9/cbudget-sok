"""Single experiment runner."""

from __future__ import annotations

import argparse

from cbudget.models.server_config import load_task_set
from cbudget.runner import iter_runs, orchestrate_run
from scripts.run_cli import (
    add_orchestration_args,
    maybe_preflight,
    orchestrate_run_with_infra_retry,
    orchestration_kwargs,
)


def parse_kv_args(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in values:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a single cbudget experiment configuration.")
    parser.add_argument("kv", nargs="*", help="key=value overrides, e.g. experiment=calibration_baseline")
    add_orchestration_args(parser)
    args = parser.parse_args()
    overrides = parse_kv_args(args.kv)

    experiment_id = overrides.get("experiment", "calibration_baseline")
    task_set = overrides.get("task_set", "coding_calibration_v1")
    seed_set = overrides.get("seed_set", "seeds_smoke")

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


if __name__ == "__main__":
    main()
