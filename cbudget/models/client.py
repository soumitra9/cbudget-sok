"""vLLM HTTP client (OpenAI-compatible API)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from cbudget.models.mock_backend import GenerationResult, MockBackend, get_backend


@dataclass
class ModelClient:
    base_url: str = "http://localhost:8000"
    seed: int = 0
    use_mock: bool = True

    def __post_init__(self) -> None:
        self._mock: MockBackend | None = MockBackend(seed=self.seed) if self.use_mock else None

    def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.2,
        stop: list[str] | None = None,
    ) -> GenerationResult:
        if self._mock is not None:
            return self._mock.generate(prompt, max_tokens=max_tokens, temperature=temperature)

        payload: dict[str, Any] = {
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if stop:
            payload["stop"] = stop

        with httpx.Client(timeout=120.0) as client:
            response = client.post(f"{self.base_url}/v1/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            choice = data["choices"][0]
            text = choice.get("text", "")
            usage = data.get("usage", {})
            return GenerationResult(
                text=text,
                generated_tokens=usage.get("completion_tokens", len(text.split())),
                finish_reason=choice.get("finish_reason", "stop"),
            )
