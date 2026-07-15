"""Shared types for the context-budget-allocation experiment harness.

Channels are: S (tool/schema context), H (history/retrieved context),
R (reasoning tokens). See 01_problem_statement_and_related_work.md
Section 1.2 for the formal definitions these types implement.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class Channel(str, Enum):
    TOOL_SCHEMA = "S"
    HISTORY = "H"
    REASONING = "R"


@dataclass
class ChannelState:
    """Current compression control and observed token cost for one channel."""

    channel: Channel
    theta: float  # compression control, meaning is channel-specific:
    #   S: fraction/top-k of tools retained (0=none, 1=all)
    #   H: retention ratio of history/retrieved content (0=fully summarized, 1=verbatim)
    #   R: target reasoning-token budget as a fraction of an uncompressed baseline
    tokens: int = 0  # tokens actually consumed after applying theta this turn
    last_marginal_utility: Optional[float] = None  # dTaskSuccess/dTokens estimate


@dataclass
class TurnBudget:
    """The overall budget for a single agent turn."""

    total_budget: int
    overhead: int  # O: system prompt + reserved output tokens, fixed
    channels: dict[Channel, ChannelState] = field(default_factory=dict)

    def available(self) -> int:
        return self.total_budget - self.overhead

    def spent(self) -> int:
        return sum(c.tokens for c in self.channels.values())

    def remaining(self) -> int:
        return self.available() - self.spent()


@dataclass
class TaskInstance:
    """One evaluation instance from a benchmark loader.

    Deliberately benchmark-agnostic: loaders for BFCL / MCP-Bench / tau-bench
    all normalize into this shape so allocators and metrics don't need to
    know which benchmark produced the instance.
    """

    task_id: str
    source_benchmark: str  # "bfcl_v4" | "mcp_bench" | "tau_bench"
    prompt: str
    available_tools: list[dict]  # raw tool schemas (name, description, parameters)
    history: list[dict] = field(default_factory=list)  # prior turns / retrieved docs
    difficulty_proxy: Optional[float] = None  # e.g., number of required tool calls
    metadata: dict = field(default_factory=dict)


@dataclass
class TurnResult:
    task_id: str
    success: bool
    total_tokens: int
    channel_tokens: dict[Channel, int]
    raw_output: Optional[str] = None


# Marginal-utility estimator signature used by the adaptive allocator.
# Takes (channel, theta, task) -> estimated d(success)/d(token) at that theta.
UtilityEstimator = Callable[[Channel, float, TaskInstance], float]
