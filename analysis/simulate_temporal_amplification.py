"""C4 temporal amplification simulation from extraction sheet references."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def parse_tokenskip(text: str) -> tuple[int, int] | None:
    match = re.search(r"TokenSkip.*?(\d+)\s*→\s*(\d+)\s*tokens", text)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None


def amplify(base: int, gamma: float, turns: int, retention: str, compaction_retention: float) -> float:
    if retention == "full":
        factor = turns
    elif retention == "final_only":
        factor = 1.0
    elif retention == "hidden_reasoning":
        factor = max(1.0, turns * 0.5)
    else:
        # compaction_after_turn_k: sensitivity parameter derived from TokenSkip after/before ratio.
        factor = turns * compaction_retention
    return base * (1 + gamma * factor)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extraction-sheet", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    text = Path(args.extraction_sheet).read_text(encoding="utf-8")
    tokenskip = parse_tokenskip(text) or (313, 181)
    before, after = tokenskip
    gamma = 1 - (after / before)
    compaction_retention = after / before  # TokenSkip single-pass retention; vary for sensitivity

    rows = []
    for retention in ("full", "final_only", "hidden_reasoning", "compaction_after_turn_k"):
        for turns in (3, 5, 10):
            amp = amplify(before, gamma, turns, retention, compaction_retention)
            rows.append(
                {
                    "method": "TokenSkip",
                    "retention_scenario": retention,
                    "turns": turns,
                    "base_tokens": before,
                    "gamma": round(gamma, 4),
                    "compaction_retention": round(compaction_retention, 4),
                    "amplified_tokens": round(amp, 2),
                    "evidence_label": "counterfactual_illustration",
                }
            )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "method",
                "retention_scenario",
                "turns",
                "base_tokens",
                "gamma",
                "compaction_retention",
                "amplified_tokens",
                "evidence_label",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
