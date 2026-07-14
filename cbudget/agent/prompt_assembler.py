"""Render prompts with region tags for token accounting."""

from __future__ import annotations

from cbudget.agent.state import AgentState


class PromptAssembler:
    def render(self, state: AgentState) -> str:
        parts: list[str] = []
        parts.append(f"[system]\n{state.system_prompt}")
        parts.append(f"[task]\n{state.task_instruction}")
        parts.append(f"[tool_schema]\n{state.tool_schema}")
        if state.compacted_summary:
            parts.append(f"[compacted_summary]\n{state.compacted_summary}")
        for message in state.messages:
            parts.append(f"[{message.role}]\n{message.content}")
        return "\n\n".join(parts)

    def regions(self, state: AgentState) -> dict[str, int]:
        return {
            "system": len(state.system_prompt.split()),
            "task": len(state.task_instruction.split()),
            "tool_schema": len(state.tool_schema.split()),
            "history": sum(len(m.content.split()) for m in state.messages),
            "compacted_summary": len((state.compacted_summary or "").split()),
        }
