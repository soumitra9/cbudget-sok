"""Metrics for comparing allocators: the accuracy-vs-token Pareto frontier
and cost-normalized accuracy, per Section "Evaluation" of the proposal.
"""
from __future__ import annotations

from dataclasses import dataclass

from allocators.types import TurnResult


@dataclass
class AllocatorRunSummary:
    allocator_name: str
    benchmark: str
    task_success_rate: float
    mean_total_tokens: float
    cost_normalized_accuracy: float  # success_rate per 1K tokens
    n_tasks: int


def summarize(allocator_name: str, benchmark: str, results: list[TurnResult]) -> AllocatorRunSummary:
    n = len(results)
    if n == 0:
        raise ValueError("no results to summarize")
    success_rate = sum(r.success for r in results) / n
    mean_tokens = sum(r.total_tokens for r in results) / n
    cna = success_rate / (mean_tokens / 1000) if mean_tokens > 0 else 0.0
    return AllocatorRunSummary(
        allocator_name=allocator_name,
        benchmark=benchmark,
        task_success_rate=success_rate,
        mean_total_tokens=mean_tokens,
        cost_normalized_accuracy=cna,
        n_tasks=n,
    )


def is_pareto_dominated(a: AllocatorRunSummary, b: AllocatorRunSummary) -> bool:
    """True if `a` is dominated by `b`: b has >= accuracy at <= token cost,
    with at least one strict inequality. Used to filter the frontier plot
    down to allocators actually worth reporting in the main table."""
    not_worse = b.task_success_rate >= a.task_success_rate and b.mean_total_tokens <= a.mean_total_tokens
    strictly_better = b.task_success_rate > a.task_success_rate or b.mean_total_tokens < a.mean_total_tokens
    return not_worse and strictly_better


def pareto_frontier(summaries: list[AllocatorRunSummary]) -> list[AllocatorRunSummary]:
    return [s for s in summaries if not any(is_pareto_dominated(s, other) for other in summaries if other is not s)]
