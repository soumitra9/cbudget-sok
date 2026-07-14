"""Build C2 incommensurability table from extraction sheet."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


METRIC_PATTERNS = {
    "RAG-MCP": "selection accuracy + prompt tokens",
    "MCP-Zero": "selection accuracy + avg tokens",
    "RTK": "estimated tokens, no quality metric",
    "Headroom": "tokens by content type",
    "lean-ctx": "tokens by language/mode",
    "Compaction": "session continuation, no published metric",
    "TokenSkip": "math accuracy vs compression ratio",
    "Chain of Draft": "accuracy + output tokens + latency",
    "SEER": "pass@1 + CoT length + loop rate",
    "Ponytail": "LOC + session tokens + cost + time + safety rate",
    "LLMLingua-2": "QA F1/BERTScore at ratio",
}


def extract_methods(text: str) -> list[dict[str, str]]:
    rows = []
    for match in re.finditer(r"^### \d+\. (.+?) —", text, re.MULTILINE):
        name = match.group(1).strip()
        metric = METRIC_PATTERNS.get(name, "see_extraction_sheet")
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
