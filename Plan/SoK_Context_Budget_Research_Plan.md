# Research Plan — SoK: The Context Budget
### Working title: "SoK: Context as a Budget — Systematizing Token-Efficiency Interventions in LLM Agents"

---

## PART A — WHAT, WHY, HOW (the one-paragraph version)

**WHAT:** A Systematization-of-Knowledge / position paper arguing that the ~12+ published methods for reducing LLM agent token consumption are point-solutions to five slices of a single shared resource — the context window — and that the field lacks (a) a unified taxonomy by intervention point, (b) commensurable evaluation, and (c) any study of how interventions compose or interfere when stacked.

**WHY:** Every existing method evaluates itself in isolation, on its own metric, in its own domain. A practitioner assembling an agent stack today has no principled way to predict whether combining methods is additive, redundant, or harmful. No published work frames these as a jointly-optimized resource-allocation problem (this gap is the thesis — it must be *verified*, not assumed; see Phase 1).

**HOW:** (1) Verify the gap with a rigorous prior-art sweep. (2) Build the taxonomy from primary sources only — every claim traced to a paper/repo, no numbers from memory. (3) Formalize the "shared budget" observation into 3–4 concrete, defensible claims. (4) Construct the cross-method comparison table using each paper's own reported numbers (no re-running benchmarks). (5) Optionally, one small original stacking experiment in the author's own measured environment. (6) Write, targeting an SoK-friendly venue or a strong workshop.

---

## PART B — PAPER SECTION STRUCTURE (what goes where, and why)

| # | Section | Content | Why it exists |
|---|---------|---------|---------------|
| 1 | **Introduction** | The token bill framing; the Cursor field measurement as motivating anecdote (scaffolding ≈ 97% of turn 1; 3-word follow-up costing 7× with MCPs on); the thesis: five taps, one budget, zero joint study | Hooks with a concrete measured number; states the position up front |
| 2 | **Scope & Definitions** | Precise boundary: *context-token* budget (what enters the prompt each turn), explicitly excluding KV-cache/memory-bandwidth optimization, quantization, and speculative decoding (inference-cost, not context-cost). Define: recurring vs one-time token cost; fungibility of saved tokens; turn-level vs session-level accounting | SoK papers live or die on scope discipline; without this boundary, reviewers ask "why isn't FlashAttention in here" |
| 3 | **The Anatomy of the Bill (empirical grounding)** | The four-scenario measurement, formalized: category-by-category breakdown, what's frozen vs what grows, the conversation-history compounding effect | Gives the taxonomy an empirical skeleton rather than an armchair one; this is original data already in hand |
| 4 | **Taxonomy** | Five intervention points × comparison axes (detailed in Part C) | The core systematization contribution |
| 5 | **The Isolation Observation** | Evidence that no method evaluates cross-category composition; metric incommensurability analysis; the missing resource-allocation frame (detailed in Part D) | The core *position* contribution |
| 6 | **Interaction Analysis (analytical)** | For each pair of categories, reason about predicted interaction: independent / overlapping / antagonistic. E.g., RTK and Headroom both target tool output (overlap candidate); Chain of Draft and compaction target different token populations (independence candidate); Ponytail reduces the very output RTK would filter (partial cannibalization candidate) | Turns the observation into testable predictions — this is what elevates it above "someone should study this" |
| 7 | **(Optional) Pilot Measurement** | One stacking experiment, 2 methods from different categories, same methodology as the four-scenario setup | Small, honest, original evidence; explicitly framed as a pilot, not a benchmark |
| 8 | **Implications & Research Agenda** | What a proper joint-optimization study would require: shared task suite, unified metric (tokens-per-solved-task?), composition benchmark; who should build it | SoK convention: end with a concrete agenda, not vibes |
| 9 | **Related Work** | Adjacent families deliberately excluded or only touched: prompt compression (LLMLingua family), agent memory systems (MemGPT-style), KV-cache methods, efficient-reasoning surveys | Pre-empts the "you missed X" review |
| 10 | **Limitations** | Single-environment measurements; reported numbers not independently reproduced; fast-moving field | Honesty section; matches pre-registration discipline used in the CARS paper |

---

## PART C — THE TAXONOMY: WHAT / WHY / HOW

**WHAT it is:** A classification of every method by **where in the token lifecycle it intervenes**, crossed with axes that are commensurable *across* categories even when raw performance numbers are not.

The five intervention points (from the blog draft, now formalized):

1. **Pre-request (tool schemas):** RAG-MCP (arxiv 2505.03275), MCP-Zero (arxiv 2506.01056), plus the manual baseline (disable unused servers)
2. **Pre-context (raw output filtering):** RTK (github.com/rtk-ai/rtk)
3. **Post-hoc (context already produced):** Headroom (github.com/headroomlabs-ai/headroom), lean-ctx (github.com/yvgude/lean-ctx), native compaction
4. **Generation-time (reasoning traces):** TokenSkip (2502.12067), CtrlCoT (2601.20467), Extra-CoT (2602.08324), Chain of Draft (2502.18600)
5. **Pre-generation (behavioral prevention):** Ponytail (github.com/DietrichGebert/ponytail), karpathy-skills (github.com/multica-ai/andrej-karpathy-skills)

The comparison axes (these are the actual intellectual work):

| Axis | Values | Why it's commensurable across categories |
|------|--------|------------------------------------------|
| Intervention point | 1–5 above | Definitional |
| Token savings (as reported) | % + absolute, with task context | Cited, never averaged across incomparable tasks |
| Quality delta (as reported) | accuracy/pass@1/task-success change | Same |
| Engineering cost | prompt-only / install-a-tool / build-an-index / fine-tune / RL pipeline | Ordinal, applies to everything |
| Recurrence of savings | per-turn recurring vs one-time | Structural property, applies to everything |
| Token population targeted | schemas / tool output / history / CoT / generated code | Determines overlap — the key input to Section 6 |
| Failure mode when wrong | wrong tool retrieved / info silently dropped / reasoning corrupted / needed code omitted | The adversarial axis — what each method risks discarding |
| Composability constraints | requires model access? requires shell hook? requires training? | Determines which combinations are even mechanically possible |

**WHY this taxonomy and not another:** Existing organizational schemes (where they exist at all) group by technique family (retrieval vs fine-tuning vs prompting). Grouping by *intervention point* is what makes the budget framing visible: it shows the five methods as five taps on one pipe, and it directly generates the interaction predictions in Section 6. A technique-family taxonomy cannot do that.

**HOW to build it (tasks):**
- [~] Abstract/key-results-level verification of all 6 arXiv papers COMPLETE (see Part F ledger). Remaining: full-PDF reads for methodology details, exact tables, and evaluation-section extraction (needed for the C1 evidence table).
- [~] All five GitHub repos verified live with READMEs read (see Part F). Remaining: pin commit/release hashes; read Ponytail's full benchmark writeup (benchmarks/results/2026-06-18-agentic.md) to verify the "22% fewer tokens" figure, which does NOT appear in the current README headline.
- [ ] Record self-reported numbers *as self-reported* (distinguish typographically in the paper from peer-reviewed numbers — this distinction is itself a finding about the field's evidence quality). NOTE: this distinction has shifted — TokenSkip is now EMNLP 2025 main conference (peer-reviewed), not a preprint.
- [x] **RESOLVED (Jul 14, 2026):** The "TokenSkip produces longer output on SE tasks" claim is confirmed and sourced. SEER (arxiv 2509.14093, v2) evaluates TokenSkip as a baseline on software-engineering tasks (DeepSeek-R1-Distill-Qwen-7B, 16K token limit) and reports: at low compression settings TokenSkip's "average CoT length even increases compared to the base model, leading to more truncation and lower accuracy," and on MathQA-Python TokenSkip's pass@1 collapses to ~1% regardless of compression setting. Cite SEER directly; the "~1% pass@1" collapse is stronger than the blog's ">20 points" phrasing — use SEER's actual numbers.
- [ ] Decide in/out for borderline methods and document the decision: **LLMLingua-2 is now firmly IN** — verification revealed TokenSkip *uses LLMLingua-2 as its token-importance scorer*, a direct dependency linking the CoT-compression family to the prompt-compression family (this cross-category dependency is itself evidence for the paper's unification thesis). MemGPT-style memory (likely OUT — architecture, not intervention), SEER (IN under generation-time — training-based, self-enhancing), CCoT/latent-CoT (likely OUT — changes the representation, not the token bill, but must be justified).

---

## PART D — THE OBSERVATION: WHAT / HOW / WHY

**WHAT the observation is (decomposed into four defensible claims):**

- **C1 — Isolation:** No paper in the corpus evaluates its method in combination with a method from another category. (Falsifiable; verified by reading every evaluation section.)
- **C2 — Incommensurability:** The categories use disjoint metrics (GSM8K accuracy vs shell-output bytes vs diff size vs tool-selection accuracy), so cross-category comparison is currently impossible even in principle from published numbers alone.
- **C3 — Fungibility:** A token saved anywhere buys the same thing — headroom before the context ceiling — so the budget is genuinely shared, making C1 an actual problem rather than a taxonomic curiosity.
- **C4 — Recurrence asymmetry:** Savings in frozen scaffolding (schemas) recur identically every turn; savings in conversation compound differently (each saved token is *re-saved* every subsequent turn). No paper accounts for this — all report single-shot or single-task savings. (Directly supported by the four-scenario measurement: scaffolding frozen token-for-token across turns, conversation quadrupling.)

**HOW to establish it (tasks):**
- [ ] For C1: build an evidence table — for each of the 12+ methods, list exactly what its evaluation section compares against. This table goes in the paper (or appendix). It is the proof of the gap, and it must be exhaustive or a reviewer kills the paper with one counterexample.
- [ ] For C1, the dangerous part — **the prior-art sweep (Phase 1, do this FIRST):** search for existing surveys/SoKs that already span these categories. Known adjacent threats to check: efficient-reasoning surveys (e.g., "Stop Overthinking"-style CoT-efficiency surveys), prompt-compression surveys, "context engineering" papers/surveys from 2025–2026, agent-efficiency benchmarks. The thesis survives if none of them (a) include agent-scaffolding/tool-schema costs AND (b) treat composition. If one does, the paper pivots to "extending X's frame" — better to know in week 1 than at review.
- [ ] For C2: extract the primary metric of every paper into one row each; the resulting table *visibly* demonstrates incommensurability.
- [ ] For C4: re-derive the exact per-category numbers from the original Cursor Context Usage reports (raw screenshots/exports, not the blog prose).

**WHY the observation matters (the paper's stakes, to be argued in Section 5):**
1. Practical: agent developers stack these tools today (RTK + compaction + a rules file is a realistic real stack) with zero evidence about interaction.
2. Scientific: interaction effects are plausibly non-trivial in both directions — overlap (two methods compressing the same token population → sub-additive) and antagonism (a filter destroying the signal a later compressor needs, or compressed reasoning degrading the agent's tool choices, which *increases* tool-output tokens).
3. Field-level: without a shared metric, the subfields cannot learn from each other; the paper proposes one (candidate: **tokens-per-successfully-completed-task**, session-level — to be stress-tested during writing).

---

## PART E — EXECUTION PLAN (phased, with kill-switches)

### Phase 1 — Gap verification & scoping (~1 week) ⚠️ DO FIRST
- [ ] Prior-art sweep (Part D task). **Kill-switch:** if a 2025–26 survey already unifies agent-context + reasoning compression + composition, stop and re-scope before writing anything.
- [ ] Finalize in/out list of methods with one-line justification each.
- [ ] Pick 2–3 target venues and read their SoK/position-paper expectations. Candidates to research (do not assume): IEEE S&P SoK track fit (security framing may be a stretch — assess honestly), NeurIPS/ICLR position-paper tracks, EMNLP/ACL survey-friendly tracks, top workshops (efficient-ML, LLM-agents workshops at NeurIPS/ICML/ICLR — realistic first target given timeline). **[RESEARCH: actual 2026–27 deadlines before committing.]**

### Phase 2 — Source reading & extraction (~2–3 weeks)
- [ ] Full-paper reads + extraction sheet (one row per method, columns = taxonomy axes). Every cell cites page/section of the source.
- [ ] Build the C1 evidence table and C2 metric table as byproducts.
- [ ] Resolve the [VERIFY] TokenSkip-on-SE-tasks claim.
- [ ] Pin repo versions; capture self-reported numbers with dates (repos change).

### Phase 3 — Analysis (~1–2 weeks)
- [ ] Fill the interaction matrix (Section 6): 5×5 categories, each cell = predicted interaction + mechanism + confidence. This is pure reasoning from the extraction sheet; it must be done *before* any pilot experiment (pre-registration discipline — same as GATE_SPEC on the CARS paper: predictions written down before data).
- [ ] Stress-test the proposed unified metric against each category; document where it breaks.

### Phase 4 — Optional pilot (~1 weekend, decide after Phase 3)
- [ ] Pre-register: pick the ONE cell of the interaction matrix that is (a) mechanically testable in the existing Cursor/Claude Code setup, (b) has a clear prediction. Leading candidate: Chain of Draft (category 4) × RTK or MCP-off (category 2/1) — additive prediction. Write expected outcome + what would count as interference *before* running.
- [ ] Run with the exact four-scenario methodology (same environment, same prompts, one variable at a time, report as field measurement not benchmark).
- Skipping this phase is fine; the paper stands without it. Include only if Phase 3 produces a genuinely crisp testable prediction.

### Phase 5 — Writing (~2–3 weeks)
- [ ] Draft in section order 2 → 4 → 5 → 6 → 3 → 8 → 9 → 1 → 10 (definitions and taxonomy first; intro last).
- [ ] Systematic full-pass editorial review against the extraction sheet — every number in the draft traced to a source cell (not to the blog draft, which is a secondary source of its own claims).
- [ ] The blog post and the paper must diverge cleanly: blog = narrative field guide; paper = systematization with evidence tables. No self-plagiarism issues since the blog is informal, but check target venue's prior-publication policy for blog posts. **[VERIFY per venue]**

### Standing risks (track throughout)
1. **Field velocity:** CtrlCoT and Extra-CoT are weeks–months old; new methods will appear mid-writing. Mitigation: taxonomy is by intervention point, so new methods slot in without restructuring — say so explicitly in the paper.
2. **Scooping on the composition question:** the interaction framing is obvious-in-retrospect; move Phase 1–3 fast.
3. **"This is just a blog post in LaTeX" review:** mitigated by the C1/C2 evidence tables, the interaction matrix, and the formal claims — none of which exist in the blog.
4. **Self-reported GitHub numbers treated as evidence:** always typographically flagged; framed as "practitioner-reported," which doubles as a finding about evidence standards in the tooling ecosystem.

---

## PART F — VERIFICATION LEDGER (completed Jul 14, 2026)

Every method checked against primary sources. Status codes: ✅ verified as blog stated · ⚠️ verified with material corrections · 🔶 self-reported only (no peer review).

| Method | Status | Verified facts & corrections vs blog draft |
|--------|--------|--------------------------------------------|
| **TokenSkip** | ✅⚠️ | arXiv 2502.12067; **published EMNLP 2025 main** (aclanthology 2025.emnlp-main.165) — cite the conference version. Qwen2.5-14B-Instruct: 40% reduction (313→181) on GSM8K, <0.4% drop — exact match. **Key discovery: uses LLMLingua-2 as its token-importance scorer** (cross-category dependency; feeds the unification thesis). Own paper: at ratio 0.5, ~10% drop on GSM8K; the dramatic 79%/21% drops are its *truncation baseline*, not TokenSkip — don't conflate. Code: github.com/hemingkx/TokenSkip |
| **CtrlCoT** | ✅ | arXiv 2601.20467, Zhejiang Univ. (Fan et al.). GSM8K + MATH-500, multiple model scales, claims SOTA over baselines incl. TokenSkip. Limitation per own paper: generated CoT length can deviate from prompted budget, worse on weak backbones |
| **Extra-CoT** | ✅ | arXiv 2602.08324 (Tang et al., incl. Huawei Foundation Model Dept.). 3-stage: formula-aware compressor + mixed-ratio SFT + CHRPO RL. Explicitly outperforms TokenSkip at high compression ratios. Math-domain only (GSM8K-class tasks) — the "stable at 20% tokens" claim must be scoped to math |
| **Chain of Draft** | ✅⚠️ | arXiv 2502.18600 (Xu, Xie, Zhao, He). Exact prompt: "≤5 words per step." Uses "as little as 7.6% of tokens" (= up to 92.4% cut) — blog's "90%+" is fair. **Correction:** authors publicly caution CoD is *not* a CoT replacement — performance inconsistent across tasks/models, weaker in zero-shot and on small models (v2 §4.5). The paper must carry this caveat |
| **SEER** | ✅ NEW | arXiv 2509.14093 — now IN scope (generation-time, training-based). 41.6% avg CoT reduction on 3 SE tasks, pass@1 preserved/improved, loops mitigated up to 96.8%. **Resolves the open [VERIFY]:** SEER's own evaluation shows TokenSkip increasing CoT length vs base at low γ and collapsing to ~1% pass@1 on MathQA-Python |
| **RAG-MCP** | ✅⚠️ | arXiv 2505.03275 (Gan & Sun). >50% prompt-token cut; 43.13% vs 13.62% selection accuracy — exact match. **Correction: no public code released** (open requests on HF unanswered) — reproducibility caveat for the paper |
| **MCP-Zero** | ✅⚠️ | arXiv 2506.01056 (Fei, Zheng, Feng); referenced elsewhere as NeurIPS 2025 — **[VERIFY publication venue before citing as such]**. 308 servers / **2,797** tools (blog said ~2,800 — use exact). 98% token reduction on APIBank. **Important nuance:** gains on Claude-3.5-Sonnet & Gemini-2.5-Flash; **GPT-4.1 showed no accuracy improvement** (already-strong baseline) — token savings ≠ accuracy gains, model-dependent. Code: github.com/xfey/MCP-Zero |
| **RTK** | 🔶⚠️ | Repo live (rtk-ai/rtk), Apache-2.0, Homebrew-distributed, active. Headline: 60–90% reduction. **Correction: the 118K→23.9K (-80%) table is explicitly labeled "Estimates based on medium-sized TypeScript/Rust projects" — an estimate, not a measured session.** pytest/cargo/go test −90% confirmed as estimates. Blog's "their own estimate" phrasing was right; the paper must not upgrade it to "measured" |
| **Headroom** | 🔶⚠️ | Repo live. **New numbers the blog lacked: 60–95% fewer tokens for JSON data, 15–20% for coding agents** (README headline). Library + proxy + MCP server; reversible compression; ships a trained model (Kompress-v2-base on HF). Canonical repo appears to be chopratejas/headroom (headroomlabs-ai mirrors/redirects) — pin the right one |
| **lean-ctx** | 🔶⚠️ | Repo live, on crates.io/npm/AUR. **Correction: much broader than blog's "AST-aware file reads" framing** — now a full local context layer (proxy compressing every request, session memory, guard, savings ledger, 76 MCP tools). Claims: 60–90% overall; cached re-reads ~2,000→~13 tokens (≈99%) — matches blog's "up to 99% on repeat reads." Taxonomy placement now spans categories 2+3 — handle explicitly |
| **Ponytail** | 🔶⚠️ | Repo live, MIT, npm-distributed. **Significant correction: README now self-corrects its own earlier benchmark.** Current honest numbers: ~54% less code = *mean* across 12 feature tasks (n=4, Haiku 4.5, real FastAPI+React repo), **up to 94% as per-task ceiling** (over-built date picker), near-zero where code already minimal; ~20% cheaper, ~27% faster; earlier flat "80–94%" figure disavowed as unfair single-shot. Blog's "22% fewer tokens" not in current README headline — verify against benchmarks/results/2026-06-18-agentic.md or drop. This self-correction episode is itself usable evidence about evidence-quality norms in the tooling ecosystem |
| **karpathy-skills** | 🔶✅ | Repo live (multica-ai). Single CLAUDE.md, four principles exactly as blog describes, derived from Karpathy's Jan 2026 X post. No quantitative claims at all — pure prompt file. The zero-benchmark + highest-adoption combination is a data point for the C2 incommensurability argument |

**Ledger-driven additions to the paper:**
1. TokenSkip→LLMLingua-2 dependency: the categories are already entangled in practice while being evaluated in isolation — sharpest single piece of evidence for C1/C3.
2. MCP-Zero's GPT-4.1 null result: token savings and task-quality effects decouple per model — supports the need for a unified metric (C2) and previews interaction-analysis subtleties (Section 6).
3. The evidence-quality gradient (peer-reviewed ↔ estimate tables ↔ disavowed benchmarks ↔ no numbers at all) is now documented per method and becomes a short subsection of Section 5.

---

## Immediate next actions (this week)
1. Phase 1 prior-art sweep — the single highest-stakes task; everything else is contingent on it.
2. Draft the in/out scope list for borderline methods (LLMLingua family, SEER, MemGPT, latent-CoT).
3. Venue shortlist with real deadlines.
