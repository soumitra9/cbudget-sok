# Blog Plan — "Where Do All My Tokens Go?" (working title)

A Medium post mapping token consumption in agentic AI coding tools (Claude Code,
Cursor) and the full landscape of what exists to fight it — papers, prompts, tools.

---

## 0. Ground rules (read before writing a single word)

1. **This post is a map, not an argument.** It catalogs what contributes to token
   consumption and what exists at each layer. It does NOT propose a solution,
   NOT synthesize a framework, NOT end with takeaways.
2. **Do not disclose the paper.** The joint-optimization thesis (B = S + H + R + O,
   marginal-utility equalization, cross-channel allocation) must NOT appear —
   not as an equation, not as a "what if these were coordinated?" question, not
   as a closing gesture. The post describes each channel and its fixes in
   isolation, exactly the way the current literature does. If a sentence starts
   drifting toward "notice these all work separately..." — delete it.
3. **No takeaways section. No conclusion section. No "final thoughts."** The post
   ends after the last catalog entry (Section 3d) with at most 2–3 sentences of
   plain sign-off (see §4 below). No summary, no bulleted lessons, no CTA
   beyond a light "what's eating your context window?" comment prompt.
4. **It must read human.** Voice rules in §5 are mandatory, not decorative.
5. **No lifted figures.** Every diagram is redrawn original work (specs in §6).
   arXiv figures are author-copyrighted; GitHub README images belong to their
   repos. Redrawing also gives the post one consistent visual language.
6. **Every number gets a source.** All stats used are listed in §7 with their
   links. If a number can't be traced to that table, it doesn't go in the post.

---

## 0b. Deliverable format (how the draft is produced and used)

1. **The draft is a single Markdown file: `blog_draft.md`.** The author will
   paste its contents into Medium's editor (Medium converts pasted headers,
   bold, and links cleanly; it does not import raw .md files directly).
2. **All figures are generated separately** as individual PNG files, after
   the author picks the visual style (Excalidraw hand-drawn vs. dark
   polished — decision still open; prose drafting does not block on it).
3. **Every figure position in `blog_draft.md` is marked with an explicit
   TODO comment placeholder**, in this exact format so they're greppable
   and unmissable during Medium assembly:

   `<!-- TODO-FIGURE: [ID] — [one-line description of what goes here,
   including data source and any caption text] -->`

   Required placeholders (minimum set, per Sections 2 and 3):
   - `TODO-FIGURE: CHART-A` — grouped/stacked bars, four scenarios
     (S1/S1b/S2/S2b) from §7a table; conversation slice in hot color.
   - `TODO-FIGURE: CHART-B` — S2→S2b delta view; scaffolding frozen at 0,
     conversation +28.5K.
   - `TODO-FIGURE: SCREENSHOT-1` — redacted, cropped Cursor Context Usage
     category list (PII rules in §7a apply).
   - `TODO-FIGURE: D1` — push-all vs RAG-MCP retrieve vs MCP-Zero request
     (one canvas, spec in §6).
   - `TODO-FIGURE: D2` — RTK raw-firehose vs filtered-trickle flow (§6).
   - `TODO-FIGURE: D3` — TokenSkip three-line strike-through example (§6).
   - `TODO-FIGURE: D4` — Ponytail decision ladder (§6).
   - Optional: `TODO-FIGURE: EXPLAINER-LINK` — not an image; reminder to
     insert the GitHub Pages URL for the interactive simulator once
     deployed.
4. Each placeholder's caption text is written INTO the placeholder comment
   at draft time, so captions are finalized with the prose, not improvised
   during assembly.
5. Assembly workflow for the author: paste `blog_draft.md` into Medium →
   grep the pasted draft for `TODO-FIGURE` → drag each PNG in at its
   marker → delete the marker → paste its caption.

---

- **Working titles** (pick at draft time, test 2–3 on Medium's preview):
  - "Where Do All My Tokens Go?"
  - "Your MCP Servers Are Eating Your Context Window"
  - "The Anatomy of a Token Bill"
- **Subtitle:** something like "A field guide to context bloat in Claude Code,
  Cursor, and friends — and everything people have built to fight it."
- **Target length:** unconstrained (expect ~2,000–2,400 words). Length is not a
  constraint per author decision.
- **Audience:** practitioners using Claude Code / Cursor / Copilot with MCP
  servers. Assumes they know what an LLM and a context window are; does NOT
  assume they've read any paper cited.
- **Tags:** AI, LLM, Developer Tools, Claude, Programming.

---

## 2. Structure

### Section 1 — The hook (~150–200 words)
- First person, experiment-driven: the author didn't just wonder where the
  tokens go — they ran the experiment. Open mid-action: "I opened a fresh
  Cursor session, turned off every MCP server, and asked one question."
- The hook stat from the author's OWN data: two conversational turns, all
  MCP servers on, and ~60.4K of a 200K window was gone — 30%, and the
  actual conversation was two short questions. (Source: §7a, Scenario 2b.)
- Secondary beat if the hook needs one: the same polite follow-up ("please
  double check") cost ~3.3K tokens without MCPs and ~24.7K with them —
  same words, ~7x the price, because this time the agent actually went and
  checked.
- The wild-web horror stats (143K/200K on schemas alone, §7b) move OUT of
  the hook and into Section 3a/3b as context — the author's own numbers
  carry the opening now.
- Tone: curious, specific, zero throat-clearing. Do NOT open with "In the
  age of AI..." or any scene-setting about how LLMs changed coding.
- Ends with the promise: here's where it all went, category by category —
  I have the receipts.

### Section 2 — The experiment: where the tokens actually go (~400–500 words + 3–4 images)
Built entirely on the author's real four-scenario Cursor Context Usage
experiment (data in §7a). Structure:

**2.1 The setup (2–3 sentences):** fresh sessions in the same repo, same
200K window, controlled variable = MCP servers on/off, same prompts:
"how many MCP servers do I have connected?" then "please double check."

**2.2 The anatomy** — introduce the categories using Cursor's OWN category
names straight from the report (plain words, NO equation, NO channel
letters — ground rule 2): system prompt, tool definitions, rules, skills,
subagent definitions, MCP & dynamic tools, conversation. One plain-words
sentence per category. Key facts to land, each from §7a:
- Baseline, zero MCPs, one short question: ~25.4K tokens — and ~24.6K of
  it is scaffolding. The user's actual conversation was ~3% of what the
  model read.
- Cursor's BUILT-IN tools alone cost ~15.8K/turn — MCP servers don't
  introduce the tool-definition tax, they pile onto one you were already
  paying.
- Enabling 18 MCP tools added ~6.3K of schemas — and nudged every other
  scaffolding line up slightly (system prompt +56, built-ins +267...).
  The glue costs too. (Detail only someone who ran it would notice —
  keep it.)
- The frozen-vs-alive contrast: between consecutive turns, every
  scaffolding line is token-for-token identical; ONLY conversation moves.
  This is "re-sent every turn" proven in one table.
- The punchline pair: "please double check" cost ~3.3K without MCPs and
  ~24.7K with them — the agent actually re-ran its MCP checks, and the
  tool OUTPUTS flooded conversation. Schemas were the visible tax (6.3K);
  outputs were the real bill (~4x the schemas, one turn).

**2.3 The compounding insight** (the screenshot-able line): tool outputs
and replies don't vanish after a turn — they become the next turn's
history. Two turns took the author to 30%; a real afternoon of work
compacts or dies.

**Visuals for this section:**
- CHART A (primary): grouped/stacked bar chart of the four scenarios
  (S1, S1b, S2, S2b) built from §7a data in the post's own visual style —
  scaffolding categories in muted fixed colors, conversation in a hot
  color so its growth screams.
- CHART B: the S2→S2b delta view — everything frozen at 0, conversation
  +28.5K. One-bar drama.
- SCREENSHOT (exactly one, authenticity beat): cropped Cursor Context
  Usage category list. REDACT before use: repository name, share-canvas
  URLs, timestamps, any employer-identifiable string. Crop to just the
  category/token list. Caption: "Cursor's Context Usage report — worth
  finding in your own dashboard."
- Optional: the original interactive explainer (token-budget-explainer
  .html) becomes a LINKED extra hosted on GitHub Pages ("I built a little
  simulator for how this compounds over more turns") — its simulated
  6-turn snowball now supplements real data rather than substituting for
  it. Re-label its legend in plain words before publishing (no channel
  letters).

### Section 3 — The catalog (~900–1,100 words, 4 subsections)
Framing sentence for the section: every fix below attacks ONE of the slices
above. Present each method as a tight card: **What / Why (with number) / How /
Link.** Keep cards to 60–100 words each. Diagrams per §6.

#### 3a. Tool definitions
- **RAG-MCP** — retrieval over tool schemas; only top-k relevant tools enter
  the prompt. >50% prompt-token cut; tool-selection accuracy 43.13% vs 13.62%
  baseline as pools grow. Link: https://arxiv.org/abs/2505.03275
  Diagram D1 (push-all vs retrieve-few, side A).
- **MCP-Zero** — inverts it: the model REQUESTS tools on demand via structured
  requests + hierarchical routing. 98% token reduction on APIBank; scales to
  ~2,800 tools / 308 servers. Link: https://arxiv.org/abs/2506.01056
  Diagram D1 (side B — same canvas as RAG-MCP so the pull-vs-push contrast is
  instantly visible).
- **Do-it-today paragraph** (no card, no diagram): disable unused MCP servers;
  use hosts' deferred tool loading where available. One honest sentence that
  the boring fix is the highest-leverage one for most readers.

#### 3b. History & tool outputs (the snowball)
Architectural framing sentence (one line, keeps the section feeling designed):
some tools intercept BEFORE output enters context, others compress what's
already headed in.
- **RTK (Rust Token Killer)** — pre-filter. A Rust CLI proxy: a PreToolUse
  hook rewrites shell commands (git status → rtk git status) so the agent
  receives filtered output. 100+ commands, <10ms overhead; their 30-min
  Claude Code session estimate: ~118K raw output tokens → ~23.9K (~80% cut);
  test runners ~90%. On failure, full output saved to a log so nothing is
  lost. Supports 14 AI tools (Claude Code, Cursor, Copilot, Gemini CLI...).
  64.9k stars — mainstream, not niche. Link: https://github.com/rtk-ai/rtk
  Diagram D2 (raw firehose vs filtered trickle).
- **Headroom** — post-filter. Compresses bulky content behind a hash stub in
  context; original retrievable on demand. Link:
  https://github.com/anthropics/headroom  ← VERIFY exact URL at draft time;
  if the canonical repo differs, use the one previously surfaced in research
  notes. Closet-ticket metaphor in prose; no diagram (D2 carries this
  subsection).
- **lean-ctx** — one to two lines only (RTK carries the shell-output story
  with better numbers/adoption): AST-aware compression of file reads, keeps
  signatures/structure, drops bodies; 60–99% savings depending on mode and
  cache state. Link: use the repo URL previously surfaced in research notes —
  VERIFY at draft time.
- **Compaction** (one paragraph, no card): the built-in behavior readers
  already see in Claude Code; naming it builds trust. No link needed, or link
  Anthropic docs if convenient.

#### 3c. Reasoning tokens (the model's own verbosity)
Written as a narrative arc, not pure cards — the arc IS the content: the
famous method is no longer the best one.
- **TokenSkip** — established the paradigm: score per-token importance, build
  compressed CoT training pairs at target ratios, LoRA fine-tune so the model
  GENERATES compressed reasoning directly (not post-hoc trimming). Safe zone:
  ~40% fewer tokens at <0.4% accuracy loss (Qwen2.5-14B, GSM8K, 313→181
  tokens). Link: https://arxiv.org/abs/2502.12067
  Diagram D3 (long sentence → struck-through filler → short sentence; reuse
  the "Calculate total. Subtract discount." example).
- **The honest turn** (short paragraph, no card, no diagram — the candor is
  the visual): at aggressive ratios TokenSkip drops 20+ accuracy points and
  behaves erratically; newer methods beat it at every reported ratio:
  - **Extra-CoT** — robust at extreme ratios (0.2) where TokenSkip collapses;
    73% token cut on MATH-500 with +0.6% accuracy.
    Link: https://arxiv.org/abs/2602.08324
  - **CtrlCoT** — dual-granularity compression, higher accuracy with fewer
    tokens across 3B/7B/14B. Link: https://arxiv.org/abs/2601.20467
  (One line each, inline — do not give these full cards; the point is the
  correction, not a survey.)
- **Chain of Draft** — the zero-training trick: a prompt instruction ("think
  step by step but keep each step to ~5 words"). Token cuts up to ~92% on
  some task types with stable accuracy; anyone can try it in 30 seconds.
  Link: https://arxiv.org/abs/2502.18600
  No diagram — a before/after text snippet in the prose is stronger.
- Somewhere in this subsection, one plain-words version of the compounding
  point from Section 2: shorter reasoning this turn = smaller history every
  future turn. (Allowed: it's a per-channel observation. NOT allowed: any
  suggestion of coordinating this with other channels.)

#### 3d. Agent behavior — the tokens you never spend
Framing sentence (writes itself): everything above compresses tokens after
the model decides to produce them; this category changes the decision.
- **Ponytail** — a rules-file/skill enforcing a decision ladder before any
  code is written: does it need to exist? > reuse codebase > stdlib > native
  platform > installed dependency > one-liner > write the minimum. Explicitly
  exempts trust-boundary validation, error handling, security, a11y. Their
  agentic benchmark (headless Claude Code, Haiku 4.5, real FastAPI+React
  repo, 12 tickets): ~54% less code, ~22% fewer tokens, ~20% lower cost,
  ~27% faster, equal safety. Delivered as Claude Code plugin / Codex plugin /
  Cursor rules / AGENTS.md. Link: https://github.com/DietrichGebert/ponytail
  Diagram D4 (the ladder, vertical, stop-at-first-rung).
- **Karpathy-inspired guidelines** — a single CLAUDE.md distilling Karpathy's
  observations on LLM coding failure modes into four principles: Think Before
  Coding / Simplicity First / Surgical Changes / Goal-Driven Execution.
  Targets overcomplication and abstraction bloat (the 1000-lines-where-100-
  would-do failure). Its own success signals (fewer unnecessary diff changes,
  minimal PRs, fewer rewrites) are all indirect token metrics. ~184k stars —
  worth one remark: the most-adopted "token optimizer" in existence is a
  prompt file, not a system. Ships Claude Code plugin + Cursor rules variant.
  Link: https://github.com/multica-ai/andrej-karpathy-skills
  No diagram (one diagram per subsection max here; D4 carries it). Optionally
  a small 4-principle table if the draft feels text-heavy.
- **The self-aware irony line** (mandatory, one sentence): these rule files
  are themselves injected into context every turn — the cure occupies a few
  hundred tokens of the disease.

### Section 4 — Sign-off (2–3 sentences MAX)
- NO summary. NO takeaways. NO "in conclusion."
- Pattern: a light personal close + a comment prompt. E.g. the author now
  checks tool-schema cost before installing a new MCP server the way one
  checks an app's battery drain — then: "what's eating your context window?
  tell me in the comments." (Rewrite in the author's voice at draft time;
  do not copy this verbatim.)

---

## 3. Section-by-section word budget

| Section | Words | Images |
|---|---|---|
| 1 Hook | 150–200 | 0 |
| 2 Anatomy | 300–350 | 2–3 PNGs |
| 3a Tool definitions | ~220 | D1 |
| 3b History & outputs | ~280 | D2 |
| 3c Reasoning | ~280 | D3 |
| 3d Agent behavior | ~250 | D4 |
| 4 Sign-off | 40–60 | 0 |
| **Total** | **~1,550–1,750 body** (reads as ~2,000+ with captions/snippets) | 6–7 |

---

## 4. Writing order (how to actually produce the draft)

1. Write Section 2 FIRST (the anatomy). It's the load-bearing explainer; if
   it's clear, everything else hangs off it.
2. Write Section 3 cards next, one subsection per sitting. Enforce the
   What/Why/How/Link card shape, then deliberately BREAK the shape in 2–3
   places (vary a card's order, fold one What into a Why) so the section
   doesn't read templated. Machine-written listicles keep perfect parallel
   structure; humans don't.
3. Write the hook LAST-but-one. Hooks written first are generic; written
   after the body exists, they can foreshadow a specific detail from §3.
4. Sign-off last. Two sentences. Resist expanding it.
5. **The disclosure pass** (mandatory, separate read): scan the full draft
   for any sentence that compares channels to each other, totals them, or
   hints at coordination/allocation. Delete on sight. The post may say
   "tool schemas are the biggest single line-item at session start" (fact
   about one channel) but never "these interact / compete / could be
   balanced."
6. **The humanity pass** (mandatory, separate read): check against §5 rules.
7. Fact-check pass against §7 table. Every stat must match its source.

---

## 5. Voice rules (mandatory)

- First person throughout. The author has opinions and a Splunk MCP server.
- At least two numbers from the AUTHOR'S OWN setup (e.g., own tool count,
  own context-meter reading before/after disabling servers) — measure these
  for real before drafting; do not invent them. Cited-paper numbers alone
  make it read like a survey.
- Exactly one opinion stated AS opinion ("personally I think the boring fix
  — uninstalling servers — beats every paper on this list for most people").
- One small honest admission (e.g., ran Chain of Draft expecting nothing,
  it embarrassed the fine-tuning plans). True ones only.
- Sentence length must vary. Read the draft aloud; if three consecutive
  sentences have the same rhythm, rewrite one.
- Banned phrases: "In this post, we will", "delve", "landscape" (as noun for
  the field), "In the age of", "game-changer", "Let's dive in", "In
  conclusion", "It's worth noting", "Moreover". Banned structures: bullet
  lists inside the prose sections (cards are the exception and should read
  as short paragraphs, not bullets); headers deeper than one level inside
  sections.
- Em-dashes are fine (humans use them); semicolons sparingly.
- Numbers: give the concrete figure and its plain-words meaning in the same
  sentence ("143K of a 200K window — nearly three-quarters gone before you
  say hello").

---

## 6. Diagram specs (all redrawn originals, one consistent style)

Global style: dark background (#0B0D10-ish, matching the existing explainer),
one accent color per diagram, hand-labeled arrows, generous whitespace,
PNG export at 2x for Medium. Build as SVG/HTML then screenshot, or draw in
Excalidraw for a deliberately hand-drawn feel (Excalidraw's roughness reads
"human" — consider it seriously).

- **D1 (3a):** one canvas, two halves. Left: "every schema, every turn" —
  40 small boxes funneling into a model icon, funnel choked. Right split A/B:
  (A) RAG-MCP: query → index → 3 boxes → model. (B) MCP-Zero: model → tool
  request arrow pointing BACK to a registry → 1 box returns. The reversed
  arrow direction between A and B is the entire point; make it unmissable.
- **D2 (3b):** two horizontal flows. Top: terminal icon → 2,000-token wall of
  text → context window (overflowing). Bottom: terminal → RTK filter block →
  ~200 tokens → context window (comfortable). Label the filter block with
  its four strategies in tiny text (filter/group/truncate/dedupe).
- **D3 (3c):** three stacked lines of the same sentence. Line 1: full
  verbose reasoning. Line 2: same text with filler words struck through in
  the accent color. Line 3: only the survivors. Caption: "the model is
  fine-tuned to generate line 3 directly — it never writes line 1."
- **D4 (3d):** Ponytail's ladder, vertical, 7 rungs top-to-bottom (need to
  exist? → reuse → stdlib → native → dependency → one-liner → write minimum),
  a "STOP at first yes" side-arrow, and a small exempt-list footnote
  (security / error handling / a11y never skipped).
- **Section-2 PNGs:** export from token-budget-explainer.html — (1) six
  uncompressed turns, (2) six turns with the compress toggle on, (3)
  optional single-turn detail. Re-label axis/legend in plain words (no
  channel letters) before export to comply with ground rule 2.

---

## 7a. The author's own measured data (primary source for Sections 1–2)

Cursor Context Usage reports, repo redacted, 200K window, July 9 2026.
Prompts: T1 = "how many MCP servers do I have connected?", T2 = "please
double check" (S1b wording: "are you double sure.. please check again").

| Category | S1: no MCP, T1 | S1b: no MCP, T2 | S2: MCP on, T1 | S2b: MCP on, T2 |
|---|---|---|---|---|
| Total | ~25.4K | ~29.3K | ~31.9K | ~60.4K |
| System prompt | 3,284 | 3,284 | 3,340 | 3,340 |
| Tool definitions (built-in, 20) | 15,801 | 15,801 | 16,068 | 16,068 |
| Rules (4) | 2,248 | 2,248 | 2,286 | 2,286 |
| Skills (20) | 2,260 | 2,260 | 2,298 | 2,298 |
| MCP & dynamic tools (18) | — | — | 6,312 | 6,312 |
| Subagent definitions (8) | 931 | 931 | 946 | 946 |
| Conversation | 838 | 4,759 | 645 | 29,197 |

Derived facts approved for the post:
- Baseline scaffolding ≈ 24.6K of 25.4K (~97%) with zero MCPs.
- Built-in tool definitions ≈ 15.8K/turn before any MCP server exists.
- 18 MCP tools ≈ +6.3K schemas (~350 tokens/tool), every turn, used or not.
- Enabling MCPs nudged all other scaffolding up (+56 sys prompt, +267
  built-ins, +38 rules, +38 skills, +15 subagents) — "the glue costs too."
- Same follow-up prompt: ~3.3K (no MCP) vs ~24.7K (MCP on) — tool outputs
  flooding conversation, ~4x the schema cost in one turn.
- Two turns with MCPs on = ~60.4K = 30% of the window.
- Methodology note (footnote-worthy in post): export the report AFTER the
  reply fully lands — an early S1 export showed Turn 1 at ~838 that later
  finalized at ~1,467/4,489 as tool-call records completed.

**Mandatory honest-contrast paragraph (Section 3a or 3b):** the author's
measured MCP overhead (~6.3K for 18 tools) is much milder than wild-web
horror stories (~143K for ~40 tools). Name both likely reasons: lean server
schemas, and Cursor apparently managing MCP definitions dynamically (note
built-ins GetMcpTools / CallMcpTool / FetchMcpResource — suggesting
on-demand loading rather than full schema injection; frame as inference
from the report, not confirmed internals). The tension to state outright:
"my setup is the good case, and it still costs 6.3K a turn" — the tax
varies wildly by host and server quality. This is more credible than
pretending the author's numbers match the worst case.

**PII rules for using these reports:** never show repository name,
share-canvas URLs, or timestamps. Screenshots cropped to category lists
only. Charts rebuilt from the table above, never screenshotted from the
dashboard.

## 7b. External source-of-truth table (every cited claim traces here)

| Claim | Figure | Source |
|---|---|---|
| GitHub+Slack+Sentry MCP ≈ 40 tools ≈ 143K/200K tokens (72%) | 143K, 72% | practitioner writeup surfaced in earlier research (production measurement) — RE-VERIFY link at draft time before citing |
| 93-tool GitHub MCP ≈ 55K tokens at init | 55K | practitioner writeup — RE-VERIFY link at draft time |
| RAG-MCP: >50% token cut; 43.13% vs 13.62% selection accuracy | 50%, 3.2x | https://arxiv.org/abs/2505.03275 |
| MCP-Zero: 98% token reduction (APIBank); 308 servers / 2,797 tools | 98% | https://arxiv.org/abs/2506.01056 |
| RTK: ~118K→~23.9K in 30-min session (~80%); ~90% on test runners; 100+ commands; <10ms; 14 tools; 64.9k stars | 80%, 90% | https://github.com/rtk-ai/rtk |
| lean-ctx: up to 99% savings on repeat reads (mode/cache dependent), AST-aware via tree-sitter | 99% | github.com/yvgude/lean-ctx — VERIFIED |
| TokenSkip: 313→181 tokens, <0.4% acc drop (Qwen2.5-14B, GSM8K) | 40%, 0.4% | https://arxiv.org/abs/2502.12067 |
| TokenSkip: >20-point accuracy drop at high compression | 20+ pts | reported in CtrlCoT: https://arxiv.org/abs/2601.20467 |
| Extra-CoT: robust at ratio 0.2; MATH-500 73% cut, +0.6% acc | 73%, +0.6% | https://arxiv.org/abs/2602.08324 |
| Chain of Draft: up to ~92% cuts on some task types, ≤5-word steps | 92% | https://arxiv.org/abs/2502.18600 (92% figure reported via EffiReason-Bench comparison — attribute carefully: "reported reductions above 90% on commonsense tasks") |
| Ponytail: ~54% less code, ~22% fewer tokens, ~20% cheaper, ~27% faster, safety parity (Haiku 4.5, 12 tickets) | 54/22/20/27 | https://github.com/DietrichGebert/ponytail |
| Karpathy skills: 4 principles; ~184k stars; Claude Code plugin + Cursor variant | 184k | https://github.com/multica-ai/andrej-karpathy-skills |
| Headroom: hash-stub compress/retrieve | — | repo URL — VERIFY at draft time |

**Rule:** any row marked RE-VERIFY/VERIFY must be confirmed with a fresh
fetch before the draft cites it. If unconfirmable, soften to "measurements
people have shared" without the precise figure, or cut.

---

## 8. Publication checklist

- [x] All VERIFY rows in §7b resolved (lean-ctx confirmed; Headroom still open — see note below)
- [x] `blog_draft.md` produced with all TODO-FIGURE placeholders per §0b
- [x] Every TODO-FIGURE placeholder has its caption text written inside it
- [x] All figure PNGs generated (dark polished style) and named to match
      their TODO-FIGURE IDs (chart-a.png, d1-tool-schemas.png, d2-rtk-filter.png,
      d3-tokenskip.png, d4-ponytail-ladder.png)
- [x] Author's personal numbers measured — four-scenario experiment done (§7a)
- [x] Screenshot redaction done: repo name, share URLs, timestamps removed,
      cropped to category list only — screenshot-1.png in place, Scenario 2b
      (used as the Chart-B punchline confirmation, not the Section 2 opener,
      since Scenario 2's report was overwritten and unrecoverable)
- [x] Charts A + B built from §7a table (not screenshotted from dashboard)
- [x] Disclosure pass done (§4.5) — zero cross-channel language
- [x] Humanity pass done (§4.6) — banned-phrase grep + read-aloud logic applied
- [x] All 7 images at high DPI (2800\u20134000px long edge), alt text written for each
- [ ] Interactive explainer deployed to GitHub Pages, link tested — TODO-FIGURE:
      EXPLAINER-LINK is the one remaining placeholder in blog_draft.md
- [ ] Every arXiv/GitHub link clicked and live — spot-check before publish
- [x] No takeaways / conclusion section exists
- [x] Title selected: "The Anatomy of a Token Bill" (option C); subtitle set
- [ ] One full read-aloud of the final draft — author's pass, not done yet
- [ ] Headroom repo URL — never actually verified (flagged, not yet resolved)
