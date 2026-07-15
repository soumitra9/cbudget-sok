# Research Plan — SoK: The Context Budget (v1)
### Working title: "SoK: Context as a Budget — Systematizing Token-Efficiency Interventions in LLM Agents"
### Revision date: July 14, 2026 — v2 precision pass: incorporates friend review of v1 (all 17 points)

**Companion artifacts (do not merge into this file):**
- `method-extraction_sheet_v1.md` — canonical Phase 2 evidence (one row per method)
- `SoK_Context_Budget_Research_Plan.md` — original plan (superseded by this document)

---

## PART A — WHAT, WHY, HOW (revised)

**WHAT:** A Systematization-of-Knowledge paper organizing academic methods, practitioner tools, and platform-native interventions that reduce token use or context pressure in large language model agents. The paper classifies where each intervention acts in the agent lifecycle, which token population it changes, whether it reduces prompt tokens (PT), generated tokens (GT), peak occupancy (PO), or unnecessary work, and what information or behavior it risks altering. It argues that the field lacks a common accounting framework and controlled evidence about how independently deployable interventions interact when composed.

**Three primary contributions:**
1. *Taxonomy and accounting model* — a lifecycle classification with orthogonal axes and a session-level vector accounting that separates PT, GT, PO, caching state, compaction events, and auxiliary overhead.
2. *Identification and documentation of the evaluation gap* — evidence tables showing that no cross-population interaction has been controlled for, that evaluation units are incommensurable across categories, and that compaction is an uncontrolled universal variable in practitioner benchmarks.
3. *Interaction framework and research agenda* — a mechanism-based hypothesis register for composition effects (additive, sub-additive, antagonistic, structurally blocked) and a proposed minimum reporting standard enabling future commensurable evaluation.

**WHY:** Agent developers already assemble stacks containing tool-schema management, tool-output filtering, history compaction, persistent behavioral instructions, and sometimes concise-reasoning policies. Existing evaluations use incompatible accounting boundaries and generally report either isolated method results or aggregate results for internally bundled systems. Practitioners therefore cannot predict whether independently deployable interventions will be additive, redundant, antagonistic, or behaviorally self-defeating at the session level. This gap must be verified, not assumed (Phase 1 prior-art sweep).

**HOW:**
1. Construct the corpus through a documented prior-art search and explicit inclusion criteria.
2. Extract mechanism, lifecycle stage, token population, resource effect, evidence quality, deployment requirements, and failure mode from primary sources (see `method-extraction_sheet_v1.md`).
3. Introduce a session-level accounting model separating PT (uncached / cache-write / cache-read), GT, PO, behavioral avoidance, caching effects, compaction events, and auxiliary overhead.
4. Establish the evaluation and composition gap through evidence tables — not a leaderboard of incomparable percentages.
5. Derive a mechanism-based interaction framework (C1–C5) and pre-register predictions before any pilot.
6. Run at least one high-value composition experiment if targeting an archival venue.
7. Propose a minimum reporting standard and composition-benchmark design.

---

## PART B — PAPER SECTION STRUCTURE (revised)

| # | Section | Content | Why it exists |
|---|---------|---------|---------------|
| 1 | **Introduction** | Token-bill motivation (Cursor four-scenario measurement); revised thesis; contributions list | Hooks with measured numbers; states position up front |
| 2 | **Scope and Accounting Model** | IN: context-token budget, session-level accounting. OUT: KV-cache/inference-cost optimization. Define PT = PT_uncached + PT_cache-write + PT_cache-read; GT; PO; behavioral avoidance; auxiliary overhead; compaction events. Recurrence and cache as first-class dimensions. **Terminology table here** (CoT, CoD, CtrlCoT, each CCoT expansion, PT, GT, PO, compaction, prompt compression). Add: *We use "context budget" as an umbrella term for the session-level resources that determine active context occupancy, token billing, and the amount of prior trajectory replayed across turns; not every intervention modifies the prompt directly.* | SoK lives or dies on scope discipline; cache and compaction are not footnotes |
| 3 | **Corpus Construction and Review Method** | Databases searched, search strings, cutoff date, inclusion/exclusion criteria, screening log, evidence grading [P/A/S], repo version freezing, taxonomy coding process | Without this, the paper reads as a curated essay, not a systematic study |
| 4 | **Anatomy of an Agent Token Bill** | Four-scenario measurement formalized: category breakdown, frozen vs growing populations, conversation compounding | Empirical skeleton for the taxonomy |
| 5 | **Taxonomy of Interventions** | Lifecycle categories × orthogonal axes (Part C). LLMLingua-2 in main taxonomy (connective tissue). Broader prompt-compression family in Related Work | Core systematization contribution |
| 6 | **Evaluation Practices and Evidence Quality** | Per-method primary metrics (C2 table); evidence-quality gradient as named finding; what each method's reported savings include/exclude | Demonstrates incommensurability; documents field evidence norms |
| 7 | **Composition Gap and Interaction Framework** | Revised C1–C5; 5×5 category interaction matrix; method-level interaction registry | Core position contribution |
| 8 | **Pilot Composition Study** | Preregistered factorial experiment (strongly preferred for archival; optional for pure position paper) | Original evidence beyond tables |
| 9 | **Reporting Standard and Research Agenda** | Minimum reporting vector; derived metrics; composition-benchmark design; who should build it | SoK convention: concrete agenda |
| 10 | **Related and Boundary Work** | MemGPT/Letta (cited, OUT); latent CoT / Coconut (OUT — changes accounting substrate); efficient-reasoning surveys; KV-cache methods; CCoT acronym disambiguation table | Pre-empts "you missed X" |
| 11 | **Limitations** | Single-environment measurements; host compaction not always observable; prompt-cache observability; repository mutability; fast-moving field | Honesty section |

**Draft order:** 2 → 3 → 5 → 6 → 7 → 9 → 4 → 8 → 10 → 1 → 11 (definitions, method, taxonomy first; intro last).

---

## PART C — THE TAXONOMY (revised)

### Top-level lifecycle categories

The five original intervention points are retained as the primary lifecycle map but are **not mutually exclusive**. Methods may span multiple categories (lean-ctx: Cat 2+3; MCP-Zero: trigger at generation, effect at pre-request; compaction: summarization + offload-by-reference). The taxonomy must allow multi-category entries or treat suites as bundles of primitives.

| # | Lifecycle stage | Methods |
|---|-----------------|--------|
| 1 | **Capability exposure** (which tools/schemas enter the prompt) | RAG-MCP, MCP-Zero, manual baseline (disable unused servers) |
| 2 | **Observation control** (filtering raw tool/command output before context) | RTK |
| 3 | **Context retention and reconstruction** (post-hoc compression, caching, compaction) | Headroom, lean-ctx, native compaction; LLMLingua-2 as **cross-cutting prompt-compression primitive** applicable to multiple lifecycle populations (schemas, retrieved evidence, history, demonstrations, training traces) |
| 4 | **Reasoning generation** (shortening or shaping CoT at generation time) | TokenSkip, CtrlCoT, Extra-CoT, Chain of Draft, SEER |
| 5 | **Trajectory prevention** (reducing unnecessary agent work before generation) | Ponytail, karpathy-skills |

### Orthogonal axes (required for every method row)

| Axis | Values |
|------|--------|
| **Target population** | Persistent instructions; tool schemas; retrieved evidence; tool output; files; history; explicit reasoning; generated artifacts; orchestration messages |
| **Operation** | Selection; deterministic filtering; learned extractive compression; summarization; offload-and-retrieval; caching; trained concise generation; behavioral prompting; latent replacement |
| **Trigger time** | Offline indexing; training time; session init; pre-request; after tool execution; during generation; between turns; threshold-triggered |
| **Resource effect** | PT reduction; GT reduction; PO relief; behavioral avoidance; cache improvement or degradation; visible-output-only; auxiliary overhead |
| **Recoverability** | Lossless; lossy irreversible; recoverable by handle (CCR); recoverable by re-query; regenerable from source |
| **Control locus** | Host platform; external retriever; middleware; model prompt; model weights; RL policy; agent itself |
| **Behavioral coupling** | Representation-only; candidate-set restriction; information-seeking change; reasoning-policy change; task-execution change; architecture-level change |
| **Source status** | [P] peer-reviewed · [A] arXiv preprint · [S] practitioner-reported (repo/vendor) |
| **Engineering cost** | Prompt-only / install-a-tool / build-an-index / fine-tune / RL pipeline |
| **Failure mode when wrong** | Wrong tool retrieved / info silently dropped / reasoning corrupted / needed code omitted / cache prefix destabilized |

**WHY lifecycle + orthogonal axes:** Technique-family taxonomies (retrieval vs fine-tuning vs prompting) cannot generate interaction predictions. Lifecycle reveals *where* the trajectory changes; orthogonal axes reveal *which resource* is affected, how savings recur, and where composition creates overlap, amplification, or interference.

### Corpus IN/OUT (current decisions)

| Method | Decision | Rationale |
|--------|----------|-----------|
| LLMLingua-2 | **IN** (cross-cutting primitive; primary placement = Cat 3) | TokenSkip consumes it as supervision scorer — cross-category dependency is lead exhibit for C1; can be applied to Cat 1 and Cat 2 populations with zero additional engineering |
| SEER | **IN** (Cat 4) | Training-based; pathology-elimination sub-tag; cross-examiner of TokenSkip on SE tasks |
| MemGPT/Letta | **OUT as primary intervention class** (cite in Related + Agenda) | Changes the memory architecture and context-management substrate rather than acting as an independently deployable local reduction method. Included as foundational boundary work because it explicitly manages active-context capacity |
| Latent CoT (Coconut, Compressed CoT) | **OUT** (cite theory arXiv 2601.21576 in Implications) | Generally not deployable as an external intervention on closed hosted models because it requires model-architecture or training access; changes the accounting substrate |
| Broader LLMLingua-1 family | Related Work only | LLMLingua-2 is the connective-tissue entry |

⚠️ **Acronym hazard:** "CCoT" refers to three different things in the literature (Compressed CoT latent, Concise Thoughts prompting, Contrastive CoT). Never use bare "CCoT" in the paper.

### Taxonomy build tasks

- [x] Abstract/key-results verification of arXiv papers (see evidence ledger, now separate file)
- [x] All five GitHub repos verified live; Ponytail 22% session-token figure confirmed in benchmark writeup
- [x] TokenSkip-on-SE-tasks claim resolved via SEER
- [~] Full-PDF reads for CtrlCoT, Extra-CoT baseline lists — **[PENDING]**
- [ ] Pin commit/release hashes for all repos
- [ ] Code every method row on all orthogonal axes in extraction sheet v2

---

## PART D — THE CLAIMS (revised C1–C5)

### C1 — Missing cross-population interaction evaluation

> The corpus contains construction dependencies (TokenSkip→LLMLingua-2), internally bundled systems (lean-ctx), and informal runtime coexistence with host-level mechanisms such as native compaction, but **no controlled evaluation** that estimates the marginal and interaction effects of independently deployable interventions acting on different token populations.

**Evidence:** C1 table — for each method, list exactly what its evaluation section compares against. Must be exhaustive.

**Prior-art sweep (Phase 1, DO FIRST):** Search for surveys/SoKs spanning agent-scaffolding + reasoning compression + composition. Kill-switch: if a 2025–26 survey already unifies these AND treats composition, re-scope to "extending X's frame."

### C2 — Non-comparable published accounting

> Reported results are not directly commensurable because methods differ in tasks, models, token directions (PT vs GT vs PO), session horizons, denominators, auxiliary overhead, cache effects, and quality measures. A common comparison would require assumptions or re-evaluation not supported by published evidence.

**Evidence:** C2 metric table — one row per method, primary metric only. No averaging across rows.

### C3 — Shared capacity, heterogeneous value

> Interventions affect token populations that contribute to a common session-level capacity and cost budget, but the value of removing a token depends on its lifecycle stage, recurrence, cacheability, direction (PT/GT), semantic role, and effect on subsequent behavior. **Tokens are not fungible.**

### C4 — Temporal amplification

> The session-level effect of a local token reduction depends on when the affected content enters the trajectory, how long it would otherwise remain active, whether it is replayed or cached, whether compaction removes it, and whether the intervention changes later actions.

**Formalization — three operational instantiations:**

Base form: \(S_i = \sum_{t=j_i}^{H} d_i \cdot I_{i,t}\)

where \(d_i\) = tokens saved at introduction turn \(j_i\), \(H\) = session horizon, \(I_{i,t} = 1\) if content \(i\) would remain active at turn \(t\) (0 if removed by compaction or expiry).

**Occupancy amplification** (count-based; weight = 1):

\[
S_i^{\text{occ}} = \sum_{t=j_i}^{H} d_i \cdot I_{i,t}
\]

**Cost amplification** (billing-weighted; weight = provider price at turn \(t\)):

\[
S_i^{\text{cost}} = \sum_{t=j_i}^{H} d_i \cdot I_{i,t} \cdot p_t
\]

**Cache-aware cost amplification** (cache-state-weighted; weight = price conditioned on cache mode \(m(i,t)\)):

\[
S_i^{\text{cache}} = \sum_{t=j_i}^{H} d_i \cdot I_{i,t} \cdot p_{m(i,t)}
\]

Use occupancy amplification for context-window headroom analysis; cost amplification for billing analysis; cache-aware for full accounting. All three are needed because they can diverge.

**Task:** Re-derive per-category numbers from original Cursor Context Usage reports (raw exports, not blog prose).

### C5 — Composition is not additive by default (NEW)

> Stack-level effects cannot be inferred from local savings because interventions may overlap on the same population, remove information required downstream, change later behavior, alter compaction frequency, or cause freed capacity to be consumed elsewhere.

**This is the logical bridge between C1 (nobody tested it) and Section 7 (here is what we'd expect).**

---

## PART E — ACCOUNTING MODEL AND MINIMUM REPORTING STANDARD

### Savings vocabulary

| Symbol | Definition |
|--------|------------|
| **PT** | Prompt tokens per turn (recurring while content stays in context) |
| **PT_u** | Prompt tokens billed at full uncached input rate |
| **PT_w** | Tokens written to prompt cache (first occurrence; write rate) |
| **PT_r** | Tokens read from prompt cache (discounted read rate) |
| **GT** | Generated tokens (paid once at generation; become PT on subsequent turns) |
| **PO** | Peak occupancy — maximum number of active context tokens observed during a session (`max_t O_t`) |
| **Minimum headroom** | Context-window limit W minus PO (`W − PO`) |
| **T_aux-token** | Auxiliary overhead in billable tokens (compression model inference, compaction summarization call, retrieval round-trips that produce billed tokens) |
| **C_aux-compute** | Non-token compute cost of auxiliary components (retriever CPU, local compression-model inference) |
| **L_aux** | Latency contribution of auxiliary components |
| **N_round-trip** | Number of auxiliary network round-trips |

### Minimum reporting vector (per session, per arm)

\[
(\text{success},\ PT,\ GT,\ PO,\ T_{\text{aux}},\ \text{turns},\ \text{tool calls},\ \text{retries},\ \text{latency},\ \text{cost},\ \text{compaction count},\ \text{compaction turns},\ \text{compaction tokens})
\]

**Compaction sub-record (required when host provides automatic compaction):**
- Whether compaction fired; automatic or manual
- Turn or timestamp; context occupancy before and after
- Tokens used to create the summary
- Whether tool outputs were retained, summarized, or dropped
- Task progress before and after compaction boundary

**Cache sub-record (when observable):**
- Cache hit rate; cache writes; cache reads
- First uncached turn after an intervention
- Time to first token; cache-related monetary cost

**Physical token volume (dimensionally consistent):**

\[
T_{\text{total}} = PT_u + PT_w + PT_r + GT + T_{\text{aux-token}}
\]

**Monetary cost (reported separately; not added to token counts):**

\[
C = p_u PT_u + p_w PT_w + p_r PT_r + p_g GT + C_{\text{aux-compute}}
\]

where \(p_u, p_w, p_r, p_g\) are provider-specific prices per token class.

**Derived metrics (secondary, never primary):**

\[
\text{tokens per success} = \frac{\mathbb{E}[T_{\text{total}}]}{P(\text{success})}
\qquad
\text{cost per success} = \frac{\mathbb{E}[C]}{P(\text{success})}
\]

The full vector remains primary. A method that lowers nominal PT but destroys cache reuse may be net-negative in billing. Report both tokens-per-success and cost-per-success; they can diverge.

### Compaction confound (methodological rule)

Several practitioner benchmarks run within hosts that provide automatic compaction, but generally do not report whether or when it occurred. **Do not claim compaction affected a specific benchmark unless compaction occurrence is documented for that run.**

If one experimental arm compacts at turn 12 and another at turn 17, turn-13 prompt-token counts are not comparable without normalizing for compaction boundaries. Log compaction events in every pilot arm.

---

## PART F — INTERACTION FRAMEWORK

### Category-level interaction types

additive · sub-additive · super-additive · antagonistic · enabling · mechanically incompatible · uncertain

### 5×5 category matrix (pre-register before pilot)

Build in Phase 3 from extraction sheet. Each cell: predicted interaction + mechanism + confidence.

**Top pre-registrable hypotheses (ranked by testability × novelty):**

1. **Compaction × CCR reversibility (Headroom/lean-ctx):** Do CCR handles survive a summary boundary, or does compaction orphan the archive?
2. **RTK × native compaction:** Does tool-output filtering change the probability, timing, frequency, and downstream cost of automatic compaction? (Preferred pilot — see Phase 4.)
3. **CoD × real agent stack:** Additive across disjoint populations? Secondary: does terse reasoning degrade tool-call planning?
4. **Prompt-layer contention:** Prior practitioner results suggest that reducing generated code does not necessarily reduce total session tokens (see extraction sheet, Ponytail benchmark arm comparison), motivating a prompt-layer contention hypothesis for stacked behavioral instructions.
5. **LLMLingua-2 on schemas:** Cat 3 tooling on Cat 1 population — zero engineering, never published.
6. **Dynamic tool loading × prompt cache (hypothesis, not fact):** Agent-initiated tool acquisition may trade schema-token savings against prompt-cache continuity from the changed region onward.

### Method-level interaction registry (appendix)

Per method-pair: affected populations, execution order, overlap, semantic dependency, recoverability, control-locus conflict, expected direction, confidence, testability, observable failure.

### Cache interaction claims (careful phrasing)

| Claim | Status |
|-------|--------|
| Changing tool definitions can invalidate reuse of the cached prefix from the changed region onward | Documented (Anthropic); breakpoint-dependent |
| MCP-Zero dynamic tool loading may trade schema savings against cache continuity | **Hypothesis** — host architecture may limit damage |
| RTK is less likely than dynamic schema loading to disrupt the stable tool-definition prefix | **Hypothesis** — message-suffix effects still need measurement |
| lean-ctx "prompt-cache-safe" | **Practitioner-reported** — not independently verified |
| Headroom cache effect depends on whether it rewrites only dynamic suffix vs reserializes history | **Architectural question** — flag, do not assume |

---

## PART G — EXECUTION PLAN (revised phases)

### Phase 1 — Corpus closure and prior-art verification (~1 week) ⚠️ DO FIRST

- [ ] Define search protocol (databases, strings, cutoff date)
- [ ] Run prior-art sweep; document screening log
- [ ] Finalize IN/OUT list with one-line justification each
- [ ] Freeze corpus cutoff date
- [ ] Decide paper type: position vs archival empirical SoK
- [ ] Venue shortlist with real 2026–27 deadlines
- [ ] **Kill-switch:** if existing survey unifies agent-context + reasoning compression + composition, re-scope before writing

### Phase 2 — Complete source coding (~1–2 weeks; largely done)

- [x] Extraction sheet v1 (`method-extraction_sheet_v1.md`) — canonical Phase 2 artifact
- [ ] Full-PDF reads: CtrlCoT, Extra-CoT (exact baselines, model lists)
- [ ] Pin repository commit hashes; record dates
- [ ] Build C1 evidence table and C2 metric table from extraction sheet
- [ ] Code all methods on orthogonal taxonomy axes (extraction sheet v2)
- [ ] Separate evidence ledger from this strategic plan (new file: `evidence_ledger.md`)

### Phase 3 — Formalization (~1–2 weeks)

- [ ] Finalize lifecycle taxonomy + orthogonal axes
- [ ] Formalize PT/GT/PO accounting and C4 temporal amplification
- [ ] Finalize C1–C5 wording; stress-test each against extraction sheet
- [ ] Build 5×5 interaction matrix + method-level registry
- [ ] Select pilot: confirm host exposes compaction metadata before committing
- [ ] Pre-register pilot hypotheses (GATE_SPEC discipline)

### Phase 4 — Pilot composition study (~1 weekend; strongly preferred for archival)

**Preferred candidate: RTK × native compaction**

Research question: Does tool-output filtering change the probability, timing, frequency, downstream cost, and information retention of native context compaction?

**Required measurements (not binary — minimum required for a defensible study):**
- Compaction occurred? Turn? Automatic or manual?
- Context occupancy immediately before compaction
- Size of compacted summary; tokens used by compaction call
- Post-compaction task success and trajectory divergence
- Whether shorter tool output caused different subsequent tool calls
- Amount of task-relevant information retained after the compaction boundary
- Cache hit rate per turn (if observable)

**Pilot hypothesis (pre-register before running):**
> By reducing low-value tool output before it enters history, RTK delays compaction and increases the proportion of task-relevant information retained after the first compaction boundary.

**Precondition (Phase 3 checkpoint):** Confirm Claude Code / host exposes enough information to identify automatic compaction reliably before committing to this pilot. If not, fall back to CoD × RTK (2×2 across disjoint populations).

**Design:** Factorial conditions, repeated trials (trajectories vary — single-run results are not reportable), log compaction and caching events, report quality and failure modes alongside tokens. Tasks must be long enough to approach the compaction boundary in at least some arms.

**Realistic timeline:** Approximately one week after instrumentation is validated — not less. Experimental control requirements (stable host/model versions, reliable compaction detection, comparable initial context, consistent MCP config, success grading, trajectory-divergence analysis) exceed a weekend once setup is included.

**Venue guidance:**
- Optional for pure position paper
- Strongly preferred for workshop SoK
- Effectively required for stronger archival empirical systematization

### Phase 5 — Writing (~2–3 weeks)

- [ ] Draft order: 2 → 3 → 5 → 6 → 7 → 9 → 4 → 8 → 10 → 1 → 11
- [ ] Every number traced to extraction sheet cell (not blog draft)
- [ ] Evidence-quality tags typographically preserved in paper ([P]/[A]/[S])
- [ ] Blog and paper diverge cleanly; check venue prior-publication policy for blog

### Standing risks

1. **Too close to the blog:** Mitigate with review method, accounting model, evidence tables, interaction framework, pilot.
2. **Overbroad novelty claim:** C1 narrowed; distinguish bundles from controlled composition.
3. **Arbitrary taxonomy:** Lifecycle + orthogonal axes.
4. **Local percentages mistaken for system outcomes:** Never average across methods; separate PT/GT/PO/avoidance/auxiliary.
5. **Practitioner claims as peer-reviewed evidence:** Preserve [P]/[A]/[S] tags and source versions.
6. **Platform-native confounds:** Log compaction, caching, tool-loading policy, model version in every measurement.
7. **Field velocity:** Taxonomy by lifecycle stage absorbs new methods without restructuring.

---

## PART H — EVIDENCE LEDGER SUMMARY (pointer only)

Full ledger lives in `method-extraction_sheet_v1.md` and will migrate to `evidence_ledger.md`. Key corrections retained here for quick reference:

| Method | Status | One-line correction |
|--------|--------|---------------------|
| TokenSkip | [P] | EMNLP 2025 main; uses LLMLingua-2; 79%/21% drops are truncation baseline |
| SEER | [A] IN | Resolves TokenSkip SE-task failure; pathology-elimination mechanism |
| LLMLingua-2 | [P] IN | Connective tissue Cat 3→4 |
| MCP-Zero | [A] | GPT-4.1 null result; 2,797 tools exact; venue **[PENDING]** |
| RAG-MCP | [A] | No code released; completion tokens increase |
| RTK | [S] | Headline numbers are estimates, not measured sessions |
| Headroom | [S] | 15–20% for coding agents (honest); 60–95% is JSON-heavy |
| lean-ctx | [S] | Spans Cat 2+3; ships unstudied internal bundle |
| Ponytail | [S] | −22% session tokens verified in benchmark writeup; self-corrected after issue #126 |
| karpathy-skills | [S] | Zero numbers; substantial visible adoption despite no quantitative evaluation |
| MemGPT | [A] OUT | Cite as ancestor of compaction + CCR |
| Latent CoT | [A] OUT | Changes accounting substrate |

**Named finding — evidence-maturity gradient (Section 6 named subsection):** The corpus spans peer-reviewed conference papers → unreviewed preprints → measured benchmarks → estimated savings → corrected-after-criticism benchmarks → substantial adoption with zero numbers. This gradient is an empirical finding about the field, not housekeeping. Section 6 must present it across two dimensions: **source status** [P/A/S] and **evaluation rigor** (controlled baselines + quality metric + reproducible setup → no evaluation at all). A method can be high [P] and low rigor (e.g., wrong metric scope), or low [S] and surprisingly high rigor (e.g., Ponytail's contamination-corrected benchmark). The joint distribution is the finding.

---

## REVISED THESIS (one paragraph, for intro)

> Tool exposure, environment observations, retained history, explicit reasoning, and avoidable agent work are currently treated as separate efficiency problems. Their interventions act on a common session-level context budget, but differ in when costs occur, whether savings recur across turns, what information is at risk, and whether agent behavior changes as a side effect. Existing evaluations use incompatible accounting boundaries and provide no controlled evidence about how independently deployable interventions from different lifecycle stages interact when composed. This paper systematizes the intervention space by lifecycle stage, introduces a recurrence-aware and cache-aware accounting model, documents the evaluation and composition gap through per-method evidence tables, and derives a mechanism-based interaction framework that yields testable predictions for future composition studies.

---

## Immediate next actions

1. **Phase 1 prior-art sweep** — highest stakes; everything else contingent.
2. **Confirm compaction observability** in Claude Code host before pilot commitment.
3. **Split evidence ledger** into `evidence_ledger.md` (facts) vs this file (strategy).
4. **Venue shortlist** with real deadlines.
5. **Begin extraction sheet v2** — add orthogonal-axis coding to every method row.
