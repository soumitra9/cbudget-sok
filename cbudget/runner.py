"""Shared run orchestration helpers."""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any

from cbudget.agent.loop import AgentLoop, RunConfig
from cbudget.models.server_config import (
    load_experiment_config,
    load_intervention,
    load_policy,
    load_seeds,
    load_task_set,
)
from cbudget.state_machine import RunState, StateMachine
from cbudget.tasks.base import TaskSpec


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = PROJECT_ROOT / "runs"


def build_run_id(experiment_id: str, task_id: str, seed: int, treatment: dict[str, Any]) -> str:
    rtk = "rtk1" if treatment.get("rtk") == "on" else "rtk0"
    compaction = treatment.get("compaction", "off")
    reasoning = treatment.get("reasoning", "standard")
    return f"{experiment_id}-{task_id}-seed{seed:02d}-{rtk}-{compaction}-{reasoning}"


def resolve_treatment(experiment: dict[str, Any], overrides: dict[str, str]) -> dict[str, Any]:
    treatment: dict[str, Any] = {}
    rtk = overrides.get("rtk", "off")
    compaction = overrides.get("compaction", "off")
    reasoning = overrides.get("reasoning", experiment.get("reasoning", "standard"))

    treatment["rtk"] = rtk
    treatment["compaction"] = compaction
    treatment["reasoning"] = reasoning

    rtk_cfg = load_intervention("rtk", "on" if rtk == "on" else "off")
    binary = rtk_cfg.get("rtk_binary", "rtk")
    if not Path(binary).is_absolute():
        binary = str(PROJECT_ROOT / binary)
    treatment["rtk_binary"] = binary

    compact_cfg: dict[str, Any] = {}
    if compaction == "off":
        load_intervention("compaction", "off")
    elif compaction == "tau_alt":
        compact_cfg = load_intervention("compaction", "tau_alt")
    else:
        compact_cfg = load_intervention("compaction", "default")

    treatment["compaction_trigger"] = compact_cfg.get("trigger_tokens")
    treatment["summary_prompt"] = compact_cfg.get("summary_prompt", "")
    treatment["hot_tail_tokens"] = compact_cfg.get("hot_tail_tokens", 2000)
    treatment["max_summary_tokens"] = compact_cfg.get("max_summary_tokens", 1024)
    treatment["compaction_temperature"] = compact_cfg.get("temperature", 0.0)
    treatment["recursion_enabled"] = compact_cfg.get("recursion_enabled", True)

    policy_name = "cod" if reasoning == "cod" else "standard"
    treatment["policy_config"] = load_policy(policy_name)
    return treatment


def iter_runs(experiment_id: str, task_set: str, seed_set: str, matrix: dict[str, list[str]] | None = None):
    experiment = load_experiment_config(experiment_id)
    tasks = load_task_set(task_set)["tasks"]
    seeds = load_seeds(seed_set)

    if matrix:
        keys = list(matrix.keys())
        values = [matrix[k] for k in keys]
        cells = [dict(zip(keys, combo)) for combo in itertools.product(*values)]
    else:
        cells = [{}]

    for task_id, seed, cell in itertools.product(tasks, seeds, cells):
        treatment = resolve_treatment(experiment, cell)
        run_id = build_run_id(experiment_id, task_id, seed, treatment)
        yield experiment_id, task_id, seed, treatment, run_id


def execute_run(experiment_id: str, task_id: str, seed: int, treatment: dict[str, Any], run_id: str) -> dict:
    run_dir = RUNS_ROOT / experiment_id / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    task = TaskSpec.from_config(task_id)
    sm = StateMachine(run_id=run_id)
    sm.transition(RunState.CREATED)
    loop = AgentLoop(
        RunConfig(
            experiment_id=experiment_id,
            run_id=run_id,
            task_id=task_id,
            seed=seed,
            treatment=treatment,
            run_dir=run_dir,
            project_root=PROJECT_ROOT,
        ),
        task,
        state_machine=sm,
    )
    return loop.run()
