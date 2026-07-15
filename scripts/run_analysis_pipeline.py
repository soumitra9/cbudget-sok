"""Stage 7 analysis pipeline."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLAN_ROOT = PROJECT_ROOT.parent / "0.3 Plan"
DEFAULT_EXTRACTION_SHEET = PROJECT_ROOT / "docs" / "method_extraction_sheet_v1.md"
RESULTS = PROJECT_ROOT / "results"


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    sheet = DEFAULT_EXTRACTION_SHEET
    if not sheet.exists():
        sheet = PLAN_ROOT / "method-extraction_sheet_v1.md"
    if not sheet.exists():
        raise FileNotFoundError(
            f"Method extraction sheet not found at {DEFAULT_EXTRACTION_SHEET} or {PLAN_ROOT / 'method-extraction_sheet_v1.md'}"
        )

    run([sys.executable, "-m", "analysis.build_c2_table", "--input", str(sheet), "--output", str(RESULTS / "c2_metrics.csv")])
    run([
        sys.executable,
        "-m",
        "analysis.simulate_temporal_amplification",
        "--extraction-sheet",
        str(sheet),
        "--output",
        str(RESULTS / "c4_temporal.csv"),
    ])
    run([
        sys.executable,
        "-m",
        "analysis.build_anatomy",
        "--runs",
        str(PROJECT_ROOT / "runs/e1_rtk_compaction"),
        "--cells",
        "baseline,compaction_only",
        "--output",
        str(RESULTS / "e0_anatomy"),
    ])
    run([
        sys.executable,
        "-m",
        "analysis.estimate_interactions",
        "--runs",
        str(PROJECT_ROOT / "runs/e1_rtk_compaction"),
        "--hypothesis",
        "configs/hypotheses/e1_frozen.yaml",
        "--output",
        str(RESULTS / "e1"),
    ])
    run([
        sys.executable,
        "-m",
        "analysis.estimate_interactions",
        "--runs",
        str(PROJECT_ROOT / "runs/e1b_rtk_cod"),
        "--hypothesis",
        "configs/hypotheses/e1b_frozen.yaml",
        "--output",
        str(RESULTS / "e1b"),
    ])
    run([
        sys.executable,
        "-m",
        "analysis.estimate_interactions",
        "--runs",
        str(PROJECT_ROOT / "runs/e1_sensitivity"),
        "--hypothesis",
        "configs/hypotheses/e1_frozen.yaml",
        "--output",
        str(RESULTS / "e1_sensitivity"),
    ])
    run([
        sys.executable,
        "-m",
        "scripts.simulate_provider_cost",
        "--runs",
        str(PROJECT_ROOT / "runs"),
        "--price-table",
        str(PROJECT_ROOT / "configs/provider_prices.yaml"),
        "--output",
        str(RESULTS / "provider_costs.csv"),
    ])
    run([sys.executable, "-m", "scripts.make_tables", "--results", str(RESULTS)])
    run([sys.executable, "-m", "scripts.make_figures", "--results", str(RESULTS)])
    print("Analysis pipeline complete.")


if __name__ == "__main__":
    main()
