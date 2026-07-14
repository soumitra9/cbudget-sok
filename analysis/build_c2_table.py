"""Build C2 incommensurability table from extraction sheet."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


METRIC_PATTERNS = {
    "RAG-MCP": "selection accuracy + prompt tokens",
    "MCP-Zero": "selection accuracy + avg tokens",
    "RTK (Rust Token Killer)": "estimated tokens, no quality metric",
    "RTK": "estimated tokens, no quality metric",
    "Headroom": "tokens by content type",
    "lean-ctx / LeanCTX": "tokens by language/mode",
    "lean-ctx": "tokens by language/mode",
    "Native compaction": "session continuation, no published metric",
    "Compaction": "session continuation, no published metric",
    "TokenSkip": "math accuracy vs compression ratio",
    "Chain of Draft (CoD)": "accuracy + output tokens + latency",
    "Chain of Draft": "accuracy + output tokens + latency",
    "SEER": "pass@1 + CoT length + loop rate",
    "Ponytail": "LOC + session tokens + cost + time + safety rate",
    "LLMLingua-2": "QA F1/BERTScore at ratio",
}


def parse_c2_primary_metrics(text: str) -> dict[str, str]:
    """Parse the C2 summary line from the method extraction sheet."""
    match = re.search(
        r"\*\*For C2 \(incommensurability\).*?\*\* (.+?)(?:\n\n|\n\*\*|\Z)",
        text,
        re.DOTALL,
    )
    if not match:
        return {}
    body = match.group(1).strip()
    metrics: dict[str, str] = {}
    for part in body.split(". "):
        if ":" not in part:
            continue
        names_raw, metric = part.split(":", 1)
        metric = metric.strip().rstrip(".")
        for name in names_raw.split("/"):
            metrics[name.strip()] = metric
    return metrics


METHOD_ALIASES = {
    "RAG-MCP": "RAG-MCP",
    "MCP-Zero": "MCP-Zero",
    "RTK (Rust Token Killer)": "RTK",
    "Headroom": "Headroom",
    "lean-ctx / LeanCTX": "lean-ctx",
    "Native compaction": "Compaction",
    "TokenSkip": "TokenSkip",
    "CtrlCoT": "CtrlCoT",
    "Extra-CoT": "Extra-CoT",
    "Chain of Draft (CoD)": "CoD",
    "SEER": "SEER",
    "Ponytail": "Ponytail",
    "andrej-karpathy-skills": "karpathy-skills",
    "LLMLingua-2": "LLMLingua-2",
    "MemGPT-style memory": "MemGPT-style memory",
    "Latent chain-of-thought": "Latent chain-of-thought",
}


def lookup_primary_metric(method_name: str, c2_metrics: dict[str, str]) -> str:
    alias = METHOD_ALIASES.get(method_name, method_name)
    if alias in c2_metrics:
        return c2_metrics[alias]
    if method_name in c2_metrics:
        return c2_metrics[method_name]
    for key, metric in c2_metrics.items():
        if key in method_name or method_name.startswith(key.split()[0]):
            return metric
    return METRIC_PATTERNS.get(method_name, METRIC_PATTERNS.get(alias, "see_extraction_sheet"))


def extract_methods(text: str) -> list[dict[str, str]]:
    c2_metrics = parse_c2_primary_metrics(text)
    rows = []
    for match in re.finditer(r"^### \d+\. (.+?) —", text, re.MULTILINE):
        name = match.group(1).strip()
        metric = lookup_primary_metric(name, c2_metrics)
        rows.append({"method": name, "primary_metric": metric, "evidence_label": "documented"})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    text = Path(args.input).read_text(encoding="utf-8")
    rows = extract_methods(text)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["method", "primary_metric", "evidence_label"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
