Dear Editor,

The present submission, "Context as a Budget: A Taxonomy and Composition Framework for Token-Efficiency Interventions in LLM Agents," is a systematization and critical assessment of token-efficiency approaches for LLM agents. In agent systems, everything runs under a shared context budget that grows across turns from tool schemas, tool execution output, retained conversation history, and explicit reasoning. Token use has become a practical limit: injecting tool schemas alone can run to hundreds of thousands of prompt tokens, and there is no shortage of proposals to compress, filter, compact, or cut reasoning. But these methods are evaluated on different tasks and different metrics, usually in isolation. So when a practitioner stacks multiple interventions, there is no clear basis for asking whether savings compound, interfere, or just do not add up across categories.

**What this work contributes.** We fill that gap at three levels. First, a five-category taxonomy of fourteen in-scope interventions (plus two excluded boundary cases), keyed to where each method acts in the agent execution loop, with eight comparison axes and a corpus-wide evidence audit. Second, a budget model that separates prompt tokens, generated tokens, and peak occupancy, and shows how savings recur differently by intervention point. Third, an executable, preregistered protocol for cross-category composition evaluation, with two pilot 2×2 factorial studies (output-filtering × compaction; output-filtering × reasoning compression). The pilots do not show that these pairs are independent; they show how to measure interactions under shared outcome definitions, with wide confidence intervals and variance diagnostics on what is still unresolved. Aggregated results, analysis code, and hypothesis files frozen before confirmatory data collection are at Zenodo (DOI: 10.5281/zenodo.21715347).

**Why Artificial Intelligence Review.** The journal covers state-of-the-art reports, critical evaluations of techniques and applications, and refereed surveys on AI developments. This manuscript fits: a catalog of token-efficiency methods for agents (not a new algorithm), a gap analysis of how the field evaluates them, and a replicable protocol for pairs that have not been tested together. Should be relevant to people working on LLM agents, context management, efficient reasoning, and multi-intervention agent stacks.

This manuscript is original, not published elsewhere, and not under review at any other journal. All authors approve the submission. No competing interests to disclose.

Thank you for reviewing this submission.

Best regards,

Soumitra Mehrotra (Corresponding Author)  
Shubhender Singh  
Saurabh Aggarwal  

Soumitra Mehrotra  
soumitra.mehrotra9@gmail.com  
San Francisco, USA
