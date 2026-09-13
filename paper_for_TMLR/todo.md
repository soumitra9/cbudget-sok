# Pre-submission checklist — AI Review (`main.tex`)

Portal: [Editorial Manager — aire](https://www.editorialmanager.com/aire/)

Last updated after: Zenodo deposit live + record metadata fixed; submission zip built and verified.

---

## Decisions confirmed

- **City of residence:** San Francisco, USA — confirmed for all three authors. Title page and EM affiliation use city + country only (no state), shared affiliation `[1]`.
- **ORCID:** Optional per the IFA. No author is adding one — leaving all blank is compliant. Nothing in the `.tex` or EM.
- **Authors (order):** Soumitra Mehrotra (corresponding), Shubhender Singh, Saurabh Aggarwal — all unaffiliated, San Francisco, USA.
- **Data availability:** Resolved via Zenodo deposit (DOI `10.5281/zenodo.21715347`). Record now shows all three authors, no Autodesk affiliation, CC BY 4.0. Deposit-plus-on-request split (aggregated data archived; raw traces on request).

---

## Done (manuscript — nothing left to edit in `main.tex`)

- [x] Springer `sn-jnl` format (`sn-basic`, author–year)
- [x] Abstract ~192 words (150–250); CI expanded on first use, "95%" consistent with body
- [x] Abbreviations at first mention: CI (abstract), MCP (§1), CoD (contributions), SE/OLS (§6)
- [x] Unaffiliated authors: San Francisco, USA (city + country; no state); shared `[1]` — three authors
- [x] Corresponding author email (no trailing semicolon; `\nomail` on co-authors without email)
- [x] Author contributions include all three authors
- [x] Statements and Declarations in manuscript PDF; correct back-matter order
- [x] All 6 figures cited in order; Helvetica lettering (regenerated, verified via `pdffonts`)
- [x] Bib DOIs/URLs: TokenSkip, LLMLingua-2, Sui survey URL
- [x] Data + Code availability cite Zenodo DOI; Appendix B and Appendix C updated to "archived at Zenodo" (no stale "on request" for deposited files)
- [x] Dataset entry `cab_dataset2026` in `references.bib`; renders once under M; `main.bbl` regenerated (18 bibitems)
- [x] `\clearpage` removed (all three); 29 pages, clean build
- [x] Precision sentence de-nested (single parenthetical)
- [x] Not concurrently under review elsewhere (IEEE)
- [x] Table citation order: Table 1 → 2 → 3 → 4
- [x] Generative-AI disclosure in §6.2
- [x] `SUBMISSION_GUIDELINES.md` zip manifest → `sn-basic.bst`

---

## Done (Zenodo deposit)

- [x] Repo `context-as-a-budget` public; minimal bundle only (frozen YAMLs, aggregated results, scripts, README); raw traces excluded
- [x] GitHub↔Zenodo enabled; `v1.0` release cut; DOI `10.5281/zenodo.21715347` minted (concept DOI, cited in paper)
- [x] Appendix C hashes verified byte-for-byte across paper, source, and archived bundle
- [x] Record metadata fixed: all three authors listed, Autodesk affiliation removed, license = CC BY 4.0

---

## Done (submission zip — built and verified)

- [x] Flat zip, 12 files, no subfolders, no aux/log files
- [x] `main.pdf` matches source: title page lists all three authors, 29 pages
- [x] `main.bbl` includes Zenodo entry (18 bibitems); no undefined citations
- [x] All 6 figures + `main.pdf` embed Helvetica, zero DejaVu
- [x] Zenodo DOI unchanged by metadata edits — no manuscript rebuild needed

**No further changes to the zip.**

---

## Before upload — remaining actions (all in the Editorial Manager portal)

1. [ ] **Paste declarations into Editorial Manager** — author contributions and competing interests into the web-form fields (interface text is what Springer publishes). Keep identical to the blocks below.
2. [ ] **Add all three authors in EM** — Soumitra Mehrotra (corresponding), Shubhender Singh, Saurabh Aggarwal; shared affiliation San Francisco, USA; only Soumitra's email.
3. [ ] **Confirm authorship is final** — names, order, corresponding author, contribution lines. No changes permitted after submit. **Saurabh must have approved the submitted version.**
4. [ ] **Choose APC / waiver / licence** (CC BY vs CC BY-NC-ND) when EM prompts.

ORCID: not applicable — no author is adding one (optional per IFA).

---

## Editorial Manager declarations (copy-paste)

EM asks for these in **web-form fields** separate from the PDF. For **Competing interests** and **Author contributions**, the interface text is what Springer publishes — keep it **identical** to the manuscript `\subsection*{Author contributions}` block.

### Funding

```
The authors did not receive support from any organization for the submitted work.
```

### Competing interests

```
The authors have no relevant financial or non-financial interests to disclose.
```

### Author contributions

```
Soumitra Mehrotra conceived the study, designed and conducted the experiments, performed the analysis, and wrote the manuscript. Shubhender Singh contributed to the taxonomy framing, reviewed the structural claims and composition-study interpretation, and revised the manuscript. Saurabh Aggarwal contributed to the related-work synthesis, reviewed the evidence-audit tables and experimental methodology, and revised the manuscript.
```

### Ethics approval and consent to participate

```
Not applicable.
```

### Consent for publication

```
Not applicable.
```

### Data availability

```
Aggregated experimental results supporting the composition study, including the frozen preregistered hypothesis files whose SHA-256 hashes are listed in Appendix C, are archived at Zenodo (https://doi.org/10.5281/zenodo.21715347). Raw agent run traces are not publicly archived owing to their size and environment-specific paths; they are available from the corresponding author on reasonable request.
```

### Materials availability

```
Not applicable.
```

### Code availability

```
Analysis scripts, figure-generation code, and aggregated outputs are archived at Zenodo (https://doi.org/10.5281/zenodo.21715347).
```

---

## Submission zip (flat — no subfolders) — BUILT, VERIFIED

```
main.tex
main.pdf
main.bbl
sn-jnl.cls
sn-basic.bst
references.bib
Fig1.pdf
Fig2.pdf
Fig3.pdf
Fig4.pdf
Fig5.pdf
Fig6.pdf
```

Do **not** include: `texmf/`, `figures/`, `bst/` subfolder, `build/`, aux/log files.

Local build (only if a source edit is ever needed):

```bash
cd paper_for_AI_review_journal/draft && make
```

---

## Manuscript QA (verified)

| Check | Status |
|---|---|
| Abstract 150–250 words | OK (~192) |
| Keywords 4–6 | OK (5) |
| Abbreviations defined at first use | OK (CI, LLM, MCP, CoD, SE, OLS) |
| Title page email line | OK (no trailing `;`) |
| Unaffiliated address = city + country | OK (San Francisco, USA) |
| Figure fonts Helvetica | OK (Fig1–6 + main.pdf, zero DejaVu) |
| References DOIs/URLs | OK (TokenSkip, LLMLingua-2, Sui, Zenodo dataset) |
| Figures 1–6 cited in order | OK |
| Tables 1–4 cited in order | OK |
| Author–year citations | OK |
| Declarations in PDF | OK |
| Page count / build | OK (29 pp, 0 errors, 0 undefined refs) |
| `main.bbl` matches `references.bib` | OK (18 bibitems, Zenodo entry present) |
| `main.pdf` title page = three authors | OK (verified in built zip) |
| Data availability | OK (Zenodo deposit, CC BY 4.0, hashes verified) |

---

## Lower priority (no change required)

- Six GitHub/vendor `@misc` entries: defensible with access dates; §5.1 covers evidentiary weight
- Redundant `\usepackage` (class already loads most); `microtype` optional
- Type 3 font on bullet lists: `sn-jnl` glyph, not figure artwork

---

## Reproducibility bundle

Minimal artifact for Table 4 / Figs 4–6 + Appendix C hash verification, archived at Zenodo (`10.5281/zenodo.21715347`). Hypothesis YAML paths match the paper byte-for-byte; hashes verified across paper, source, and archive.
