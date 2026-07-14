"""Load model and environment YAML configs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

CONFIG_ROOT = Path(__file__).resolve().parents[2] / "configs"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data or {}


def resolve_config(*parts: str) -> Path:
    return CONFIG_ROOT.joinpath(*parts)


def load_model_config(name: str = "qwen2.5_7b_instruct") -> dict[str, Any]:
    return load_yaml(resolve_config("models", f"{name}.yaml"))


def load_experiment_config(experiment_id: str) -> dict[str, Any]:
    return load_yaml(resolve_config("experiments", f"{experiment_id}.yaml"))


def load_task_config(task_id: str) -> dict[str, Any]:
    return load_yaml(resolve_config("tasks", f"{task_id}.yaml"))


def load_task_set(task_set_id: str) -> dict[str, Any]:
    return load_yaml(resolve_config("tasks", f"{task_set_id}.yaml"))


def load_policy(name: str) -> dict[str, Any]:
    return load_yaml(resolve_config("policies", f"react_{name}.yaml"))


def load_intervention(kind: str, variant: str) -> dict[str, Any]:
    return load_yaml(resolve_config("interventions", f"{kind}_{variant}.yaml"))


def load_seeds(seed_set: str) -> list[int]:
    data = load_yaml(resolve_config("seeds", f"{seed_set}.yaml"))
    return list(data.get("seeds", []))
