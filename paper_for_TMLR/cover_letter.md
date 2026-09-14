# Cover note to the Action Editor

**Submission:** *Context as a Budget: A Taxonomy, an Accounting Framework, and a Measurement Audit for Composing Token-Efficiency Interventions in LLM Agents*

## What the paper claims, and why the claims are supported

This paper makes a deliberately small set of claims, each of which survives inspection:

1. **We report no detectable compositional effect between token-efficiency interventions, and we demonstrate why.** In a preregistered 2x2 factorial pilot, cumulative prompt tokens have a per-cell standard deviation about equal to their mean (~62,700 vs ~58,900). Of eighteen token-outcome contrasts, only two are distinguishable from zero, and both are *treatment-fidelity checks* that merely confirm each intervention did the mechanical thing it is defined to do. Neither survives multiplicity correction. The design cannot reliably detect its own manipulations, so it cannot detect a second-order interaction between two of them.

2. **The contribution is the measurement audit and the sample sizes it implies.** We quantify what evaluating composition in this setting costs: resolving the output-filtering prompt-token effect we actually observe would require roughly 4,900 runs per cell, against the twelve used. We also document two reusable diagnostics: a process-based degeneracy filter that flagged 72% of a nominal 144-run experiment as uninformative in a treatment-loaded pattern, and the near-futility of seed expansion at low temperature.

3. **Supporting structure:** a taxonomy of fourteen interventions by intervention point; a budget-recurrence accounting framework that yields one a priori prediction, which we test and report as inconclusive (not validated) at this sample size; and a confirmatory reproduction that regenerates byte-for-byte from raw traces.

## Fit with TMLR's criteria

TMLR asks whether claims are supported by evidence, not whether results are surprising or beat a baseline. Every claim above is either a measurement of the evaluation itself or an explicitly hedged null. We do not claim any intervention interaction, any downstream token saving, or a validated predictive model; the paper is careful to state what the data at this sample size can and cannot support. The central exhibit is a full contrast-by-contrast audit table (standard error and 95% interval for every contrast), placed in the body rather than an appendix.

## Reproducibility and anonymity

The submission is anonymized for double-blind review. The aggregated run table, the significance-audit artifacts that produce the central exhibit, the analysis and figure code, and the SHA-256-hashed frozen preregistration files are provided as anonymized supplementary material; the public archive will be linked in the camera-ready version.
