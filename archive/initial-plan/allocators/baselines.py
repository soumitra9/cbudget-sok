"""Baseline allocators (RQ1 comparison points).

Each allocator implements `allocate(task, budget) -> dict[Channel, float]`
returning theta for each channel. These are intentionally simple / faithful
reproductions of "what each prior paper's default behavior amounts to" when
placed under a shared budget it was never designed to share.
"""
from __future__ import annotations

from .types import Channel, TaskInstance, TurnBudget


class NoCompressionAllocator:
    """theta=1.0 everywhere: every tool schema, all history, uncapped reasoning.

    This is the naive baseline that motivates the whole paper -- include it
    first in every experiment table so the token-cost blowup is visible.
    """

    name = "no_compression"

    def allocate(self, task: TaskInstance, budget: TurnBudget) -> dict[Channel, float]:
        return {Channel.TOOL_SCHEMA: 1.0, Channel.HISTORY: 1.0, Channel.REASONING: 1.0}


class EqualSplitAllocator:
    """Naive fixed split: budget divided evenly across the three channels.

    theta per channel is derived by whatever fraction of "full" content that
    equal token share buys, computed by the caller (allocators don't know
    token costs directly; see experiments/run.py for the theta<->token
    conversion via each channel's cost model).
    """

    name = "equal_split"

    def allocate(self, task: TaskInstance, budget: TurnBudget) -> dict[Channel, float]:
        # Placeholder theta; experiments/run.py resolves this against a
        # per-channel cost model to find the theta that fits 1/3 of budget.
        return {Channel.TOOL_SCHEMA: 1 / 3, Channel.HISTORY: 1 / 3, Channel.REASONING: 1 / 3}


class IndependentDefaultsAllocator:
    """Reproduces 'current practice': each channel tuned to its own paper's
    recommended default, with no cross-channel coordination.

    - S: RAG-MCP-style top-k retrieval (default k retained as a constant,
      NOT rebalanced against how much budget H or R are using).
    - H: lean-ctx/Headroom-style aggressive compression (fixed ratio).
    - R: reasoning-token compression at a fixed ratio. NOTE: originally
      modeled on TokenSkip (arXiv:2502.12067), but TokenSkip is now the
      *weak* baseline in this literature -- it degrades sharply at
      aggressive compression (>20-point accuracy drops reported by
      follow-up work) and several 2025-2026 methods (CtrlCoT, Extra-CoT
      arXiv:2602.08324, SEER arXiv:2509.14093) beat it on both axes at
      every reported compression ratio. If this baseline is meant to
      represent "the best a single-channel-only practitioner would
      currently do," swap in Extra-CoT's reported operating point instead
      of TokenSkip's -- see 01_problem_statement_and_related_work.md
      Section 2.2 for the corrected positioning.

    This is the key baseline for RQ1: if the adaptive allocator doesn't beat
    THIS, there's no paper.
    """

    name = "independent_defaults"

    def __init__(
        self,
        tool_top_k_fraction: float = 0.3,   # RAG-MCP-ish: keep top ~30% of tools
        history_retention: float = 0.4,      # lean-ctx-ish default compression
        reasoning_budget_fraction: float = 0.5,  # placeholder ratio; recalibrate
        # against Extra-CoT / CtrlCoT reported curves, not TokenSkip's --
        # see docstring above.
    ) -> None:
        self.tool_top_k_fraction = tool_top_k_fraction
        self.history_retention = history_retention
        self.reasoning_budget_fraction = reasoning_budget_fraction

    def allocate(self, task: TaskInstance, budget: TurnBudget) -> dict[Channel, float]:
        return {
            Channel.TOOL_SCHEMA: self.tool_top_k_fraction,
            Channel.HISTORY: self.history_retention,
            Channel.REASONING: self.reasoning_budget_fraction,
        }


BASELINE_REGISTRY = {
    "no_compression": NoCompressionAllocator,
    "equal_split": EqualSplitAllocator,
    "independent_defaults": IndependentDefaultsAllocator,
}
