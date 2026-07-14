"""Chain-of-Draft policy: tool turns vs final #### turn."""

from __future__ import annotations

from cbudget.agents.react import ReactPolicy


class ChainOfDraftPolicy(ReactPolicy):
    def system_prompt(self, base: str) -> str:
        instruction = self.config.get("instruction_text", "").strip()
        if not instruction:
            return base
        return f"{base}\n\n{instruction}"
