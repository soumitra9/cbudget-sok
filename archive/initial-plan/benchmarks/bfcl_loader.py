"""Loader for Berkeley Function Calling Leaderboard v4.

Expected local layout (matches Gorilla repo's BFCL data release):
  data_path/
    BFCL_v4_*.json           # one file per category (simple, multi_turn, live, ...)
    possible_answer/
      BFCL_v4_*.json         # ground truth for AST comparison

We only load the categories relevant to varying tool-set size (S) and
multi-turn context accumulation (H): 'multi_turn_base', 'multi_turn_*',
and 'live_*' categories. Single-turn 'simple' category is useful as a
sanity-check floor (S/H barely matter there; R shouldn't either) but is not
the primary evaluation surface for this paper.
"""
from __future__ import annotations

import json
from pathlib import Path

from allocators.types import TaskInstance
from .base import BenchmarkLoader


class BFCLLoader(BenchmarkLoader):
    name = "bfcl_v4"

    RELEVANT_CATEGORIES = (
        "multi_turn_base",
        "multi_turn_miss_func",
        "multi_turn_miss_param",
        "multi_turn_long_context",  # explicitly designed to stress context length -- priority target
        "live_multiple",
        "live_parallel_multiple",
    )

    def load(self, data_path: Path) -> list[TaskInstance]:
        instances: list[TaskInstance] = []
        for category in self.RELEVANT_CATEGORIES:
            f = data_path / f"BFCL_v4_{category}.json"
            if not f.exists():
                continue  # allow partial local datasets during development
            with open(f) as fh:
                for line in fh:  # BFCL data is JSONL
                    row = json.loads(line)
                    tools = row.get("function", row.get("tools", []))
                    turns = row.get("question", row.get("turns", []))
                    history = turns[:-1] if len(turns) > 1 else []
                    prompt = turns[-1] if turns else ""
                    instances.append(
                        TaskInstance(
                            task_id=f"bfcl:{category}:{row.get('id', len(instances))}",
                            source_benchmark=self.name,
                            prompt=str(prompt),
                            available_tools=tools,
                            history=history,
                            difficulty_proxy=self.estimate_difficulty(len(tools)),
                            metadata={"category": category},
                        )
                    )
        return instances
