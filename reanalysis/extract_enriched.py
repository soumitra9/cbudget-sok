"""Phase 1 extractor: structural (non-outcome-dispersion) run properties.

Reads local raw traces under ``runs/<experiment>/<run>/{status.json,manifest.json,events.jsonl}``
and emits ``reanalysis/run_summary_enriched.csv``.

Freeze-leak restriction (see plan Phase 1): this file deliberately does NOT emit
``mean_pt_per_turn``, ``mean_gt_per_turn`` or any per-cell mean / treatment contrast.
Those reveal outcome dispersion and would let primary-estimand selection drift from
"effective n" toward "lowest variance". They are computed only in Phase 4, after the
freeze. Raw cumulative ``pt``/``gt``/``success`` are already public in the archived
``run_summary.csv`` and are carried through here for later phases; they are NOT used in
freeze selection. ``total_tool_output_tokens`` is outcome-adjacent (RTK acts on tool
output) but is required for the RTK fidelity table; it was computed pre-freeze and is
not used in selection (recorded in the frozen YAML).

The per-run ``traj_signature`` is a hash used only for equality grouping (determinism /
duplicate detection); it never exposes dispersion in a form usable for selection.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# experiment -> second factorial factor (matches analysis.estimate_interactions)
EXPERIMENT_FACTOR_B: dict[str, str] = {
    "e1_rtk_compaction": "compaction",
    "e1b_rtk_cod": "reasoning",
    "e1_sensitivity": "compaction",
}

# agent-executed test invocation (used for the "no test execution" degeneracy criterion)
_TEST_RE = re.compile(r"\b(pytest|unittest|python[0-9.]*\s+-m\s+pytest)\b")


def _factor_b_on(value: str, factor_key: str) -> int:
    if factor_key == "reasoning":
        return 1 if value == "cod" else 0
    # compaction (and default)
    return 0 if value in ("off", "", "standard", "none") or value is None else 1


def _iter_events(events_path: Path):
    with events_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def extract_run(run_dir: Path, experiment: str) -> dict[str, Any] | None:
    status_path = run_dir / "status.json"
    manifest_path = run_dir / "manifest.json"
    events_path = run_dir / "events.jsonl"
    if not (status_path.exists() and manifest_path.exists() and events_path.exists()):
        return None

    status = json.loads(status_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    treatment = manifest.get("treatment", {})
    factor_key = EXPERIMENT_FACTOR_B.get(experiment, "compaction")
    factor_default = "standard" if factor_key == "reasoning" else "off"
    factor_val = str(treatment.get(factor_key, factor_default))

    turns = 0
    n_tool_calls = 0
    ran_tests = False
    total_tool_output_tokens = 0
    rtk_supported_calls = 0
    rtk_fallback_calls = 0
    sig_parts: list[str] = []

    for e in _iter_events(events_path):
        etype = e.get("event_type")
        if etype == "model_request":
            turns += 1
        elif etype == "tool_request":
            n_tool_calls += 1
            cmd = str(e.get("original_command", ""))
            if _TEST_RE.search(cmd):
                ran_tests = True
            # structural signature element: turn index + command text (behavioural, not dispersion)
            sig_parts.append(f"{e.get('turn')}|{cmd}")
        elif etype == "tool_result":
            total_tool_output_tokens += int(e.get("output_tokens", 0) or 0)
            if e.get("rtk_supported"):
                rtk_supported_calls += 1
            if e.get("fallback_used"):
                rtk_fallback_calls += 1

    traj_signature = hashlib.sha256("\n".join(sig_parts).encode("utf-8")).hexdigest()[:16]

    rtk_on = 1 if treatment.get("rtk", "off") == "on" else 0
    factor_b_on = _factor_b_on(factor_val, factor_key)
    # RTK fidelity: share of tool calls actually compressed by RTK (supported and not fallback).
    rtk_fidelity = (
        (rtk_supported_calls - rtk_fallback_calls) / n_tool_calls if n_tool_calls else 0.0
    )

    return {
        "experiment": experiment,
        "run_id": manifest.get("run_id", run_dir.name),
        "task_id": manifest.get("task_id"),
        "seed": manifest.get("seed"),
        "rtk_on": rtk_on,
        "factor_key": factor_key,
        "factor_b_on": factor_b_on,
        "factor_b_value": factor_val,
        "compaction_trigger": treatment.get("compaction_trigger"),
        # already-public outcomes, carried for later phases; NOT used in freeze selection
        "pt": float(status.get("total_serialized_pt", 0)),
        "gt": float(status.get("total_gt", 0)),
        "success": bool(status.get("task_success", False)),
        # structural fields
        "turns": turns,
        "n_tool_calls": n_tool_calls,
        "ran_tests": ran_tests,
        "compaction_activated": int(status.get("total_compaction_gt", 0) or 0) > 0,
        "total_compaction_gt": int(status.get("total_compaction_gt", 0) or 0),
        "rtk_supported_calls": rtk_supported_calls,
        "rtk_fallback_calls": rtk_fallback_calls,
        "rtk_fidelity": round(rtk_fidelity, 4),
        "total_tool_output_tokens": total_tool_output_tokens,
        "traj_signature": traj_signature,
    }


def add_degeneracy(rows: list[dict[str, Any]]) -> None:
    """Add process-based degeneracy flags (any-of). Duplicate is within the
    (experiment, task, rtk_on, factor_b_on) cell."""
    sig_counts: dict[tuple, int] = {}
    for r in rows:
        key = (r["experiment"], r["task_id"], r["rtk_on"], r["factor_b_on"], r["traj_signature"])
        sig_counts[key] = sig_counts.get(key, 0) + 1
    for r in rows:
        key = (r["experiment"], r["task_id"], r["rtk_on"], r["factor_b_on"], r["traj_signature"])
        r["deg_zero_tools"] = r["n_tool_calls"] == 0
        r["deg_turn1"] = r["turns"] <= 1
        # deg_no_tests kept for transparency only; EXCLUDED from the canonical degenerate
        # flag. Inspection of the traces showed it misclassifies engaged 30-turn wall-hitting
        # runs (the grader runs pytest, so the agent often never types it). The plan listed it
        # as an OR criterion before the data was seen; the data contradicts it.
        r["deg_no_tests"] = not r["ran_tests"]
        r["deg_dup_in_cell"] = sig_counts[key] > 1
        r["degenerate"] = bool(
            r["deg_zero_tools"] or r["deg_turn1"] or r["deg_dup_in_cell"]
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--experiments",
        nargs="+",
        default=["e1_rtk_compaction", "e1b_rtk_cod", "e1_sensitivity"],
    )
    parser.add_argument("--runs-root", default=str(PROJECT_ROOT / "runs"))
    parser.add_argument("--output", default=str(PROJECT_ROOT / "reanalysis" / "run_summary_enriched.csv"))
    args = parser.parse_args()

    runs_root = Path(args.runs_root)
    rows: list[dict[str, Any]] = []
    for exp in args.experiments:
        exp_dir = runs_root / exp
        if not exp_dir.is_dir():
            print(f"WARN: {exp_dir} missing, skipping")
            continue
        for run_dir in sorted(exp_dir.iterdir()):
            if not run_dir.is_dir() or ".attempt" in run_dir.name:
                continue
            row = extract_run(run_dir, exp)
            if row is not None:
                rows.append(row)

    add_degeneracy(rows)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # brief console summary (counts only, no treatment contrast)
    by_exp: dict[str, int] = {}
    deg_by_exp: dict[str, int] = {}
    for r in rows:
        by_exp[r["experiment"]] = by_exp.get(r["experiment"], 0) + 1
        deg_by_exp[r["experiment"]] = deg_by_exp.get(r["experiment"], 0) + int(r["degenerate"])
    print(f"Wrote {len(rows)} runs to {out}")
    for exp in by_exp:
        print(f"  {exp}: n={by_exp[exp]} degenerate={deg_by_exp[exp]}")


if __name__ == "__main__":
    main()
