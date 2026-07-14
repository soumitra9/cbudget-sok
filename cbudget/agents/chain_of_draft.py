"""Chain-of-Draft policy: tool turns vs final #### turn."""

from __future__ import annotations

import sys

from cbudget.agents.react import ReactPolicy


class ChainOfDraftPolicy(ReactPolicy):
    def system_prompt(self, base: str) -> str:
        instruction = self.config.get("instruction_text", "").strip()
        if not instruction:
            print(
                "ERROR: ChainOfDraftPolicy requires non-empty instruction_text in policy config.",
                file=sys.stderr,
            )
            raise ValueError("ChainOfDraftPolicy missing instruction_text; refusing to run as ReAct.")
        return f"{base}\n\n{instruction}"
