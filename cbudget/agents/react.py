"""Standard ReAct policy."""

from __future__ import annotations

import json
import re

from cbudget.agent.state import AgentState
from cbudget.agents.base import AgentPolicy

TOOL_CALL_RE = re.compile(r"<tool_call>(.*?)</tool_call>", re.DOTALL)
FINAL_ANSWER_RE = re.compile(r"####\s*(.*)", re.DOTALL)
COMMAND_RE = re.compile(r'"command"\s*:\s*"((?:\\.|[^"\\])*)"')


_FORMAT_INSTRUCTIONS = """
To use the shell tool, respond with exactly this format:
Thought: <your reasoning>
<tool_call>{"name":"shell","arguments":{"command":"<shell command>"}}</tool_call>

When the task is fully complete, respond with:
#### <brief completion summary>

Shell environment rules:
- The shell is non-interactive (no TTY). Never use nano, vim, vi, or other interactive editors.
- Edit files with sed, printf/heredoc, cat <<'EOF', or python -c.
- Prefer one shell command per tool call.

Always use one of those two formats. Never respond with plain prose alone.""".strip()


class ReactPolicy(AgentPolicy):
    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    def system_prompt(self, base: str) -> str:
        return f"{base}\n\n{_FORMAT_INSTRUCTIONS}"

    def parse_response(self, text: str, state: AgentState) -> dict:
        tool_matches = list(TOOL_CALL_RE.finditer(text))
        if tool_matches:
            raw_payload = tool_matches[-1].group(1).strip()
            command = self._extract_command(raw_payload)
            if command is not None:
                return {"action": "tool", "command": command, "raw": text}
            return {"action": "parse_error", "raw": text}

        final_match = FINAL_ANSWER_RE.search(text)
        if final_match:
            return {"action": "final", "answer": final_match.group(1).strip(), "raw": text}

        return {"action": "parse_error", "raw": text}

    @staticmethod
    def _extract_command(raw_payload: str) -> str | None:
        try:
            payload = json.loads(raw_payload)
            command = payload.get("arguments", {}).get("command")
            if isinstance(command, str) and command:
                return command
        except json.JSONDecodeError:
            pass
        match = COMMAND_RE.search(raw_payload)
        if not match:
            return None
        try:
            return json.loads(f'"{match.group(1)}"')
        except json.JSONDecodeError:
            return match.group(1).encode("utf-8").decode("unicode_escape")
