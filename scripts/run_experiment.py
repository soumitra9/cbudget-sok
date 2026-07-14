"""Single experiment runner."""

from __future__ import annotations

import argparse

from cbudget.runner import execute_run, iter_runs


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
    args = parser.parse_args()
    overrides = parse_kv_args(args.kv)

    experiment_id = overrides.get("experiment", "calibration_baseline")
    task_set = overrides.get("task_set", "coding_calibration_v1")
    seed_set = overrides.get("seed_set", "seeds_smoke")

    for _, task_id, seed, treatment, run_id in iter_runs(experiment_id, task_set, seed_set):
        result = execute_run(experiment_id, task_id, seed, treatment, run_id)
        print(f"{run_id}: success={result.get('task_success')} pt={result.get('total_serialized_pt')}")


if __name__ == "__main__":
    main()
