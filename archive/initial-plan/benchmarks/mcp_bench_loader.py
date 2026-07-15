"""Loader for MCP-Bench (arXiv:2508.20453).

This is the primary benchmark for varying |available_tools| (channel S)
independently of task difficulty, since it's built directly on real MCP
servers rather than a synthetic function-calling format.

Expected local layout: whatever the MCP-Bench repo/paper releases as its
task set -- confirm exact schema against the released artifact before
wiring this up for real; the field names below are a best-guess based on
the paper's task description and WILL need adjustment once the actual
data is in hand.
"""
from __future__ import annotations

import json
from pathlib import Path

from allocators.types import TaskInstance
from .base import BenchmarkLoader


class MCPBenchLoader(BenchmarkLoader):
    name = "mcp_bench"

    def load(self, data_path: Path) -> list[TaskInstance]:
        instances: list[TaskInstance] = []
        tasks_file = data_path / "tasks.json"
        if not tasks_file.exists():
            return instances  # dev-time no-op; see module docstring

        with open(tasks_file) as fh:
            raw_tasks = json.load(fh)

        for i, task in enumerate(raw_tasks):
            servers = task.get("mcp_servers", [])
            all_tools = [tool for server in servers for tool in server.get("tools", [])]
            instances.append(
                TaskInstance(
                    task_id=f"mcp_bench:{task.get('id', i)}",
                    source_benchmark=self.name,
                    prompt=task.get("instruction", ""),
                    available_tools=all_tools,
                    history=[],
                    difficulty_proxy=self.estimate_difficulty(
                        len(task.get("expected_tool_calls", []))
                    ),
                    metadata={
                        "num_servers": len(servers),
                        "domain": task.get("domain"),
                    },
                )
            )
        return instances
