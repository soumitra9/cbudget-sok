"""Render prompts with region tags for token accounting."""

from __future__ import annotations

from cbudget.accounting.occupancy import count_tokens
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
            "system": count_tokens(state.system_prompt),
            "task": count_tokens(state.task_instruction),
            "tool_schema": count_tokens(state.tool_schema),
            "history": sum(count_tokens(m.content) for m in state.messages),
            "compacted_summary": count_tokens(state.compacted_summary or ""),
        }

    def to_chat_messages(self, state: AgentState) -> list[dict[str, str]]:
        # System message: role + format rules + tools. Task instruction is a user turn so
        # the model is conditioned to respond to it (system-only context causes premature EOS).
        system_parts = [
            state.system_prompt,
            f"Available tools:\n{state.tool_schema}",
        ]
        if state.compacted_summary:
            system_parts.append(f"Previous conversation summary:\n{state.compacted_summary}")
        messages: list[dict[str, str]] = [
            {"role": "system", "content": "\n\n".join(system_parts)},
            {"role": "user", "content": state.task_instruction},
        ]
        for message in state.messages:
            if message.role == "assistant":
                messages.append({"role": "assistant", "content": message.content})
            elif message.role == "tool":
                messages.append({
                    "role": "user",
                    "content": (
                        f"[tool output]\n{message.content}\n\n"
                        "Respond with shell{\"command\":\"...\"} to run another command, "
                        "or #### <summary> when fully done.\n"
                        "To edit a Python file: write the ENTIRE file using "
                        "python3 -c \"open('path','w').write('...')\". Never use sed."
                    ),
                })
            else:
                messages.append({"role": message.role, "content": message.content})
        return messages
