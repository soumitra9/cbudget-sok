"""Task loading utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cbudget.models.server_config import load_task_config


@dataclass
class TaskSpec:
    task_id: str
    repository: str
    base_commit: str
    workspace_snapshot: str
    instruction_file: str
    grader_command: str
    grader_timeout: int
    allowed_tools: list[str]
    max_agent_turns: int
    max_model_calls: int
    max_wall_time_seconds: int
    network_access: bool
    fact_schema: str | None = None

    @classmethod
    def from_config(cls, task_id: str) -> "TaskSpec":
        cfg = load_task_config(task_id)
        grader = cfg.get("grader", {})
        return cls(
            task_id=cfg["task_id"],
            repository=cfg["repository"],
            base_commit=cfg["base_commit"],
            workspace_snapshot=cfg["workspace_snapshot"],
            instruction_file=cfg["instruction_file"],
            grader_command=grader.get("command", "true"),
            grader_timeout=int(grader.get("timeout_seconds", 300)),
            allowed_tools=list(cfg.get("allowed_tools", ["shell"])),
            max_agent_turns=int(cfg.get("max_agent_turns", 30)),
            max_model_calls=int(cfg.get("max_model_calls", 40)),
            max_wall_time_seconds=int(cfg.get("max_wall_time_seconds", 1800)),
            network_access=bool(cfg.get("network_access", False)),
            fact_schema=cfg.get("fact_schema"),
        )

    def read_instruction(self, root: Path) -> str:
        path = root / self.instruction_file
        if path.exists():
            return path.read_text(encoding="utf-8")
        return f"Complete task {self.task_id}."
