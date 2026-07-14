"""vLLM HTTP client (OpenAI-compatible API)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

from cbudget.accounting.occupancy import count_tokens
from cbudget.models.mock_backend import GenerationResult, MockBackend
from cbudget.models.server_config import load_model_config


@dataclass
class ModelClient:
    base_url: str = "http://localhost:8000"
    seed: int = 0
    use_mock: bool = True
    model_name: str = field(default="")
    stop: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._mock: MockBackend | None = MockBackend(seed=self.seed) if self.use_mock else None
        if not self.use_mock and not self.model_name:
            cfg = load_model_config()
            self.model_name = cfg.get("repository", "Qwen/Qwen2.5-7B-Instruct")
            gen = cfg.get("generation", {})
            self.stop = list(gen.get("stop") or [])

    def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.2,
        stop: list[str] | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> GenerationResult:
        if self._mock is not None:
            return self._mock.generate(prompt, max_tokens=max_tokens, temperature=temperature)

        effective_stop = stop if stop is not None else self.stop
        if messages is not None:
            return self._generate_chat(messages, max_tokens, temperature, effective_stop)
        return self._generate_completion(prompt, max_tokens, temperature, effective_stop)

    def _generate_chat(
        self,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
        stop: list[str],
    ) -> GenerationResult:
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if stop:
            payload["stop"] = stop

        with httpx.Client(timeout=120.0) as client:
            response = client.post(f"{self.base_url}/v1/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            choice = data["choices"][0]
            text = choice.get("message", {}).get("content", "") or ""
            text = self._repair_tool_call_stop(text, choice.get("finish_reason", "stop"), stop)
            usage = data.get("usage", {})
            return GenerationResult(
                text=text,
                generated_tokens=usage.get("completion_tokens", count_tokens(text)),
                finish_reason=choice.get("finish_reason", "stop"),
            )

    def _generate_completion(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        stop: list[str],
    ) -> GenerationResult:
        payload: dict[str, Any] = {
            "model": self.model_name,
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
            text = self._repair_tool_call_stop(text, choice.get("finish_reason", "stop"), stop)
            usage = data.get("usage", {})
            return GenerationResult(
                text=text,
                generated_tokens=usage.get("completion_tokens", count_tokens(text)),
                finish_reason=choice.get("finish_reason", "stop"),
            )

    @staticmethod
    def _repair_tool_call_stop(text: str, finish_reason: str, stop: list[str]) -> str:
        if "</tool_call>" in stop and "<tool_call>" in text and "</tool_call>" not in text:
            return text + "</tool_call>"
        return text
