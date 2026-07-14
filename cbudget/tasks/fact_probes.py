"""Fact-retention probe system.

Prefer exact probes (grep, AST check) over semantic ones.
Semantic probes must use a different frozen model from the agent to avoid circularity.
"""

from __future__ import annotations

import os
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
    return normalize_fact_schema(data.get("facts", []))


def normalize_fact_schema(fact_schema: list[FactSpec | dict[str, Any]]) -> list[FactSpec]:
    normalized: list[FactSpec] = []
    for fact in fact_schema:
        if isinstance(fact, FactSpec):
            normalized.append(fact)
        elif isinstance(fact, dict):
            normalized.append(FactSpec(**fact))
        else:
            raise TypeError(f"Unsupported fact schema entry type: {type(fact)!r}")
    return normalized


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
    raise NotImplementedError(
        "Semantic fact probes require a frozen external evaluator from a different model family. "
        "Set CBUDGET_ALLOW_SEMANTIC_PROBE_STUB=1 only for local dev."
    )


def run_probes(fact_schema: list[FactSpec | dict[str, Any]], summary_text: str) -> list[dict[str, Any]]:
    results = []
    allow_stub = os.environ.get("CBUDGET_ALLOW_SEMANTIC_PROBE_STUB", "").lower() in ("1", "true")
    for fact in normalize_fact_schema(fact_schema):
        if fact.probe == "exact":
            result = probe_exact(fact, summary_text)
        elif allow_stub:
            result = _probe_semantic_dev_stub(fact, summary_text)
        else:
            result = probe_semantic_stub(fact, summary_text)
        results.append(result.to_dict())
    return results


def _probe_semantic_dev_stub(fact: FactSpec, summary_text: str) -> ProbeResult:
    """Dev-only keyword stub; never used in confirmatory runs."""
    keywords = [w.lower() for w in re.findall(r"[a-zA-Z]+", fact.value) if len(w) > 2]
    summary_lower = summary_text.lower()
    hits = sum(1 for kw in keywords if kw in summary_lower)
    present = hits >= max(1, len(keywords) // 2) if keywords else fact.value.lower() in summary_lower
    return ProbeResult(
        fact_id=fact.id,
        present=present,
        contradicted=False,
        unsupported_variant=False,
        probe_method="semantic_rule_dev_stub",
    )
