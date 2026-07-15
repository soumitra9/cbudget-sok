"""Loader for tau-bench (Yao et al., arXiv:2406.12045) -- retail/airline
domains -- and, if available locally, tau2-bench's telecom extension.

tau-bench is the primary source for channel R (reasoning) signal: success
requires multi-turn policy compliance, not just correct tool invocation, so
it's the benchmark where cutting reasoning tokens too aggressively should
show up as a measurable accuracy drop (unlike BFCL single-turn categories,
where it may not).

IMPORTANT: verify tau2-bench's exact citation/release details directly
before relying on it in the paper -- flagged as unconfirmed in the
related-work doc. Do not cite it beyond "Sierra Research, description per
public sources" until pinned down.

Expected local layout: matches sierra-research/tau-bench repo's env task
format (envs/retail/data, envs/airline/data).
"""
from __future__ import annotations

import json
from pathlib import Path

from allocators.types import TaskInstance
from .base import BenchmarkLoader


class TauBenchLoader(BenchmarkLoader):
    name = "tau_bench"

    def __init__(self, domain: str = "retail") -> None:
        assert domain in ("retail", "airline"), "tau-bench ships retail/airline domains"
        self.domain = domain

    def load(self, data_path: Path) -> list[TaskInstance]:
        instances: list[TaskInstance] = []
        tasks_file = data_path / self.domain / "tasks.json"
        tools_file = data_path / self.domain / "tools.json"
        if not tasks_file.exists() or not tools_file.exists():
            return instances

        with open(tools_file) as fh:
            tools = json.load(fh)
        with open(tasks_file) as fh:
            raw_tasks = json.load(fh)

        for i, task in enumerate(raw_tasks):
            instances.append(
                TaskInstance(
                    task_id=f"tau_bench:{self.domain}:{task.get('id', i)}",
                    source_benchmark=self.name,
                    prompt=task.get("instruction", ""),
                    available_tools=tools,
                    history=[],
                    difficulty_proxy=self.estimate_difficulty(
                        len(task.get("actions", []))
                    ),
                    metadata={"domain": self.domain, "policy": task.get("policy_id")},
                )
            )
        return instances
