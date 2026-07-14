"""Standard ReAct policy."""

from __future__ import annotations

import json
import re

from cbudget.agent.state import AgentState
from cbudget.agents.base import AgentPolicy

TOOL_CALL_RE = re.compile(r"<tool_call>(.*?)</tool_call>", re.DOTALL)
FINAL_ANSWER_RE = re.compile(r"####\s*(.*)", re.DOTALL)


class ReactPolicy(AgentPolicy):
    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    def system_prompt(self, base: str) -> str:
        return base

    def parse_response(self, text: str, state: AgentState) -> dict:
        tool_match = TOOL_CALL_RE.search(text)
        if tool_match:
            payload = json.loads(tool_match.group(1).strip())
            command = payload.get("arguments", {}).get("command", "")
            return {"action": "tool", "command": command, "raw": text}

        final_match = FINAL_ANSWER_RE.search(text)
        if final_match:
            return {"action": "final", "answer": final_match.group(1).strip(), "raw": text}

        return {"action": "parse_error", "raw": text}
