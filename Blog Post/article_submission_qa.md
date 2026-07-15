# Article Submission Q&A

## 1. One-paragraph abstract of the article

Every message you send an AI coding agent silently re-sends a mountain of context: the tool definitions, rules, and scaffolding the agent uses to describe itself, plus the entire growing conversation, re-read in full on every turn. A small measured experiment in Cursor makes the shape of the problem concrete: the user prompt is the smallest line on the bill, while invisible scaffolding and accumulating tool output dominate; MCP servers add a real tax, but a smaller one than their reputation suggests. From there, the piece becomes a field guide to what people have actually built to fight context bloat, organized by which slice of the bill each attacks: retrieving or requesting tool schemas on demand instead of dumping them all, filtering or compressing conversation output before and after it lands, trimming the model’s own reasoning, and teaching the agent to write less in the first place. The throughline is simple: context is a budget you keep re-paying, most of it invisible, and the cheapest wins come from first learning to read your own bill.

## 2. Brief outline of the article

The article opens with a small Cursor measurement that makes the hidden context cost of AI coding agents visible, while making clear that Cursor is only the meter, not the subject. It then breaks down the token bill into its major line items: invisible scaffolding, built-in tool definitions, MCP tool schemas, conversation history, tool outputs, command logs, and reasoning traces. The next section walks through the four-scenario measurement, showing that MCP servers add a real but limited schema tax, while the larger cost comes from fixed scaffolding and the compounding growth of conversation/tool-output history. A short takeaway section explains how readers can inspect their own context bill and identify the noisiest source of context growth. The second half surveys the emerging ecosystem of fixes, organized by which part of the bill each attacks: tool-schema retrieval and routing, output filtering and compression, context compaction, reasoning-token reduction, and agent-behavior rules that avoid unnecessary work. The article closes by arguing that context is not just a technical detail of AI coding tools, but a budget teams repeatedly repay on every turn.

## 3. Topic focus of the article

The article focuses on context bloat in AI coding agents: where the token budget actually goes, why the cost is often invisible to users, and how different tools and techniques try to reduce it. It uses Cursor’s context report as a concrete measurement instrument, but the broader topic is the hidden context cost of agentic coding workflows across tools such as Cursor, Claude Code, and MCP-enabled assistants. The article emphasizes that MCP tool schemas are only one line item on the bill; fixed scaffolding, tool outputs, command logs, conversation history, and reasoning traces can dominate the real cost over time.

## 4. Target reader for the article

The target reader is a technical practitioner who uses or evaluates AI coding agents: software engineers, staff/principal engineers, engineering managers, platform engineers, developer-experience teams, AI infrastructure teams, and technical leaders responsible for adopting tools such as Cursor, Claude Code, MCP-enabled assistants, or other agentic coding systems. The article is especially for readers who already see AI coding agents as useful, but want a clearer understanding of their hidden costs, context-window behavior, and practical ways to control token waste in real development workflows.

## 5. How this article is different and unique from other articles already published on the same topic

Most articles about AI coding agents focus on adoption: which tools to use, how they improve productivity, and what they can automate. This article looks at the less visible side of adoption: what these agents carry in context on every turn, how that context turns into a recurring token bill, and why the real cost is often not the user’s prompt but scaffolding, tool definitions, MCP schemas, command output, conversation history, and reasoning traces. It uses a small measured Cursor run as an itemized bill for a broader agentic-coding problem, then expands into a survey of the emerging techniques people are building to fight context bloat. The article is unique because it combines a concrete field measurement with a structured survey: MCP adds a real tax, but the larger cost comes from accumulated tool output and conversation growth, and each source of bloat is mapped to a specific class of fixes, including tool-schema retrieval, output filtering, context compression, reasoning reduction, and agent rules that prevent unnecessary work before tokens are spent.

## 6. How this article is based on real-world project experience

The article is based on day-to-day experience using AI coding agents as part of normal software development work: opening sessions, connecting tools, adding MCP servers, asking agents to inspect the environment, and relying on them to run commands or verify answers. Rather than presenting a large formal benchmark, the article uses a deliberately small experiment to make that everyday experience measurable: the same local coding environment, the same context window, and the same prompts, with MCP servers toggled off and on. The point is to reflect what an average developer actually does with these tools every day, then use one short, controlled measurement to expose the hidden context costs behind that workflow.

## 7. Technologies and tools discussed in the article

The article discusses the AI coding-agent tools and context-management techniques directly referenced in the draft. The focus is on how each tool or method affects the token bill: tool schemas, command output, conversation history, reasoning traces, or agent behavior.

- **Cursor** — used for the short measured experiment and context usage report.
- **Claude Code** — discussed as another AI coding-agent environment where context bloat matters.
- **MCP servers** — connected tool servers that add tool schemas and tool-call behavior to the context budget.
- **RAG-MCP** — retrieves relevant tool schemas instead of sending every schema upfront.
- **MCP-Zero** — lets the model request tools through a routing system.
- **RTK / Rust Token Killer** — filters noisy command output before it enters context.
- **Headroom** — compresses bulky context behind retrievable references.
- **lean-ctx** — compresses code context using code structure.
- **Compaction** — summarizes older conversation history to free context.
- **TokenSkip** — reduces reasoning-token length through training.
- **CtrlCoT** — reasoning-compression method discussed as a newer alternative.
- **Extra-CoT** — reasoning-compression method discussed as a newer alternative.
- **Chain of Draft** — prompts the model toward shorter reasoning steps.
- **Ponytail** — agent rules that reduce unnecessary code and token use.
- **CLAUDE.md / Karpathy-style rules** — prompt/rules files that push agents toward simpler, smaller changes.

Together, these tools show that context bloat is not one problem with one fix. The article organizes them by which part of the bill they attack: schemas, outputs, history, reasoning, or unnecessary agent work.

## 8. Case studies and use cases covered

The article covers one short real-world measurement and several practical use cases around context bloat in AI coding agents. The goal is not to present a formal benchmark, but to make everyday agent usage visible and then survey the kinds of fixes emerging around it.

- **Cursor context measurement** — a short experiment using the same local coding environment, same 200K context window, and same prompts, with MCP servers toggled off and on.
- **MCP on/off comparison** — a practical case showing that MCP tool schemas add a real tax, but are not the only or largest source of context growth.
- **Follow-up verification prompt** — a simple “please double check” use case showing how tool re-querying and returned output can rapidly increase conversation history.
- **Tool-schema bloat** — use cases where many connected tools increase prompt overhead or make tool selection harder.
- **Command-output bloat** — coding-agent workflows where shell output, test logs, file reads, and tool results flood the context window.
- **Context compression** — cases where bulky code or conversation history needs to be compressed, summarized, or retrieved only when needed.
- **Reasoning-token reduction** — cases where the model’s own reasoning traces become part of the recurring context cost.
- **Agent-behavior control** — cases where rules or skills reduce unnecessary code generation, rewrites, and exploratory work before tokens are spent.

These use cases all connect back to the same question: what part of the agent’s token bill is growing, and which class of fix is designed to reduce that specific cost?

## 9. Brief biography

Soumitra Mehrotra is a Principal Data Scientist at Autodesk, a Design and Make company. He works on applied AI, machine learning systems, and data science problems across large-scale product and engineering workflows. His work spans production machine learning, generative AI, context engineering, anomaly detection, natural-language interfaces, and cost-aware AI infrastructure, with a focus on building practical systems that are reliable, measurable, and useful in real software environments.

## 10. Five key takeaways of the article

Every AI coding-agent message carries more than the user’s prompt: it can re-send system scaffolding, tool definitions, MCP schemas, conversation history, command output, tool results, and reasoning traces.

MCP servers add a real context tax, but the larger and more surprising cost often comes from fixed scaffolding and the compounding growth of conversation history after the agent starts using tools.

A small Cursor measurement makes the hidden bill visible, but the broader lesson applies beyond Cursor: context is a recurring budget that AI coding agents keep re-paying turn after turn.

The most useful way to fight context bloat is to identify which line item is growing — schemas, shell output, file reads, logs, reasoning, or unnecessary agent work — instead of applying generic “use fewer tokens” advice.

The emerging ecosystem of fixes is best understood as a survey of targeted controls: retrieve tool schemas only when needed, filter noisy outputs before they enter context, compress or summarize history, reduce reasoning traces carefully, and constrain agents so they do less unnecessary work in the first place.
