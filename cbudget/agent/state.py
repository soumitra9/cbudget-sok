"""Agent state and message types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentState:
    task_instruction: str
    system_prompt: str
    tool_schema: str
    messages: list[Message] = field(default_factory=list)
    compacted_summary: str | None = None
    task_fact_schema: list[dict[str, Any]] = field(default_factory=list)
    turn: int = 0
    done: bool = False
    success: bool | None = None

    @property
    def fixed_scaffolding(self) -> dict[str, str]:
        return {
            "system": self.system_prompt,
            "tool_schema": self.tool_schema,
        }
