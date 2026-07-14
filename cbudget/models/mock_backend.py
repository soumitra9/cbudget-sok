"""Mock inference backend for local CPU development."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any


from cbudget.accounting.occupancy import count_tokens


@dataclass
class GenerationResult:
    text: str
    generated_tokens: int
    finish_reason: str = "stop"


class MockBackend:
    """Returns deterministic canned responses preserving the JSONL event schema."""

    def __init__(self, seed: int = 0) -> None:
        self.seed = seed
        self._turn = 0

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.2) -> GenerationResult:
        self._turn += 1
        if self._turn == 1:
            text = 'Thought: inspect repo\n<tool_call>{"name":"shell","arguments":{"command":"ls -la"}}</tool_call>'
            return GenerationResult(text=text, generated_tokens=count_tokens(text))
        if self._turn == 2:
            text = "Thought: apply fix\n####\nTask complete."
            return GenerationResult(text=text, generated_tokens=count_tokens(text))
        text = "####\nDone."
        return GenerationResult(text=text, generated_tokens=count_tokens(text))


def get_backend(seed: int = 0) -> MockBackend:
    backend = os.environ.get("CBUDGET_BACKEND", "mock").lower()
    if backend == "mock":
        return MockBackend(seed=seed)
    raise NotImplementedError(f"Backend {backend!r} not implemented yet; use mock locally.")
