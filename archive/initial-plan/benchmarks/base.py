"""Base interface for benchmark loaders.

Each loader normalizes its native format into allocators.types.TaskInstance
so the allocation/evaluation loop never needs benchmark-specific branching.

NOTE: none of these loaders ship the actual benchmark data (licenses/repo
access vary). Each `load()` expects a local path to the benchmark's own
released data and documents exactly what file layout it expects. Fetch the
real datasets separately:
  - BFCL v4:    https://github.com/ShishirPatil/gorilla (berkeley-function-call-leaderboard)
  - MCP-Bench:  arXiv:2508.20453 (check paper/repo for released task set)
  - tau-bench:  https://github.com/sierra-research/tau-bench
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from allocators.types import TaskInstance


class BenchmarkLoader(ABC):
    name: str

    @abstractmethod
    def load(self, data_path: Path) -> list[TaskInstance]:
        """Return a list of normalized TaskInstance objects."""
        raise NotImplementedError

    @staticmethod
    def estimate_difficulty(num_required_tool_calls: int) -> float:
        """Shared difficulty proxy used consistently across loaders so the
        bandit allocator's task-type bucketing (easy/medium/hard) means the
        same thing regardless of source benchmark."""
        return float(num_required_tool_calls)
