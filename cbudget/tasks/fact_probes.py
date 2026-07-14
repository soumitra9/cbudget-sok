"""Fact-retention probe system.

Prefer exact probes (grep, AST check) over semantic ones.
Semantic probes must use a different frozen model from the agent to avoid circularity.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class FactSpec:
    id: str
    value: str
    importance: str  # required | supporting
    probe: str  # exact | semantic


@dataclass
class ProbeResult:
    fact_id: str
    present: bool
    contradicted: bool
    unsupported_variant: bool
    probe_method: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_fact_schema(path: Path) -> list[FactSpec]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [FactSpec(**entry) for entry in data.get("facts", [])]


def probe_exact(fact: FactSpec, summary_text: str) -> ProbeResult:
    """Check for literal presence of the fact value in the summary."""
    present = fact.value.lower() in summary_text.lower()
    return ProbeResult(
        fact_id=fact.id,
        present=present,
        contradicted=False,
        unsupported_variant=False,
        probe_method="exact",
    )


def probe_semantic_stub(fact: FactSpec, summary_text: str) -> ProbeResult:
    """
    Rule-based semantic probe placeholder until a frozen external evaluator is wired.
    Checks keyword overlap between fact value tokens and summary text.
    """
    keywords = [w.lower() for w in re.findall(r"[a-zA-Z]+", fact.value) if len(w) > 2]
    summary_lower = summary_text.lower()
    hits = sum(1 for kw in keywords if kw in summary_lower)
    present = hits >= max(1, len(keywords) // 2) if keywords else fact.value.lower() in summary_lower
    contradicted = False
    if "do not" in fact.value.lower() or "not change" in fact.value.lower():
        contradicted = "change public api" in summary_lower or "modify api" in summary_lower
    return ProbeResult(
        fact_id=fact.id,
        present=present and not contradicted,
        contradicted=contradicted,
        unsupported_variant=False,
        probe_method="semantic_rule",
    )


def run_probes(fact_schema: list[FactSpec], summary_text: str) -> list[dict[str, Any]]:
    results = []
    for fact in fact_schema:
        if fact.probe == "exact":
            result = probe_exact(fact, summary_text)
        else:
            result = probe_semantic_stub(fact, summary_text)
        results.append(result.to_dict())
    return results
