"""Adaptive joint allocator (RQ1 / RQ3).

Implements the KKT-motivated rule from Section 1.2 of the problem statement:
at a jointly-optimal allocation, marginal utility per token should be equal
across channels. We approximate this online with a simple contextual-bandit
style update rather than solving the Lagrangian exactly, since true marginal
utilities are unobserved and must be estimated from noisy per-turn outcomes.

Two variants are provided:
  - GreedyMarginalAllocator: myopic, allocates the next token increment to
    whichever channel currently has the highest ESTIMATED marginal utility.
    Cheap, no training required, good first thing to get working.
  - LearnedBanditAllocator: maintains a per-(task-type, channel) utility
    estimate updated via observed outcomes (UCB1-style), so it improves
    across a benchmark run rather than re-estimating from scratch each turn.
"""
from __future__ import annotations

import math
from collections import defaultdict

from .types import Channel, TaskInstance, TurnBudget, UtilityEstimator

STEP = 0.05  # granularity of theta increments when greedily allocating


class GreedyMarginalAllocator:
    """Iteratively hands the next token increment to the channel with the
    highest estimated marginal utility until the budget is exhausted.

    Requires a `utility_estimator` callable (see types.UtilityEstimator).
    In the first pass this can be a cheap proxy (e.g., a small held-out
    probe set per channel/task-type) rather than a fully learned model --
    see experiments/probes.py for how that proxy should be constructed.
    """

    name = "greedy_marginal"

    def __init__(self, utility_estimator: UtilityEstimator, cost_model) -> None:
        self.utility_estimator = utility_estimator
        self.cost_model = cost_model  # maps (channel, theta, task) -> tokens

    def allocate(self, task: TaskInstance, budget: TurnBudget) -> dict[Channel, float]:
        theta = {c: 0.0 for c in Channel}
        available = budget.available()
        spent = 0

        # Always fund a minimal floor per channel first (an agent with zero
        # tool schemas or zero reasoning tokens usually just fails outright;
        # the marginal-utility curve near theta=0 is degenerate/undefined).
        floor = 0.05
        for c in Channel:
            theta[c] = floor
            spent += self.cost_model(c, theta[c], task)

        while spent < available:
            # Estimate marginal utility of the next STEP increment for each
            # channel at its current theta, pick the best, apply it.
            best_channel = None
            best_utility = -math.inf
            for c in Channel:
                if theta[c] >= 1.0:
                    continue
                u = self.utility_estimator(c, theta[c], task)
                if u > best_utility:
                    best_utility = u
                    best_channel = c

            if best_channel is None:
                break  # every channel maxed out

            next_theta = min(1.0, theta[best_channel] + STEP)
            incremental_cost = self.cost_model(best_channel, next_theta, task) - \
                self.cost_model(best_channel, theta[best_channel], task)

            if spent + incremental_cost > available:
                break  # can't afford the next increment anywhere; stop

            theta[best_channel] = next_theta
            spent += incremental_cost

        return theta


class LearnedBanditAllocator:
    """UCB1-style bandit over (task_type, channel) pairs.

    Tracks a running mean marginal-utility-per-token estimate for each
    channel, conditioned on a coarse task-type key (e.g., source_benchmark +
    a difficulty bucket), and uses that instead of a fresh per-turn probe.
    Cheaper at inference time than GreedyMarginalAllocator once "warmed up"
    across a benchmark run; strictly an RQ3 mechanism, not required for RQ1.
    """

    name = "learned_bandit"

    def __init__(self, cost_model, exploration_c: float = 1.0) -> None:
        self.cost_model = cost_model
        self.exploration_c = exploration_c
        self._counts: dict[tuple[str, Channel], int] = defaultdict(int)
        self._means: dict[tuple[str, Channel], float] = defaultdict(float)
        self._total_pulls = 0

    def _task_key(self, task: TaskInstance) -> str:
        bucket = "unknown"
        if task.difficulty_proxy is not None:
            bucket = "easy" if task.difficulty_proxy < 2 else (
                "medium" if task.difficulty_proxy < 5 else "hard"
            )
        return f"{task.source_benchmark}:{bucket}"

    def _ucb_score(self, key: tuple[str, Channel]) -> float:
        n = self._counts[key]
        if n == 0:
            return math.inf  # force initial exploration
        mean = self._means[key]
        bonus = self.exploration_c * math.sqrt(math.log(max(self._total_pulls, 1)) / n)
        return mean + bonus

    def update(self, task: TaskInstance, channel: Channel, observed_utility: float) -> None:
        key = (self._task_key(task), channel)
        n = self._counts[key]
        self._means[key] = (self._means[key] * n + observed_utility) / (n + 1)
        self._counts[key] += 1
        self._total_pulls += 1

    def allocate(self, task: TaskInstance, budget: TurnBudget) -> dict[Channel, float]:
        task_key = self._task_key(task)
        theta = {c: 0.05 for c in Channel}  # same floor rationale as above
        available = budget.available()
        spent = sum(self.cost_model(c, theta[c], task) for c in Channel)

        while spent < available:
            scores = {c: self._ucb_score((task_key, c)) for c in Channel if theta[c] < 1.0}
            if not scores:
                break
            best_channel = max(scores, key=scores.get)
            next_theta = min(1.0, theta[best_channel] + STEP)
            incremental_cost = self.cost_model(best_channel, next_theta, task) - \
                self.cost_model(best_channel, theta[best_channel], task)
            if spent + incremental_cost > available:
                break
            theta[best_channel] = next_theta
            spent += incremental_cost

        return theta
