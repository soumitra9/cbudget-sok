import math

from allocators.adaptive import GreedyMarginalAllocator, LearnedBanditAllocator
from allocators.baselines import (
    EqualSplitAllocator,
    IndependentDefaultsAllocator,
    NoCompressionAllocator,
)
from allocators.types import Channel, TaskInstance, TurnBudget
from experiments.cost_model import linear_cost_model
from metrics.pareto import is_pareto_dominated, pareto_frontier, summarize
from allocators.types import TurnResult


def make_task(n_tools=5, difficulty=2.0) -> TaskInstance:
    return TaskInstance(
        task_id="t1",
        source_benchmark="unit_test",
        prompt="do something",
        available_tools=[{"name": f"tool_{i}", "description": "x" * 100} for i in range(n_tools)],
        history=[{"role": "user", "content": "y" * 200}],
        difficulty_proxy=difficulty,
    )


def test_no_compression_allocator_returns_full_theta():
    task = make_task()
    budget = TurnBudget(total_budget=8000, overhead=800)
    theta = NoCompressionAllocator().allocate(task, budget)
    assert all(v == 1.0 for v in theta.values())


def test_equal_split_allocator_sums_close_to_one():
    task = make_task()
    budget = TurnBudget(total_budget=8000, overhead=800)
    theta = EqualSplitAllocator().allocate(task, budget)
    assert math.isclose(sum(theta.values()), 1.0, rel_tol=1e-6)


def test_independent_defaults_allocator_is_static_per_channel():
    task_small = make_task(n_tools=2)
    task_large = make_task(n_tools=50)
    budget = TurnBudget(total_budget=8000, overhead=800)
    allocator = IndependentDefaultsAllocator()
    theta_small = allocator.allocate(task_small, budget)
    theta_large = allocator.allocate(task_large, budget)
    # Defining property of this baseline: it does NOT adapt to task size --
    # that's exactly the behavior the adaptive allocator should beat.
    assert theta_small == theta_large


def test_greedy_marginal_allocator_respects_budget():
    task = make_task(n_tools=20, difficulty=4.0)
    budget = TurnBudget(total_budget=3000, overhead=800)

    def probe(channel, theta, task):
        return math.exp(-3 * theta)

    allocator = GreedyMarginalAllocator(utility_estimator=probe, cost_model=linear_cost_model)
    theta = allocator.allocate(task, budget)

    spent = sum(linear_cost_model(c, theta[c], task) for c in Channel)
    assert spent <= budget.available(), "allocator must not exceed available budget"
    assert all(0.0 <= v <= 1.0 for v in theta.values())


def test_greedy_marginal_allocator_prefers_high_utility_channel():
    task = make_task(n_tools=20, difficulty=4.0)
    budget = TurnBudget(total_budget=6000, overhead=800)

    # Rig the probe so REASONING always looks far more valuable than the rest.
    def biased_probe(channel, theta, task):
        if channel == Channel.REASONING:
            return 10.0 * math.exp(-theta)
        return 0.1 * math.exp(-3 * theta)

    allocator = GreedyMarginalAllocator(utility_estimator=biased_probe, cost_model=linear_cost_model)
    theta = allocator.allocate(task, budget)
    assert theta[Channel.REASONING] >= theta[Channel.TOOL_SCHEMA]
    assert theta[Channel.REASONING] >= theta[Channel.HISTORY]


def test_learned_bandit_allocator_updates_and_allocates():
    task = make_task(n_tools=10, difficulty=1.0)
    budget = TurnBudget(total_budget=4000, overhead=800)
    allocator = LearnedBanditAllocator(cost_model=linear_cost_model)

    # Simulate several turns of feedback favoring the HISTORY channel.
    for _ in range(20):
        allocator.update(task, Channel.HISTORY, observed_utility=5.0)
        allocator.update(task, Channel.TOOL_SCHEMA, observed_utility=0.5)
        allocator.update(task, Channel.REASONING, observed_utility=0.5)

    theta = allocator.allocate(task, budget)
    assert theta[Channel.HISTORY] >= theta[Channel.TOOL_SCHEMA]


def test_pareto_frontier_filters_dominated_allocators():
    results_good = [TurnResult(task_id="t", success=True, total_tokens=500, channel_tokens={})] * 10
    results_bad = [TurnResult(task_id="t", success=False, total_tokens=1000, channel_tokens={})] * 10
    good = summarize("good", "unit_test", results_good)
    bad = summarize("bad", "unit_test", results_bad)

    assert is_pareto_dominated(bad, good)
    frontier = pareto_frontier([good, bad])
    assert frontier == [good]
