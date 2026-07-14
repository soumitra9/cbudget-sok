# Method Extraction Sheet — v1 (Jul 14, 2026)
### Phase 2 artifact for "SoK: Context as a Budget"

**Provenance discipline.** Every entry below is grounded in the primary source read on Jul 14, 2026: full paper text (CoD, RAG-MCP read end-to-end; TokenSkip, MCP-Zero, SEER, LLMLingua-2, MemGPT read at abstract+methods+results depth via indexed excerpts), repo READMEs + docs (all five tools), Ponytail's full benchmark writeup, Anthropic compaction docs. Items still requiring a full-PDF pass are marked **[PENDING]**. Confidence tags: **[P]** peer-reviewed, **[A]** arXiv preprint, **[S]** self-reported (repo/vendor).

**Savings vocabulary used throughout (Q3):**
- **PT** = prompt tokens per turn (recurring — re-paid every turn the content stays in context)
- **GT** = generated tokens (paid once at generation, then convert to PT for every subsequent turn)
- **PO** = peak occupancy (distance to the context-window ceiling; determines session length)
- **VO** = visible output only (cosmetic; no billing effect)

---

## CATEGORY 1 — Tool definitions & schemas (pre-request)

### 1. RAG-MCP — Gan & Sun, arXiv 2505.03275 [A]
1. **Modifies:** which tool schemas enter the prompt. All MCP metadata lives in an external vector index; a retriever (Qwen-family encoder) selects top-k for the query; only the single best schema is injected. Optional "validation" step tests the candidate with a synthetic query before invocation.
2. **When:** per user query, before the LLM sees anything — strictly upstream of generation.
3. **Reduces:** PT (measured: 1,084 avg prompt tokens vs 2,133.84 for all-schemas "Blank" baseline ≈ 49% — the paper's "over 50%" is rounding up). **Completion tokens INCREASE** (78.14 vs Actual Match's 23.60) — the paper frames this as "more thorough reasoning."
4. **Behavior vs representation:** representation of the toolset changes; behavior changes as a consequence (selection accuracy 43.13% vs 13.62%) — the model isn't instructed differently, it's shown less.
5. **Training/deployment:** no LLM training. Requires building and maintaining a vector index, an embedding/retrieval service, and optionally the validation harness. **No code released** (open requests unanswered on HF).
6. **Eval setup:** MCPBench WebSearch subset; 20 trials per method; base LLM qwen-max-0125; answer judging by DeepSeek-v3 — though the metrics paragraph also says "Llama as Judge," an internal inconsistency worth citing carefully. Baselines: Blank Conditioning (all N schemas), Actual Match (keyword pre-filter). Stress test: N = 1→11,100 distractors from 4,400+ servers (mcp.so), 20 web-search tasks; success degrades past ~100 tools even with retrieval.
7. **Savings include/exclude:** includes prompt tokens with injected metadata. **Excludes:** the retriever's own compute and any encoder token cost; the completion-token increase; index construction/maintenance; the validation step's extra calls. Single task family (web search).
8. **Taxonomy placement:** Category 1, correct. Cleanest example of the class.
9. **Already combined?** No. Evaluated strictly alone.
10. **Plausible interactions:** (a) Mutually exclusive with MCP-Zero — same token population, different mechanism (push vs pull); they're alternatives, not a stack. (b) Sub-additive with platform-native dynamic tool loading (e.g., Cursor's GetMcpTools/CallMcpTool pattern observed in the blog measurement) — if the host already defers schemas, RAG-MCP has little left to save. (c) Fully orthogonal to categories 2–5 (disjoint populations) — the cleanest additive-stacking candidates. (d) LLMLingua-2 could compress the *retrieved* schema further — an unexplored intra-pipeline composition.

### 2. MCP-Zero — Fei, Zheng & Feng, arXiv 2506.01056 [A; cited elsewhere as NeurIPS 2025 — **[PENDING venue confirmation]**]
1. **Modifies:** the provisioning protocol itself. No schemas are preloaded; the model emits a structured *tool request* when it detects a capability gap; Hierarchical Semantic Routing (server-level match, then tool-level) resolves it; Iterative Capability Extension lets the agent build cross-domain toolchains across turns.
2. **When:** during generation, on demand, repeatedly across a trajectory — a pull model, vs RAG-MCP's per-query push.
3. **Reduces:** PT massively (98% reduction on APIBank vs full-schema injection; accurate selection from 2,797 tools that would otherwise occupy 248.1k tokens). Adds a small GT cost (the structured requests themselves).
4. **Behavior vs representation:** genuinely behavioral — the framing is "restoring tool-discovery autonomy"; the agent's control flow changes from passive selection to active acquisition. Strongest behavior-change claim in Category 1.
5. **Training/deployment:** no fine-tuning; prompt-guided request format plus a routing/matching service and an embedded tool corpus. Code released (github.com/xfey/MCP-Zero) including experiment scripts and matcher.
6. **Eval setup:** authors' own MCP-tools dataset (308 servers / 2,797 tools from the official MCP repo); benchmarks: needle-in-a-haystack over the tool corpus, APIBank multi-turn. Models: Claude-3.5-Sonnet, Gemini-2.5-Flash, GPT-4.1. Baselines: standard full-schema tool calling; query-based retrieval (≈ the RAG-MCP approach). Multi-turn consistency: ~3% accuracy drop vs >20% in baselines.
7. **Savings include/exclude:** includes schema tokens avoided on APIBank. **Excludes:** router/embedding compute; the request tokens' downstream history cost; and — critically — **the accuracy caveat: GPT-4.1 showed no accuracy improvement** (already-strong baseline). Token savings and quality gains decouple by model.
8. **Taxonomy placement:** Category 1, but flag it as a *hybrid*: the intervention point is pre-request, yet the trigger lives at generation time. The taxonomy should note trigger-time vs effect-site as separate attributes — MCP-Zero is the method that forces that distinction.
9. **Already combined?** No cross-category combination; it internally compares against retrieval (its intra-category rival).
10. **Plausible interactions:** (a) Same-slot alternative to RAG-MCP. (b) Interesting tension with compaction: after a summary boundary, does the agent remember which tools it already acquired, or re-request them (token churn)? Untested, testable. (c) With CoD-style terse reasoning: structured tool-requests depend on the model articulating capability gaps — aggressive reasoning compression could plausibly degrade request quality (cross-category antagonism candidate).

---

## CATEGORY 2 — Raw tool/command output (pre-context)

### 3. RTK (Rust Token Killer) — github.com/rtk-ai/rtk [S]
1. **Modifies:** shell command output before it enters the agent's context. A hook rewrites invocations (`git status` → `rtk git status`); deterministic per-command filters (100+ commands) compress the result. Single Rust binary, <10ms overhead, Apache-2.0, Homebrew-distributed.
2. **When:** at the tool-execution boundary, synchronously, every wrapped command — before the output ever becomes a tool-result message.
3. **Reduces:** the tool-result slice of PT — and because tool results persist in history, each filtered output is saved again on every subsequent turn (recurring PT). GT unaffected. PO improved as a consequence.
4. **Behavior vs representation:** intended as pure representation (same information, denser). De facto behavioral risk: the filter is lossy and deterministic; if it drops the one line the agent needed, the agent re-runs commands or reasons from incomplete state. The failure mode is *silent omission*.
5. **Training/deployment:** none/trivial — install binary + shell hook. The lowest-friction Category 2/3 entry.
6. **Eval setup:** **none in the formal sense.** The headline table (118K → 23.9K tokens, −80%, for a 30-min Claude Code session; −90% on pytest/cargo/go test) is explicitly labeled "Estimates based on medium-sized TypeScript/Rust projects" with assumed command frequencies. Baseline: raw command output. No task-success metric at all — savings are measured, quality is asserted.
7. **Savings include/exclude:** includes only wrapped-command outputs under an assumed usage profile. Excludes scaffolding, schemas, model reasoning, and any measure of whether filtering ever cost the agent a correct answer.
8. **Taxonomy placement:** Category 2, correct — the type specimen for pre-context filtering.
9. **Already combined?** Not formally. In the wild it runs under Claude Code, i.e., on top of native compaction and microcompaction — every real deployment is already an unmeasured stack.
10. **Plausible interactions:** (a) Overlapping population with Headroom and lean-ctx (all three eat tool output) — stacking is sub-additive at best; RTK's pre-filtered output may also defeat Headroom's content-type routing (a filtered `git diff` may no longer look like a diff). (b) Positive interaction with compaction: less bulk in history → compaction triggers later and summarizes less → less lossy summarization (compounding benefit — good pilot candidate). (c) Compounding *loss* risk: RTK-filtered output that later gets summarized by compaction has been lossy-compressed twice with no recovery path (RTK is not reversible, unlike Headroom/lean-ctx CCR).

---

## CATEGORY 3 — Bulky context & history (post-hoc)

### 4. Headroom — github.com/chopratejas/headroom (mirrored as headroomlabs-ai) [S]
1. **Modifies:** anything the agent reads — tool outputs, logs, files, RAG chunks, conversation history — via per-content-type compressors (JSON, code, logs, diffs, text) feeding a Compress-Cache-Retrieve (CCR) store. Compression is **reversible**: originals sit behind handles; the model can ask for them back (`headroom_retrieve`). Ships as Python/TS library, OpenAI/Anthropic-compatible proxy, and MCP server; `headroom wrap claude` wraps a whole agent in one command. Includes a trained compressor model (Kompress-v2-base on HF).
2. **When:** after content is produced, before the model reads it — per request when run as proxy; per explicit tool call when run as MCP server (the mode determines whether the intervention is automatic or agent-initiated, which changes its character).
3. **Reduces:** PT (60–95% on JSON-heavy data; **15–20% for coding agents** — the honest, much smaller headline for the agentic case); PO correspondingly. Retrievals *re-add* tokens later — net savings depend on redemption rate, which is not reported.
4. **Behavior vs representation:** mostly representation, plus one real behavioral affordance: the agent learns it can retrieve originals, which changes its information-seeking policy (in MCP mode, the agent must actively decide to compress/retrieve — fully behavioral there).
5. **Training/deployment:** pip/npm/Docker install; proxy or MCP config; no user-side training (vendor pre-trained the compressor model).
6. **Eval setup:** self-reported "Proof" benchmarks against uncompressed baselines; no peer review; no third-party replication found. "Same answers" is claimed, not independently measured.
7. **Savings include/exclude:** content-type-conditional (JSON number ≠ agent number — the paper must never average them). Excludes: retrieval round-trips, proxy latency, the compressor model's own compute, and the redemption-rate question entirely.
8. **Taxonomy placement:** Category 3, correct — though in proxy mode it also touches Category 2's population (tool outputs), so like lean-ctx it smudges the 2/3 border. The taxonomy should define the border by *when* (after content exists, generic) rather than *what* (which content type).
9. **Already combined?** Not with other categories. Notably, **lean-ctx ships a head-to-head comparison doc against Headroom** (docs/comparisons/vs-headroom.md) — the only place in this corpus where two tools explicitly compare, and it's intra-category rivalry, not composition.
10. **Plausible interactions:** (a) **Compaction vs claim tickets — the sharpest antagonism hypothesis in the corpus:** if native compaction summarizes away the CCR handles/markers embedded in history, the originals become unreachable; reversibility silently dies at the summary boundary. Testable, cheap, and nobody has checked. (b) Sub-additive with RTK/lean-ctx (shared population). (c) Orthogonal to Categories 1, 4, 5.

### 5. lean-ctx / LeanCTX — github.com/yvgude/lean-ctx [S]
1. **Modifies:** four things at once, one local Rust binary: (i) file reads — 10 modes (`full`, `map`, `signatures`, `diff`, `lines:N-M`, `density:X`…), tree-sitter AST across 27 languages, JIT disclosure (outline first, expand spans on demand), cached re-reads ~13 tokens; (ii) shell output — 95+ compression patterns, 270 passthrough rules; (iii) the entire outbound request via an optional local proxy (system prompt, history, tool results — claimed prompt-cache-safe); (iv) plus session memory, access guard, and a signed savings ledger. An adaptive ModePredictor learns per-file-type read modes from past sessions. Reversible by design (CCR, five recovery paths).
2. **When:** spans two intervention points — at the read/execution boundary (like RTK) and at request-assembly time (like a compression proxy).
3. **Reduces:** PT (claims 60–90% on reads and shell output); repeat-read PT nearly eliminated (~2,000 → ~13 via cache); PO via the proxy. GT untouched.
4. **Behavior vs representation:** substantially behavioral — JIT disclosure restructures *how the agent reads* (outline → targeted expansion), and ModePredictor adapts that policy over time. Not a passive filter.
5. **Training/deployment:** `lean-ctx setup`, no config claimed; local learning only (ModePredictor); crates.io/npm/AUR distribution.
6. **Eval setup:** self-serve benchmark harness with reproducible VHS demo tapes and a "benchmark proof" report by language and mode; no peer review; baselines = its own full-fidelity modes.
7. **Savings include/exclude:** read/shell-focused claims; the "~13 token re-read" is a cache hit, i.e., savings conditional on repeat access patterns. Excludes model reasoning, schemas; the proxy-mode savings are not separately quantified in the README.
8. **Taxonomy placement:** **the blog's Category 3 placement is wrong, or rather, incomplete** — LeanCTX spans Categories 2 + 3 simultaneously. The taxonomy must either allow multi-category entries or treat suites as bundles of primitives. This is a finding, not an annoyance: the most feature-rich practitioner tool doesn't fit a single-intervention taxonomy because practitioners already build stacks.
9. **Already combined?** Internally, yes — it *is* an unstudied composition (read filtering + shell filtering + request compression + caching + memory), shipped as one product with only aggregate numbers. Externally, it positions against Headroom explicitly (comparison doc) — rivalry, not stacking.
10. **Plausible interactions:** (a) Subsumes RTK's slot — running both is redundant-to-conflicting. (b) Proxy mode under Headroom's proxy = double compression, plausibly destructive. (c) Its "prompt-cache-safe" claim intersects directly with compaction's known cache-invalidation cost — one of the few places two methods make claims about the *same side effect*.

### 6. Native compaction — Claude Code + Claude API [vendor; S for third-party numbers]
1. **Modifies:** the conversation history itself — replaces older turns with a model-written summary. Three distinct mechanisms now exist and must not be conflated: (i) **Claude Code auto/manual compaction** — auto-triggers near the window limit (sources report ~95%, one code-level analysis says ~98% — cite as approximate), `/compact [instructions]` for manual, PreCompact/PostCompact hooks, post-compaction rehydration (re-reads recent files, todos, continuation instruction); (ii) **microcompaction** — large tool outputs offloaded to disk, replaced by path references, recent results kept inline ("hot tail"); (iii) **server-side API compaction** (beta `compact-2026-01-12`) — input-token trigger threshold, emits a compaction block, subsequent requests drop pre-boundary content; SDK-level `compaction_control` variant with configurable threshold (default 100K) and summarizer model.
2. **When:** episodic, threshold-triggered (not per-turn) for (i)/(iii); continuous policy for microcompaction. The only method in the corpus whose intervention timing is *state-dependent* rather than per-event.
3. **Reduces:** **PO primarily** — its purpose is extending session length past the ceiling; per-turn PT drops sharply after each boundary. It *costs* GT (the summarization call) and invalidates the prompt-cache history layer (next turn slower/costlier) — the only method with a first-class, vendor-acknowledged negative line item.
4. **Behavior vs representation:** lossy by design; documented behavioral consequences — constraints stated 100 turns ago may exist only as summary; community tooling measures "ghost lexicon" (terms that vanish post-boundary) and shifted tool-call distributions. Microcompaction changes retrieval behavior (agent re-reads from disk by path).
5. **Training/deployment:** none — it's on by default in Claude Code; API version needs a beta header and config.
6. **Eval setup:** no published benchmark. Vendor docs describe mechanism; third-party reports (e.g., "50–60% savings in multi-phase workflows") are anecdotal and must be cited as such.
7. **Savings include/exclude:** excludes the summarization call's cost, the cache-invalidation penalty, and any measure of information-loss rate. "Savings" here is really *session-length extension*, a different unit than every other method — Exhibit A for claim C2 (incommensurability).
8. **Taxonomy placement:** Category 3, correct — but flag microcompaction separately: offload-with-reference is closer to Headroom/lean-ctx CCR than to summarization, meaning Anthropic ships *two different Category 3 mechanisms* inside one product.
9. **Already combined?** **It combines with everything, invisibly.** Every practitioner benchmark run inside Claude Code (Ponytail's included) executes on top of compaction machinery. This is the corpus's universal uncontrolled variable — a methodological point the paper should make explicitly.
10. **Plausible interactions:** (a) Headroom/lean-ctx handle survival across summary boundaries (see Headroom Q10 — the killer test). (b) RTK/CoD shrink what compaction must summarize → later triggers, fewer boundaries, less cumulative loss (positive, multiplicative). (c) MCP-Zero re-acquisition after boundaries (see MCP-Zero Q10).

---

## CATEGORY 4 — Reasoning traces (generation-time)

### 7. TokenSkip — Xia et al., **EMNLP 2025 main** (arXiv 2502.12067) [P]
1. **Modifies:** the CoT the model *natively generates*. Pipeline: collect the target model's own CoT outputs → score token importance **with LLMLingua-2** → prune to target ratios γ ∈ {0.5…1.0} → LoRA-fine-tune on (question, γ) → compressed-CoT pairs. At inference, γ is specified in the prompt; the model generates the shortened trace directly.
2. **When:** generation time at inference; the real intervention is at training time.
3. **Reduces:** GT (reasoning tokens), with knock-on PT savings in any multi-turn setting — though evaluation is single-shot only, so the compounding benefit the blog highlights is *inferred, never measured, by anyone in this corpus*.
4. **Behavior vs representation:** behavioral in the strict sense — the model's output distribution is retrained.
5. **Training/deployment:** white-box model access mandatory; data generation + LoRA fine-tune per model per domain. Inapplicable to closed models. Code/checkpoints released (hemingkx/TokenSkip).
6. **Eval setup:** GSM8K, MATH-500; Qwen2.5-Instruct series (larger models degrade less; 14B: −40% tokens 313→181, <0.4% drop; at γ=0.5, ~10% drop, 1.8× latency speedup; MATH-500: −30% tokens, <4% drop). Baselines: prompt-based length reduction (fails to hit target ratios — actual ratio >0.89 when asked for 0.5) and hard truncation (catastrophic: −79% accuracy on GSM8K at 0.5). **Careful:** the 79%/21% collapses belong to the truncation *baseline*, not TokenSkip — the blog draft risked conflation.
7. **Savings include/exclude:** CoT tokens on math, single-shot. Excludes: prompt side, multi-turn compounding, the training cost, and out-of-domain behavior — which is where it breaks (SEER: on SE tasks at low γ, CoT length *increases* vs base; MathQA-Python pass@1 collapses to ~1%).
8. **Taxonomy placement:** Category 4, correct.
9. **Already combined?** **Yes — the corpus's only explicit cross-category composition:** it consumes LLMLingua-2 (Category 3, post-hoc prompt compression) as its supervision-labeling component. The categories are already entangled in practice while being evaluated in isolation. Lead exhibit for claims C1/C3.
10. **Plausible interactions:** (a) Alternative to CoD/CtrlCoT/Extra-CoT/SEER within-category. (b) Its domain fragility (SEER's findings) is the strongest evidence for the paper's "what gets silently dropped" analysis: compression tuned on math prunes tokens that were load-bearing elsewhere.

### 8. CtrlCoT — Fan et al., arXiv 2601.20467 (Zhejiang) [A]
1. **Modifies:** the generated CoT via a dual-granularity pipeline: Hierarchical Reasoning Abstraction (produces CoTs at multiple semantic granularities), Logic-Preserving Distillation (trains a logic-aware pruner that keeps indispensable cues — numbers, operators — across ratios), Distribution-Alignment Generation (aligns compressed traces with fluent inference-time style to avoid fragmentation).
2. **When:** generation time; training-time preparation (SFT-based).
3. **Reduces:** GT; claims higher accuracy at comparable-or-shorter lengths than baselines including TokenSkip, across ratios.
4. **Behavior vs representation:** behavioral (retrained output distribution), with the third component explicitly targeting *style* — an acknowledgment that pruned-token training data causes disfluent generation (a failure mode TokenSkip inherits silently).
5. **Training/deployment:** white-box; multi-stage training (abstraction generation + pruner training + aligned SFT). Heavier than TokenSkip, lighter than Extra-CoT.
6. **Eval setup:** GSM8K + MATH-500 across multiple model scales; "strong baselines" including TokenSkip. **[PENDING: exact baseline list, model list, and numbers — full-PDF read required.]** Self-declared limitation: generated length still deviates from the prompted budget, worse on weak backbones.
7. **Savings include/exclude:** math-domain GT only; single-shot; excludes budget-adherence slack (the limitation means realized savings < nominal ratio on weak models).
8. **Taxonomy placement:** Category 4, correct.
9. **Already combined?** Internally combines two *granularities* of compression (semantic + token-level) — the paper's entire premise is that naive combination fails (sequential dependency, distribution mismatch) and must be engineered. This is the corpus's only serious *intra*-category composition study — direct precedent for the paper's cross-category composition question, and evidence that composition is non-trivial even inside one category.
10. **Plausible interactions:** as TokenSkip; its distribution-alignment insight predicts a general phenomenon: any downstream consumer of compressed traces (a judge, a tool-router, compaction's summarizer) may mis-handle stylistically fragmented reasoning.

### 9. Extra-CoT — Tang et al., arXiv 2602.08324 (incl. Huawei Foundation Model Dept.) [A]
1. **Modifies:** the generated CoT at *extreme* ratios (down to ~20% of tokens). Three stages: (i) a dedicated semantically-preserved compressor (question-aware, index-based formula-aware annotation) generates high-fidelity supervision; (ii) mixed-ratio SFT teaches a spectrum of budgets; (iii) CHRPO, a hierarchical-reward RL algorithm, explicitly incentivizes accuracy at ultra-low budgets.
2. **When:** generation time; the heaviest training-time pipeline in the corpus (compressor training + SFT + RL).
3. **Reduces:** GT, stably at ratios where TokenSkip collapses.
4. **Behavior vs representation:** behavioral; RL-shaped.
5. **Training/deployment:** white-box, full SFT+RL stack — the maximal engineering-cost anchor for the taxonomy's cost axis (prompt-only CoD sits at the other end of the same category, which is analytically convenient).
6. **Eval setup:** mathematical CoT data; baselines (per the paper's own text, retrieved secondhand — **[PENDING primary confirmation]**): base model, training-free prompt/truncation, a TokenSkip re-implementation (using LLMLingua-2 as compressor — note the dependency propagates), and a Thinkless re-implementation. Auxiliary long-context eval on Pangu-Embedded-7B-V1.1.
7. **Savings include/exclude:** math-domain, single-shot GT; excludes the very large training cost and any agentic/multi-turn setting.
8. **Taxonomy placement:** Category 4, correct.
9. **Already combined?** Inherits the LLMLingua-2 dependency through its TokenSkip baseline; otherwise isolated.
10. **Plausible interactions:** as TokenSkip/CtrlCoT. Its existence sharpens the cost axis: within one category, the field now spans "add one sentence to the prompt" to "train an RL pipeline" for overlapping goals — the taxonomy's engineering-cost column does real discriminative work here.

### 10. Chain of Draft (CoD) — Xu, Xie, Zhao & He (Zoom), arXiv 2502.18600 [A] — full paper read
1. **Modifies:** nothing but the prompt. System prompt: *"Think step by step, but only keep a minimum draft for each thinking step, with 5 words at most. Return the answer after ####."* Plus few-shot exemplars with author-written drafts. The 5-word limit is a guideline, not enforced.
2. **When:** generation time, zero infrastructure — a per-step budget (unlimited steps), vs Concise-Thoughts-style global budgets that models fail to adhere to.
3. **Reduces:** GT (GSM8K: CoT ~205→CoD ~44 tokens on GPT-4o, ~190→~40 on Claude 3.5 Sonnet; sports understanding: 189.4→14.3 on Claude, the famous 92.4% cut) and latency (−48% to −76%). Also reduces PT on the input side (shorter few-shot exemplars) — the only Category 4 method with an input-side saving.
4. **Behavior vs representation:** behavioral via instruction; no weights touched.
5. **Training/deployment:** none. **The only Category 4 method deployable on black-box/hosted models** — decisive for the composability-constraints axis.
6. **Eval setup:** follows the original CoT paper's task menu — GSM8K (arithmetic), BIG-bench date + sports understanding (commonsense), synthesized 250-example coin flip (symbolic). Models: GPT-4o (2024-08-06), Claude 3.5 Sonnet (20240620). Baselines: Standard few-shot (direct answer) and few-shot CoT. Accuracy cost in the flagship few-shot setting: GSM8K 95.4→91.1 (GPT-4o), 95.8→91.4 (Claude) — "matches or surpasses" holds on commonsense/symbolic, *not* on GSM8K.
7. **Savings include/exclude:** few-shot flagship-model setting only. The paper's own §4.5 documents both exclusions: **zero-shot collapse** (Claude: CoD 65.5% vs CoT 90.4% on GSM8K — a 25-point gap; token savings also shrink) and **small-model collapse** (<3B: 10–27-point gaps vs CoT). Authors' own HF note: CoD is not a CoT replacement; hypothesized cause is absence of CoD-style traces in training data. Multi-turn/agentic settings never tested.
8. **Taxonomy placement:** Category 4, correct — the zero-cost anchor.
9. **Already combined?** The paper *proposes* combining with parallel decoding/self-speculative methods (latency, not token, techniques) but tests nothing. Not combined with any other category.
10. **Plausible interactions:** (a) The premier pilot candidate: prompt-only, black-box-safe, instantly stackable with RTK/Headroom/compaction (disjoint populations) inside a real agent session. (b) Open risk for that pilot: in agentic use, terse reasoning may degrade tool-call planning or MCP-Zero-style capability articulation — exactly the cross-category antagonism worth pre-registering. (c) Direct conflict candidate with karpathy-skills' "Think Before Coding" (one instruction says elaborate less, the other says deliberate more — both live in the same prompt if stacked).

### 11. SEER — Huang et al., arXiv 2509.14093 [A]
1. **Modifies:** the model's reasoning length policy via self-generated training: Best-of-N sampling (N=3; keep the *shortest correct* trace — explicitly suppressing loops) + an adaptive CoT-length filter calibrated to each dataset's length distribution; fine-tune on the surviving concise traces.
2. **When:** generation time; training-time self-enhancement loop.
3. **Reduces:** GT (−41.6% avg CoT length across three SE tasks) while *improving* robustness: truncations and infinite loops (up to −96.8% loops) were themselves major token sinks — SEER is the one method whose savings partly come from eliminating pathological generation rather than compressing healthy generation.
4. **Behavior vs representation:** behavioral (retrained), targeting stability as much as brevity.
5. **Training/deployment:** white-box; multiple-candidate sampling budget at training time; no external compressor dependency (contrast TokenSkip).
6. **Eval setup:** code generation, defect detection, NL code search + MathQA-Python; DeepSeek-R1-Distill-Qwen-7B; 16K token limit (an *operational constraint* framing closer to agent reality than other Cat-4 papers). Baselines: base model, length-control prompts, truncation, TokenSkip (matched N=3 budget). Findings on TokenSkip: length can *increase* vs base at low γ; MathQA-Python pass@1 ~1%.
7. **Savings include/exclude:** SE domain + one math set, single model; excludes multi-model generality and, again, multi-turn agent settings.
8. **Taxonomy placement:** Category 4; worth a sub-tag ("pathology-elimination") — its mechanism differs from prune-and-imitate.
9. **Already combined?** No; it's the corpus's designated cross-examiner of TokenSkip.
10. **Plausible interactions:** its loop findings interact with compaction: runaway reasoning loops are precisely what fills windows and forces compaction boundaries — a stability-first Cat-4 method may reduce Cat-3 activations more than a compression-first one. Good analytical vignette for Section 6.

---

## CATEGORY 5 — Unnecessary agent work (pre-generation)

### 12. Ponytail — github.com/DietrichGebert/ponytail [S — but the strongest self-run methodology in the corpus]
1. **Modifies:** the agent's *decision policy before any code is written*, via a skill/plugin (SessionStart hook) enforcing a ladder: does this need to exist → already in codebase → stdlib → platform-native → installed dependency → one line → minimum that works. Hard carve-outs: never simplify away trust-boundary validation, error handling, security, accessibility.
2. **When:** pre-generation, every turn (the rules ride in context permanently — the cure costs a few hundred tokens of the disease, acknowledged).
3. **Reduces:** GT (code) and everything downstream of it: on 12 feature tasks vs no-skill baseline (per-task baseline: 191 LOC, **349k session tokens**, $0.097, 69s) — LOC −54% (per-task range ~0% to −94%), **tokens −22%** (blog figure confirmed in the benchmark writeup, not the README headline), cost −20%, time −27%. On 6 surgical safety tasks: small size effects, 100% safe rate (vs 95% for the bare "YAGNI one-liner" prompt — the only arm that dropped a guard, a path-traversal check).
4. **Behavior vs representation:** purely behavioral — the archetype of Category 5.
5. **Training/deployment:** npm plugin install; no training.
6. **Eval setup:** the best-designed self-evaluation here, rebuilt in response to a public critique (issue #126): headless Claude Code 2.1.177 sessions, Haiku 4.5, pinned real repo (full-stack-fastapi-template @ cd83fc1), n=4 per (task, arm), metric = `git diff` added lines, four arms (baseline / ponytail / "caveman" terse-prose control / the critic's own 7-word YAGNI prompt), adversarial-input safety execution, isolated plugin loading after discovering a contamination bug (the hook was firing on the baseline arm — found, fixed, disclosed), preserved workspaces for offline rescoring. Self-listed limitations: one model, safety is a floor, n=4 nondeterminism, 4 timeout-corrupted cells.
7. **Savings include/exclude:** whole-session tokens on a real repo — **the only session-level, agent-level token measurement in the entire corpus**, which is exactly the unit the SoK argues for. Excludes other models and scales; the −54% is an honest mean dragged down by tasks with no bloat ("huge where there's bloat to cut, nothing where there isn't").
8. **Taxonomy placement:** Category 5, correct.
9. **Already combined?** The four-arm design is an *ablation of same-slot alternatives* (skill vs terse-prose vs short prompt), not a cross-category stack — but it's the closest thing to composition methodology in the corpus, and its contamination bug is a cautionary tale for any future stacking experiment (arms leak).
10. **Plausible interactions:** (a) Multiplicative with RTK: less code → fewer build/test invocations → less raw output to filter. (b) Prompt-layer contention with CoD and karpathy-skills — three instruction sets in one context; interference untested. (c) The caveman result (−20% LOC but **+7% tokens**) is a gift: it proves same-category interventions can *look* similar and diverge in token effect — the SoK's argument in one row.

### 13. andrej-karpathy-skills — github.com/multica-ai/andrej-karpathy-skills [S — no quantitative claims at all]
1. **Modifies:** agent behavior via a single CLAUDE.md distilling four principles from Karpathy's public observations: Think Before Coding (state assumptions, present interpretations, push back, stop when confused), Simplicity First, Surgical Changes, Goal-Driven Execution (tests-first, verifiable criteria). Explicit tradeoff note in the file: "biases toward caution over speed."
2. **When:** pre-generation, every turn (persistent context residency).
3. **Reduces:** nominally GT (its success criteria — fewer unnecessary diffs, fewer rewrites, smaller PRs — are token metrics wearing different names). **No measurement exists.** Zero benchmarks, zero numbers.
4. **Behavior vs representation:** purely behavioral.
5. **Training/deployment:** copy one file.
6. **Eval setup:** none. Highest community adoption in the corpus with the least evidence — the far pole of the evidence-quality gradient (Section 5 material).
7. **Savings include/exclude:** n/a — nothing reported.
8. **Taxonomy placement:** Category 5, correct.
9. **Already combined?** Users merge it with project CLAUDE.md files by instruction ("merge with project-specific instructions as needed") — informal, universal, unmeasured composition.
10. **Plausible interactions:** (a) "Think Before Coding" plausibly *increases* reasoning tokens (more deliberation, more clarifying questions = more turns) while decreasing code tokens — a method whose net token effect could be negative or positive depending on task mix; ideal illustration that Category 5's unit of account is the *session*, not the trace. (b) Direct instruction-level tension with CoD (elaborate vs compress). (c) Same-slot overlap with Ponytail (Simplicity First ≈ the ladder, minus enforcement and minus the safety carve-outs).

---

## CROSS-CATEGORY DEPENDENCY — now in scope

### 14. LLMLingua-2 — Pan et al., **ACL 2024 Findings** (arXiv 2403.12968, Microsoft) [P]
1. **Modifies:** any prompt text, post-hoc, task-agnostically. Mechanism: GPT-4 data distillation produces an extractive compression dataset (MeetingBank); prompt compression is reformulated as **token classification** (preserve/discard) with a BERT-level bidirectional encoder — fixing LLMLingua-1's two flaws (unidirectional perplexity; objective misaligned with compression).
2. **When:** post-hoc, immediately before dispatch, on arbitrary text — the most population-agnostic method here.
3. **Reduces:** PT. Family claims up to 20x (LLMLingua-1 on long contexts); LLMLingua-2 emphasizes faithfulness + 3–6x speed over its predecessor rather than deeper ratios.
4. **Behavior vs representation:** representation only — the LLM never knows compression happened (no retrieval affordance, unlike CCR systems; loss is silent and irreversible).
5. **Training/deployment:** vendor-trained small encoder; user runs local inference; no LLM access needed — deployable in front of black-box models.
6. **Eval setup:** in-domain MeetingBank (QA F1 86.92 vs LLMLingua's 67.52; summarization BERTScore 88.77 vs 86.42) + out-of-domain benchmarks; baselines: Selective-Context, LLMLingua(-1). Peer-reviewed.
7. **Savings include/exclude:** text-compression quality metrics; excludes agentic settings entirely — no one has published its effect on *tool schemas, tool outputs, or agent history*, despite it being mechanically applicable to all three.
8. **Taxonomy placement:** Category 3 (post-hoc), correct — but its real role in the SoK is as connective tissue.
9. **Already combined?** **Yes, twice, across category lines:** consumed by TokenSkip (and Extra-CoT's TokenSkip baseline) as the importance scorer for Category 4 training data. The prompt-compression family and the CoT-compression family are already one supply chain — evaluated as strangers.
10. **Plausible interactions:** (a) Could compress Category 1's population (schemas) and Category 2's (tool output) today, with zero engineering — the cheapest unexplored cross-category experiments in the space. (b) Applied on top of RTK-filtered output: near-certainly diminishing returns (RTK already stripped the low-information tokens LLMLingua-2 would classify as discardable).

---

## BOUNDARY CASES — proposed IN/OUT decisions with rationale

### 15. MemGPT-style memory — Packer et al., arXiv 2310.08560 (UC Berkeley → Letta) [A]
1. **What it actually does:** OS-inspired virtual context management: a fixed **main context** (≈ RAM) + **external context** (≈ disk); the LLM manages its own paging via function calls (append to working context, archival search, retrieval); a queue manager + memory-pressure interrupts govern eviction; on flush, evicted messages are **recursively summarized** (new summary = f(old summary, evicted messages)).
2. **When:** continuously, as an architecture — not an intervention applied to an existing agent.
3. **Reduces:** nothing per turn. Main context is deliberately kept *full*; the system's goal is **unbounded effective context**, i.e., it changes what PO *means* rather than lowering it. Tokens are relocated, not saved; paging itself costs function-call tokens.
4. **Behavior:** maximally behavioral — the agent's core loop is memory management.
5. **Training/deployment:** framework adoption (now Letta); no model training in the original design.
6. **Eval setup:** document analysis + multi-session conversation (consistency/recall) vs fixed-context baselines — task-capability metrics, not token metrics.
7. **Reported savings:** none claimed; the paper's currency is capability past the window, not cost below it.
8. **Taxonomy placement → OUT, with a documented rationale:** the taxonomy classifies interventions on a given budget; MemGPT re-architects the budget. Including it would dissolve the taxonomy's unit of analysis. **But cite it twice:** (i) as the intellectual ancestor of compaction (recursive summarization) and of microcompaction/CCR (paging with references); (ii) in the research agenda — a mature joint-optimization framework would look more like an OS scheduler (MemGPT's metaphor) than like any single method in Categories 1–5. The boundary case earns its keep by naming where the field is heading.
9. **Already combined?** It *contains* primitive versions of Categories 3's mechanisms; that's precisely why it's out — it's a system, not a term in a sum.
10. **Interactions:** running any Category 1–5 method *inside* a MemGPT-style architecture changes their economics (paging makes information loss recoverable, so lossy filters like RTK become safer) — one paragraph of Section 6, no more.

### 16. Latent chain-of-thought — Coconut (Hao et al., arXiv 2412.06769, Meta) and Compressed CoT (Cheng & Van Durme, arXiv 2412.13171) [A]; theory: arXiv 2601.21576 [A]
1. **What they actually do:** move reasoning out of token space. Coconut feeds the final hidden state back as input, reasoning in a continuous latent space; Compressed CoT generates variable-length *contentful contemplation tokens* — dense continuous representations of reasoning chains.
2. **When:** generation time, but below the token level.
3. **Reduces:** GT to ~zero by *eliminating the representation being counted* — which is exactly the problem: "token savings" is no longer a meaningful measurement of them. They also shift cost into forward passes that token accounting doesn't see.
4. **Behavior:** retrained reasoning substrate; interpretability is lost (CoD's paper notes Coconut's accuracy drop on GSM8K and its inapplicability to black-box models — a citable independent characterization).
5. **Training/deployment:** white-box, custom training loops; incompatible with hosted agents, which are the SoK's setting.
6. **Eval:** math/logic benchmarks vs explicit CoT; units are accuracy + latency, not context tokens.
7. **Savings include/exclude:** incommensurable by construction (see Q3).
8. **Taxonomy placement → OUT, three-line rationale for the paper:** (i) they change the accounting substrate rather than economizing within it; (ii) they're unusable in the deployed-agent setting the SoK addresses; (iii) including them would force the unified metric to price hidden-state compute, which is Category-error territory (that's the KV-cache/inference-cost literature, already excluded in Section 2). **One theoretical citation stays IN:** arXiv 2601.21576 proves learning signal for internalizing high-order reasoning dependencies decays exponentially ("Order-r Interaction") — a limit result that bounds *all* Category 4 compression ambitions, latent or token-level. Cite it in Implications.
9/10. **Combined/interactions:** n/a beyond the theory citation.
⚠️ **Acronym hazard for the paper:** "CCoT" is used in the literature for *three different things* — Compressed CoT (Cheng & Van Durme, latent), Concise Thoughts (Nayab et al. 2407.19825, global-token-budget prompting, discussed in the CoD paper), and occasionally Contrastive CoT. Never use the bare acronym.

---

## SYNTHESIS APPENDIX — what the sheet establishes for the SoK's claims

**For C1 (isolation):** confirmed for every method: no cross-category composition is *evaluated* anywhere. Nuances that sharpen rather than weaken the claim: TokenSkip *consumes* a Category 3 method without evaluating the combination as a combination; CtrlCoT proves intra-category composition is hard enough to be a whole paper; lean-ctx *ships* a multi-category stack with only aggregate self-reported numbers; every in-agent benchmark silently runs on top of compaction.

**For C2 (incommensurability), the per-method primary metric in one list:** RAG-MCP: selection accuracy + prompt tokens (20 trials). MCP-Zero: selection accuracy + avg tokens. RTK: estimated tokens, no quality metric. Headroom: tokens by content type, "same answers" asserted. lean-ctx: tokens by language/mode. Compaction: session continuation, no published metric. TokenSkip/CtrlCoT/Extra-CoT: math accuracy vs compression ratio. CoD: accuracy + output tokens + latency. SEER: pass@1 + CoT length + loop rate. Ponytail: LOC + session tokens + cost + time + safety rate. karpathy-skills: nothing. LLMLingua-2: QA F1/BERTScore at ratio. No two categories share a unit; only Ponytail measures at session level.

**For C4 (recurrence asymmetry):** the sheet's PT/GT/PO decomposition shows Categories 1–3 save recurring PT, Category 4 saves GT that *converts* to PT, Category 5 saves at the session level — three different compounding profiles no paper models.

**Top pre-registrable interaction hypotheses (Section 6 seeds), ranked by testability × novelty:**
1. **Compaction × Headroom/lean-ctx reversibility:** do CCR handles survive a summary boundary, or does compaction orphan the archive? (Cheap, binary, damning either way.)
2. **CoD × real agent stack (RTK on/off):** additive-savings prediction across disjoint populations; secondary hypothesis: CoD degrades tool-call planning (SEER-style pathology check).
3. **RTK × compaction frequency:** filtered output → later compaction triggers → fewer summary boundaries → measurably less information loss.
4. **Prompt-layer contention:** ponytail + karpathy-skills + CoD in one context — do instructions interfere (caveman's +7% tokens proves same-layer divergence is real)?
5. **LLMLingua-2 on schemas:** Category 3 tooling applied to Category 1's population — zero engineering, never published.
