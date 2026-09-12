"""Phase 2 pre-freeze gates (run properties only; no treatment-contrast estimated).

Computes, from reanalysis/run_summary_enriched.csv:
  1. Determinism / effective-n: distinct trajectories per (task, arm) across seeds;
     bug-vs-temperature verdict; effective n per cell.
  2. Degeneracy audit (process-based) folded into effective n.
  3. e1_sensitivity eligibility: genuine 2x2 same factors vs tau-sweep.

Outputs reanalysis/phase2_gates.json. These results feed the freeze in Phase 3.
None of this touches per-turn outcome dispersion or any interaction estimate.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENRICHED = PROJECT_ROOT / "reanalysis" / "run_summary_enriched.csv"
OUT = PROJECT_ROOT / "reanalysis" / "phase2_gates.json"

ARMS = [(0, 0), (0, 1), (1, 0), (1, 1)]


def determinism_report(df: pd.DataFrame) -> dict:
    """Per experiment: how much do seeds diverge? Effective n per cell."""
    out = {}
    for exp, sub in df.groupby("experiment"):
        seeds = sorted(sub["seed"].unique().tolist())
        cells = []  # one per (task, arm)
        for (task, r, f), g in sub.groupby(["task_id", "rtk_on", "factor_b_on"]):
            cells.append(
                {
                    "task": task,
                    "rtk_on": int(r),
                    "factor_b_on": int(f),
                    "n_seeds": int(g["seed"].nunique()),
                    "distinct_traj": int(g["traj_signature"].nunique()),
                }
            )
        cdf = pd.DataFrame(cells)
        n_cells = len(cdf)
        all_identical = int((cdf["distinct_traj"] == 1).sum())
        fully_divergent = int((cdf["distinct_traj"] == cdf["n_seeds"]).sum())
        # effective n per arm = sum over tasks of distinct trajectories in that (task, arm)
        eff_by_arm = {}
        nom_by_arm = {}
        for (r, f) in ARMS:
            arm = cdf[(cdf["rtk_on"] == r) & (cdf["factor_b_on"] == f)]
            armruns = sub[(sub["rtk_on"] == r) & (sub["factor_b_on"] == f)]
            if len(armruns) == 0:
                continue
            eff_by_arm[f"Y{r}{f}"] = int(arm["distinct_traj"].sum())
            nom_by_arm[f"Y{r}{f}"] = int(len(armruns))
        out[exp] = {
            "seeds": seeds,
            "n_seeds": len(seeds),
            "n_task_arm_cells": n_cells,
            "cells_all_seeds_identical": all_identical,
            "cells_fully_divergent": fully_divergent,
            "mean_distinct_traj_per_cell": round(float(cdf["distinct_traj"].mean()), 3),
            "nominal_n_per_arm": nom_by_arm,
            "effective_n_per_arm": eff_by_arm,
            "min_effective_n_per_arm": min(eff_by_arm.values()) if eff_by_arm else None,
        }
    return out


def bug_vs_temperature(det: dict) -> dict:
    """A seeding bug => ALL cells identical across seeds in EVERY experiment (incl. E1's
    two seeds). If any experiment shows seeds diverging, seeds are functional and the
    collapse elsewhere is temperature/task-triviality driven."""
    e1 = det.get("e1_rtk_compaction", {})
    e1_diverges = e1.get("cells_all_seeds_identical", None) == 0 and e1.get("n_task_arm_cells", 0) > 0
    verdict = "temperature_determinism" if e1_diverges else "possible_seeding_bug"
    return {
        "verdict": verdict,
        "basis": (
            "E1's two seeds diverge in every task-arm cell (cells_all_seeds_identical=0), "
            "so seeds are applied and functional; the E2/e1_sensitivity collapse is driven by "
            "temperature-0.2 near-greedy determinism on trivial fixtures, not a seeding bug."
            if e1_diverges
            else "E1 shows seed-identical cells; a seeding bug cannot be ruled out and a repair re-run may be warranted."
        ),
        "repair_rerun_preauthorized": not e1_diverges,
    }


def e1_sensitivity_eligibility(df: pd.DataFrame) -> dict:
    s = df[df["experiment"] == "e1_sensitivity"]
    if len(s) == 0:
        return {"present": False}
    triggers = sorted([t for t in s["compaction_trigger"].dropna().unique().tolist()])
    arms_present = sorted({(int(r), int(f)) for r, f in zip(s["rtk_on"], s["factor_b_on"])})
    n_trigger_values = s["compaction_trigger"].nunique(dropna=True)
    # genuine 2x2 requires both factors to vary and tau constant within the design
    genuine_2x2 = len(arms_present) == 4
    tau_constant = n_trigger_values <= 1
    return {
        "present": True,
        "n_runs": int(len(s)),
        "tasks": sorted(s["task_id"].unique().tolist()),
        "seeds": sorted(s["seed"].unique().tolist()),
        "arms_present_rtk_factorb": [list(a) for a in arms_present],
        "distinct_compaction_trigger_values": triggers,
        "n_distinct_trigger_values": int(n_trigger_values),
        "is_genuine_2x2_same_factors": bool(genuine_2x2),
        "tau_constant_across_cells": bool(tau_constant),
        "eligible_as_primary": bool(genuine_2x2 and tau_constant),
        "note": (
            "If tau varies across cells it is a third factor and the estimand is not E1's "
            "quantity; e1_sensitivity is also non-preregistered (outside the frozen hypothesis files)."
        ),
    }


def main() -> None:
    df = pd.read_csv(ENRICHED)
    det = determinism_report(df)
    report = {
        "source": "reanalysis/run_summary_enriched.csv",
        "determinism": det,
        "bug_vs_temperature": bug_vs_temperature(det),
        "e1_sensitivity_eligibility": e1_sensitivity_eligibility(df),
        "degeneracy_by_experiment": {
            exp: {
                "n": int(len(g)),
                "degenerate": int(g["degenerate"].sum()),
                "non_degenerate": int((~g["degenerate"]).sum()),
            }
            for exp, g in df.groupby("experiment")
        },
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
