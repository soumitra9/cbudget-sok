"""Significance audit: for EVERY token-outcome contrast, is it distinguishable from zero?

This exists to stop the find-headline / verify / retract cycle. It computes, for each
outcome and each factorial contrast, the point estimate and a task-seed block-bootstrap
95% CI (the frozen inference method, which also handles the within-(task,seed) pairing
that cancels between-task variance). A contrast is only usable if its CI excludes zero.

If nothing survives for raw cumulative PT/GT, the honest paper is a taxonomy + accounting
framework + methodological pilot (protocol and required sample size), not an empirical
token-outcome finding.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENRICHED = PROJECT_ROOT / "reanalysis" / "run_summary_enriched.csv"
OUT = PROJECT_ROOT / "reanalysis" / "significance_audit.json"

OUTCOMES = ["pt", "gt", "pt_per_turn", "gt_per_turn", "turns", "total_tool_output_tokens"]


def main_rtk(df, col):
    return float(df[df.rtk_on == 1][col].mean() - df[df.rtk_on == 0][col].mean())


def main_comp(df, col):
    return float(df[df.factor_b_on == 1][col].mean() - df[df.factor_b_on == 0][col].mean())


def interaction(df, col):
    m = df.groupby(["rtk_on", "factor_b_on"])[col].mean()
    return float(m[(1, 1)] - m[(1, 0)] - m[(0, 1)] + m[(0, 0)])


CONTRASTS = {"rtk_main": main_rtk, "compaction_main": main_comp, "interaction": interaction}


def block_bootstrap_full(df, statistic, block_cols=("task_id", "seed"), n=1000, seed=0):
    """Block bootstrap that also returns SE (std of replicates), matching the frozen
    harness's resampling exactly (same rng seed/n/block grouping -> identical CIs)."""
    blocks = list(df.groupby(list(block_cols), dropna=False))
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(n):
        chosen = rng.choice(len(blocks), size=len(blocks), replace=True)
        boot_df = pd.concat([blocks[i][1] for i in chosen], ignore_index=True)
        samples.append(float(statistic(boot_df)))
    samples = np.asarray(samples)
    point = float(statistic(df))
    se = float(samples.std(ddof=1))
    return {
        "point": point,
        "se": se,
        "t": (point / se) if se > 0 else float("nan"),
        "ci_low": float(np.percentile(samples, 2.5)),
        "ci_high": float(np.percentile(samples, 97.5)),
        "n_blocks": len(blocks),
    }


def audit(df, experiment):
    out = {}
    for cname, cfun in CONTRASTS.items():
        for col in OUTCOMES:
            try:
                res = block_bootstrap_full(
                    df, lambda d, c=col, f=cfun: f(d, c),
                    block_cols=("task_id", "seed"), n=1000, seed=0,
                )
            except Exception as e:  # noqa: BLE001
                out[f"{cname}::{col}"] = {"error": str(e)}
                continue
            excl = bool(res["ci_low"] > 0 or res["ci_high"] < 0)
            out[f"{cname}::{col}"] = {
                "point": round(res["point"], 3),
                "se": round(res["se"], 3),
                "t": round(res["t"], 3),
                "ci95": [round(res["ci_low"], 1), round(res["ci_high"], 1)],
                "n_blocks": res["n_blocks"],
                "distinguishable_from_zero": excl,
            }
    return out


def main() -> None:
    df = pd.read_csv(ENRICHED)
    df["pt_per_turn"] = df["pt"] / df["turns"]
    df["gt_per_turn"] = df["gt"] / df["turns"]
    result = {}
    for exp in ["e1_rtk_compaction", "e1b_rtk_cod"]:
        sub = df[df.experiment == exp].copy()
        result[exp] = audit(sub, exp)
    # summary: how many contrasts are distinguishable from zero?
    n_sig = sum(
        1 for exp in result for k, v in result[exp].items() if v.get("distinguishable_from_zero")
    )
    n_tot = sum(1 for exp in result for k in result[exp])
    result["_summary"] = {
        "n_contrasts": n_tot,
        "n_distinguishable_from_zero": n_sig,
        "note": "e1b_rtk_cod (E2) is contaminated by 72% process-degenerate runs and CoD-arm collider; its entries are descriptive only.",
    }
    OUT.write_text(json.dumps(result, indent=2))
    # console table
    for exp in ["e1_rtk_compaction", "e1b_rtk_cod"]:
        print(f"\n=== {exp} ===")
        for k, v in result[exp].items():
            flag = "  SIG" if v.get("distinguishable_from_zero") else "  ns "
            print(f"{flag}  {k:38s} point={v['point']:>14}  SE={v['se']:>12}  t={v['t']:>7}  CI={v['ci95']}")
    print(f"\nSUMMARY: {n_sig}/{n_tot} contrasts distinguishable from zero")


if __name__ == "__main__":
    main()
