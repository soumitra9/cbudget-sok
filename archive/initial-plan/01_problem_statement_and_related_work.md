# Context Budget Allocation for Agentic LLMs: A Joint Optimization View of Tool Schemas, Retrieved Context, and Reasoning Tokens

## 1. Problem Statement

### 1.1 Motivation

Modern agentic LLM deployments (Claude Code, Cursor, MCP-connected assistants) draw on
a single, finite input budget to serve at least three competing purposes within every turn:

1. **Tool/schema context** — the JSON schemas, descriptions, and parameter specs for every
   connected tool, injected regardless of whether the turn uses them.
2. **Retrieved/history context** — file contents, shell output, prior tool results,
   conversation history.
3. **Reasoning tokens** — the model's own generated chain-of-thought, which for
   reasoning-tuned models can run into the thousands of tokens per turn and itself
   competes for the same context window on subsequent turns once it re-enters context.

Production measurements show this is not a marginal concern: a stack of three MCP servers
(GitHub, Slack, Sentry — roughly 40 tools) can consume 72% of a 200K-token window in
schemas alone before a user query is processed, and reasoning-tuned models can add
another several thousand tokens per turn once CoT length exceeds ~10K tokens on hard
problems.

Two independent research communities have each optimized one slice of this budget:

- The **tool-selection community** (RAG-MCP, MCP-Zero) reduces channel (1) via retrieval
  or on-demand tool discovery.
- The **efficient-reasoning community** (TokenSkip, CCoT, RL-pruned CoT methods) reduces
  channel (3) via skip-token selection, latent compression, or length-penalized training.
- A separate **applied tooling ecosystem** (Headroom, lean-ctx, MCP gateways) compresses
  channel (2) heuristically — caching, AST-aware summarization, deduplication.

**No published work treats these three channels as a single constrained resource-allocation
problem.** Each is compressed to its own local optimum, evaluated on its own metric
(tool-selection accuracy for (1), CoT-accuracy tradeoff for (3), raw token savings for
(2)), with no shared objective function and no cross-channel citation graph between the
three literatures as of this writing (mid-2026).

### 1.2 Formalization

For a single agent turn operating under a hard context budget $B$ (tokens), let:

$$B = S + H + R + O$$

where:
- $S$ = tokens spent on tool/schema context,
- $H$ = tokens spent on retrieved/history context,
- $R$ = tokens spent on reasoning (CoT) generation,
- $O$ = fixed overhead (system prompt, output budget reserve), treated as constant.

Each channel $c \in \{S, H, R\}$ has a **compression control** $\theta_c$ (e.g., retrieval-$k$
for $S$, summarization ratio for $H$, a skip-threshold or target length for $R$) and an
associated **marginal utility function** $u_c(\theta_c)$ — the task-success gain per
token spent in that channel, holding the others fixed. Channel utility functions are
almost certainly non-linear, task-dependent, and exhibit diminishing returns (adding the
9th tool schema back in after the 8th most relevant one already restored most of the
accuracy loss buys little; the first few hundred reasoning tokens buy much more than the
last few thousand).

**Independent optimization** (current practice) selects each $\theta_c$ to maximize
$u_c$ subject only to a per-channel budget fixed in advance, typically by convention or
by each tool's own defaults (e.g., RAG-MCP's top-$k$, TokenSkip's compression ratio).

**Joint optimization** (the proposed framing) selects $(\theta_S, \theta_H, \theta_R)$
to solve:

$$\max_{\theta_S,\theta_H,\theta_R} \; \text{TaskSuccess}(\theta_S,\theta_H,\theta_R)
\quad \text{s.t.} \quad S(\theta_S) + H(\theta_H) + R(\theta_R) \le B - O$$

A standard result from constrained optimization is that a jointly optimal allocation
equalizes marginal utility per token across channels ($u_S'= u_H' = u_R'$ at the
optimum, via KKT / Lagrangian conditions), which independently-tuned per-channel
defaults have no mechanism to achieve — each channel's paper optimizes against its own
implicit budget, not against the other two channels' opportunity cost.

### 1.3 Research Questions

- **RQ1 (Existence of the gap):** Does an allocation that equalizes cross-channel
  marginal utility empirically outperform independently-tuned per-channel baselines at
  matched total token budget, on realistic agentic tool-use tasks?
- **RQ2 (Structure of the tradeoff):** How do marginal-utility curves for $S$, $H$, and
  $R$ differ by task type (e.g., simple single-tool BFCL calls vs. multi-turn τ-bench
  policy-constrained tasks vs. MCP-Bench multi-server tasks)? Is there a stable ordering,
  or does the optimal split shift enough per-task that a static split is provably
  insufficient?
- **RQ3 (Adaptivity):** Can a lightweight online controller (bandit / online-convex
  update), observing per-turn signals, recover most of the gain from the oracle joint
  allocation without per-task offline tuning?

---

## 2. Related Work

### 2.1 Tool/Schema-Level Context Compression

**RAG-MCP** (Gan & Sun, arXiv:2505.03275) reframes tool discovery as retrieval: a
semantic index returns only the top-$k$ relevant tool descriptions before the LLM sees
the prompt, cutting prompt tokens by over 50% and more than tripling tool-selection
accuracy (43.13% vs. 13.62% baseline) on a stress test with a growing tool pool.

**MCP-Zero** (Fei, Zheng & Feng, arXiv:2506.01056) inverts the pattern further: instead
of retrieving candidates for the model, the model actively requests the tools it
believes it needs via structured requests, resolved through hierarchical semantic
routing. On a 308-server, 2,797-tool dataset, this yields a 98% reduction in token
consumption on APIBank while preserving accuracy.

**Dynamic ReAct** (arXiv:2509.20386) benchmarks itself directly against both of the
above for large-scale MCP tool selection, indicating the sub-field already treats
RAG-MCP and MCP-Zero as the standard baselines.

**"MCP Tool Descriptions Are Smelly!"** (arXiv:2602.14878) runs an ablation over the
*components* of a tool description (summary, parameter docs, examples, etc.) and finds
no single minimal-description recipe generalizes across domains and models — i.e., even
within channel $S$ alone, the compression-vs-accuracy tradeoff is task-dependent, which
motivates treating $\theta_S$ as a learned control rather than a fixed convention.

**Gap relative to this proposal:** all three treat $S$ as the only variable and hold $H$
and $R$ implicitly fixed (or unmeasured). None report reasoning-quality or
history-compression interactions.

### 2.2 Reasoning-Token Compression

Three current surveys map this sub-field: **"Stop Overthinking"** (Sui et al.,
arXiv:2503.16419, TMLR 2025), **"A Survey of Efficient Reasoning for Large Reasoning
Models"** (arXiv:2503.21614), and **"Efficient Reasoning Models: A Survey"**
(arXiv:2504.10903). They converge on the same taxonomy: discrete text-token compression
(prompt engineering, instruction tuning, RL-based length penalties) vs. continuous
latent-token compression.

**TokenSkip** (Xia et al., arXiv:2502.12067) established the now-common paradigm:
score per-token semantic importance within a CoT, build compressed training pairs at
target ratios, and fine-tune the model to generate compressed rationales directly. It
remains the most-cited baseline in this space, but it is **not the current state of the
art** — at moderate compression (~40%) it preserves accuracy well (Qwen2.5-14B on GSM8K:
313→181 tokens, <0.4% accuracy drop), but multiple follow-ups report it becomes unstable
or collapses at aggressive ratios: one direct comparison found TokenSkip loses over 20
accuracy points at high compression, and a software-engineering-reasoning study found it
occasionally produces *longer* output than the uncompressed baseline due to truncation
artifacts. Later methods that directly supersede it: **CtrlCoT** (dual-granularity
compression, beats TokenSkip's accuracy at fewer tokens across 3B/7B/14B scales),
**Extra-CoT** (arXiv:2602.08324; specifically targets the high-compression regime where
TokenSkip collapses, remaining robust at ratios as extreme as 0.2), and **SEER**
(arXiv:2509.14093; reports more stable behavior than TokenSkip across compression
settings on software-engineering benchmarks).

**Compressed Chain of Thought / CCoT** (arXiv:2412.13171) takes a different approach
from all of the above: instead of shortening CoT *text*, it replaces it with trained
dense "contemplation tokens" in latent space, giving a tunable compression ratio via
LoRA fine-tuning. RL-pruning approaches (ThinkPrune, C3oT, O1-Pruner, and the
certainty-triggered suppression method CGRS, arXiv:2508.05337) instead train the model
to *generate* shorter reasoning directly via reward shaping, rather than post-hoc
filtering.

**Chain of Draft / CoD** (Xu et al., arXiv:2502.18600) is the notable outlier: a
**prompting-only** method requiring no fine-tuning at all — simply instructing the model
to keep each reasoning step to ~5 words. It reports token reductions as extreme as
92%+ on some task types (commonsense reasoning) while matching or exceeding CoT
accuracy, and is a meaningfully cheaper thing to implement first for $\theta_R$'s cost
model than a fine-tuned method, at the cost of being less precisely controllable to a
specific target ratio than TokenSkip-style training.

**Gap relative to this proposal:** every method here treats the CoT budget in isolation
against a fixed task-accuracy objective. None model $R$'s compression control as
competing for the *same* window as $S$ or $H$ within an agentic (tool-using) loop —
the evaluated tasks are almost exclusively single-turn math/reasoning benchmarks
(GSM8K, MATH, AMC2023), not tool-calling agents. This also means none of their reported
$u_R(\theta_R)$ curves have been validated in a ReAct-style setting where Thoughts are
interleaved with Actions/Observations rather than generated as one uninterrupted block —
worth flagging as a stated limitation/threat-to-validity when this paper's own curves are
measured only in the agentic setting and can't be directly compared to these papers'
single-shot numbers.

### 2.3 General Context/History Compression Tooling

Applied tools — **Headroom** (compress/retrieve MCP-exposed content on demand) and
**lean-ctx** (AST-aware compression of file reads and shell output, 60–99% savings
depending on mode and cache state) — address channel $H$ (and, for lean-ctx, also
overlap into $S$ via its own MCP tool wrappers). Neither publishes a peer-reviewed
evaluation; both report token-savings metrics without controlled reasoning-quality
ablations, and neither coordinates its compression aggressiveness with the *other* two
channels' current occupancy.

### 2.4 Benchmarks Available for a Joint Study

- **BFCL v4** (Patil et al., ICML 2025) — tool-selection correctness across single-turn,
  multi-turn, and agentic categories; AST-based evaluation of function-call correctness.
- **MCP-Bench** (arXiv:2508.20453) — benchmarks tool-using agents specifically over real
  MCP servers with complex, realistic tasks; the natural fit for varying $|tools|$
  (and therefore $S$) independently of task difficulty.
- **τ-bench** (Yao et al., arXiv:2406.12045) — multi-turn tool-agent-user interaction
  with policy constraints, where reasoning depth (not just tool selection) plausibly
  drives success; a τ²-bench extension (Sierra Research) adds dual-control multi-turn
  scenarios but its primary citation should be confirmed directly before submission
  rather than assumed here.

### 2.5 Summary of the Gap

| Channel | Optimized in isolation by | Metric used | Coordinated with other channels? |
|---|---|---|---|
| $S$ (tool schemas) | RAG-MCP, MCP-Zero, Dynamic ReAct | tool-selection accuracy, prompt tokens | No |
| $H$ (history/retrieved context) | Headroom, lean-ctx | token savings | No |
| $R$ (reasoning tokens) | CtrlCoT, Extra-CoT, SEER, CCoT, CoD (TokenSkip: foundational but superseded) | task accuracy vs. CoT length | No |

No paper in any of the three columns reports a metric that spans more than one channel,
and none formalizes the shared-budget constraint in Section 1.2. That is the specific,
citable gap this paper targets.

---

## 3. Notes for Attorney/NIW Context (delete before submission)

This is a systems/ML-efficiency contribution, not a security paper — it does not by
itself strengthen the adversarial-ML/national-security thread of the NIW compendium the
way the CARS 2026 anomaly-detection paper does. If it's meant to double as NIW evidence
(Prong 2 authority-building) rather than purely as a peer-review/judging credibility
signal, consider whether a security-flavored framing (e.g., budget allocation under
*adversarially grown* tool sets, tying back to FedRAMP/production-infrastructure
relevance) is worth layering in before the related-work section is locked. Flagging
this now since it changes venue choice and framing — happy to sketch that variant
alongside this one if useful.
