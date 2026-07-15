"""End-to-end experiment runner: for each benchmark x allocator pair, run
every task instance through the allocator, execute the (compressed) prompt
against a model, score success, and produce an AllocatorRunSummary table.

This file wires the pieces together but stubs out the actual model call
(`execute_turn`) -- that's the piece that needs a real inference backend
(local HF model on the A40s, or an API) plugged in before results mean
anything. Everything upstream of that (loaders, allocators, cost model,
metrics) is runnable and testable right now without a model.

Usage (once data + execute_turn are wired up):
    python -m experiments.run --benchmark bfcl_v4 --data-path /path/to/bfcl
"""
from __future__ import annotations

import argparse
from pathlib import Path

from allocators.adaptive import GreedyMarginalAllocator
from allocators.baselines import BASELINE_REGISTRY
from allocators.types import Channel, TaskInstance, TurnBudget, TurnResult
from benchmarks.bfcl_loader import BFCLLoader
from benchmarks.mcp_bench_loader import MCPBenchLoader
from benchmarks.tau_bench_loader import TauBenchLoader
from experiments.cost_model import linear_cost_model
from metrics.pareto import pareto_frontier, summarize

LOADERS = {
    "bfcl_v4": BFCLLoader,
    "mcp_bench": MCPBenchLoader,
    "tau_bench": TauBenchLoader,
}

DEFAULT_BUDGET = 8000  # tokens; sweep this in the actual experiment grid
DEFAULT_OVERHEAD = 800  # system prompt + reserved output


def naive_utility_probe(channel: Channel, theta: float, task: TaskInstance) -> float:
    """Placeholder marginal-utility estimator for GreedyMarginalAllocator.

    Replace with either (a) a small held-out probe set run against the real
    model to measure d(success)/d(tokens) empirically per channel/theta
    bucket, or (b) the LearnedBanditAllocator's online estimates once a
    benchmark run has warmed those up. Diminishing returns shape only,
    calibrated to nothing real yet -- this exists so the allocation loop is
    exercisable end-to-end before model-in-the-loop measurement exists.
    """
    import math

    return math.exp(-3 * theta)  # front-loaded utility, decays as theta -> 1


def execute_turn(task: TaskInstance, theta: dict[Channel, float]) -> TurnResult:
    """STUB. Replace with a real call: build the compressed prompt according
    to theta (truncate/retrieve tools per theta[S], summarize history per
    theta[H], cap reasoning tokens per theta[R] via max_tokens or a
    skip-token method), run it against the target model, and score success
    against the benchmark's own grader (AST match for BFCL, env-state check
    for tau-bench, task-specific check for MCP-Bench).
    """
    raise NotImplementedError(
        "Wire this up to a real inference backend before running experiments. "
        "See docstring for what each theta value should control."
    )


def run_allocator(allocator, tasks: list[TaskInstance], budget_size: int) -> list[TurnResult]:
    results = []
    for task in tasks:
        budget = TurnBudget(total_budget=budget_size, overhead=DEFAULT_OVERHEAD)
        theta = allocator.allocate(task, budget)
        result = execute_turn(task, theta)
        results.append(result)
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", required=True, choices=list(LOADERS.keys()))
    parser.add_argument("--data-path", required=True, type=Path)
    parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    args = parser.parse_args()

    loader = LOADERS[args.benchmark]()
    tasks = loader.load(args.data_path)
    if not tasks:
        raise SystemExit(
            f"No tasks loaded from {args.data_path} -- check the loader's "
            f"expected file layout in benchmarks/{args.benchmark}_loader.py"
        )

    allocators = {name: cls() for name, cls in BASELINE_REGISTRY.items()}
    allocators["greedy_marginal"] = GreedyMarginalAllocator(
        utility_estimator=naive_utility_probe, cost_model=linear_cost_model
    )

    summaries = []
    for name, allocator in allocators.items():
        results = run_allocator(allocator, tasks, args.budget)
        summaries.append(summarize(name, args.benchmark, results))

    frontier = pareto_frontier(summaries)
    print("\n=== Pareto frontier (non-dominated allocators) ===")
    for s in frontier:
        print(f"{s.allocator_name:24s} success={s.task_success_rate:.3f} "
              f"tokens={s.mean_total_tokens:.0f} cna={s.cost_normalized_accuracy:.4f}")


if __name__ == "__main__":
    main()
