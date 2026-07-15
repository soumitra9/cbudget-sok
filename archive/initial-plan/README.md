# context-budget-allocation

Experiment harness for *"Context Budget Allocation for Agentic LLMs: A Joint
Optimization View of Tool Schemas, Retrieved Context, and Reasoning
Tokens"*. See `01_problem_statement_and_related_work.md` for the
formalization and related-work positioning this code implements.

## Status

Runnable right now, without a model:
- `allocators/` — baseline allocators (no-compression, equal-split,
  independent-defaults) and adaptive allocators (greedy marginal-utility,
  UCB1 bandit). Fully implemented, unit-tested.
- `metrics/pareto.py` — Pareto-frontier and cost-normalized-accuracy
  summaries. Fully implemented, unit-tested.
- `benchmarks/` — loaders for BFCL v4, MCP-Bench, tau-bench, normalizing
  each into the shared `TaskInstance` type. **Stubbed against best-guess
  file layouts** — confirm against the real released data before trusting
  output; each loader's docstring flags this.
- `experiments/cost_model.py` — placeholder theta→tokens cost model
  (linear, char-count-based). **Needs replacement** with a real tokenizer
  and measured (not assumed) compression curves before any reported numbers
  are meaningful — see the module docstring for the calibration recipe.
- `experiments/run.py` — end-to-end orchestration. Everything runs except
  `execute_turn`, which is intentionally a `NotImplementedError` stub until
  a real inference backend (local HF model on the A40s, or an API) is
  wired in.

## Not yet done (in priority order)

1. **`execute_turn`**: build the actual compressed prompt from `theta` and
   call a real model. This is the single blocking piece for any real
   experiment.
2. **Real cost model**: replace `linear_cost_model` with tokenizer-measured
   curves per channel (RQ2 needs this to even describe the marginal-utility
   shapes honestly).
3. **Real utility probes**: replace `naive_utility_probe` with either a
   small held-out calibration set per (channel, task-type) or bootstrap
   from `LearnedBanditAllocator`'s online estimates across a first
   benchmark pass.
4. **Confirm MCP-Bench and tau-bench data schemas** against the actual
   released artifacts — the loaders currently guess field names from the
   papers' task descriptions.
5. **Pin down tau2-bench's citation** before using it — flagged as
   unconfirmed in the related-work doc.

## Running tests

```
pip install -r requirements.txt
pytest tests/ -v
```

All allocator/metric logic is covered without needing model access or
downloaded benchmark data.

## Running an experiment (once step 1-2 above are done)

```
python -m experiments.run --benchmark bfcl_v4 --data-path /path/to/bfcl/data
```
