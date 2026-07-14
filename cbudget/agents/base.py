"""Agent policy interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from cbudget.agent.state import AgentState


class AgentPolicy(ABC):
    @abstractmethod
    def system_prompt(self, base: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def parse_response(self, text: str, state: AgentState) -> dict:
        """Return {action: tool|final, command?, answer?}."""
        raise NotImplementedError
