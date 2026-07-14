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

    def to_chat_messages(self, state: AgentState) -> list[dict[str, str]]:
        system_parts = [
            state.system_prompt,
            state.task_instruction,
            f"Available tools:\n{state.tool_schema}",
        ]
        if state.compacted_summary:
            system_parts.append(f"Previous summary:\n{state.compacted_summary}")
        messages: list[dict[str, str]] = [{"role": "system", "content": "\n\n".join(system_parts)}]
        for message in state.messages:
            if message.role == "assistant":
                messages.append({"role": "assistant", "content": message.content})
            elif message.role == "tool":
                messages.append({"role": "user", "content": f"[tool output]\n{message.content}"})
            else:
                messages.append({"role": message.role, "content": message.content})
        return messages
