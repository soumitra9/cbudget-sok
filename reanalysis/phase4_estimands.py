"""Phase 4: compute post-freeze estimands per reanalysis/rule_frozen.yaml.

Derived per-turn columns are computed HERE (post-freeze), never earlier. Applies the
frozen rule: primary = E1 pt_per_turn interaction with task-seed block bootstrap; plus
the pre-specified post-hoc / descriptive analyses and the Oaxaca decomposition.
Outputs reanalysis/phase4_estimands.json and reanalysis/phase4_cell_means.csv.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from analysis.bootstrap import bootstrap_block_statistic

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENRICHED = PROJECT_ROOT / "reanalysis" / "run_summary_enriched.csv"
RULE = PROJECT_ROOT / "reanalysis" / "rule_frozen.yaml"
OUT_JSON = PROJECT_ROOT / "reanalysis" / "phase4_estimands.json"
OUT_CELLS = PROJECT_ROOT / "reanalysis" / "phase4_cell_means.csv"


def interaction_stat(df: pd.DataFrame, outcome: str) -> float:
    m = df.groupby(["rtk_on", "factor_b_on"])[outcome].mean()
    return float(m[(1, 1)] - m[(1, 0)] - m[(0, 1)] + m[(0, 0)])


def block_ci(df: pd.DataFrame, outcome: str) -> dict:
    return bootstrap_block_statistic(
        df, lambda d: interaction_stat(d, outcome), block_cols=("task_id", "seed"), n=1000, seed=0
    )


def cell_table(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["rtk_on", "factor_b_on"])
    tab = g.agg(
        n=("run_id", "size"),
        mean_pt=("pt", "mean"),
        mean_gt=("gt", "mean"),
        mean_turns=("turns", "mean"),
        mean_pt_per_turn=("pt_per_turn", "mean"),
        mean_gt_per_turn=("gt_per_turn", "mean"),
        success_rate=("success", "mean"),
    ).reset_index()
    # aggregate occupancy = mean(pt)/mean(turns) so that T*O == mean_pt exactly
    tab["occ"] = tab["mean_pt"] / tab["mean_turns"]
    return tab


def oaxaca(tab: pd.DataFrame, ref=(0, 0), treat=(1, 1)) -> dict:
    def get(cell, col):
        row = tab[(tab.rtk_on == cell[0]) & (tab.factor_b_on == cell[1])].iloc[0]
        return float(row[col])

    T00, O00 = get(ref, "mean_turns"), get(ref, "occ")
    T11, O11 = get(treat, "mean_turns"), get(treat, "occ")
    dT, dO = T11 - T00, O11 - O00
    delta_pt = T11 * O11 - T00 * O00
    replay = dT * O00          # trajectory-length change valued at baseline per-turn cost
    per_turn = T00 * dO        # per-turn occupancy change over baseline trajectory length
    remainder = dT * dO        # interaction of the two deltas
    ratio = abs(remainder) / abs(delta_pt) if delta_pt else float("nan")
    return {
        "reference_cell": f"Y{ref[0]}{ref[1]}",
        "treated_cell": f"Y{treat[0]}{treat[1]}",
        "delta_pt": delta_pt,
        "replay_term_dturns_x_occ": replay,
        "per_turn_term_turns_x_docc": per_turn,
        "remainder_dT_x_dO": remainder,
        "remainder_ratio": ratio,
        "clean_separation": bool(ratio < 0.15),
        "components_sum_check": replay + per_turn + remainder,
    }


def main() -> None:
    rule = yaml.safe_load(RULE.read_text())
    df = pd.read_csv(ENRICHED)
    df["pt_per_turn"] = df["pt"] / df["turns"]
    df["gt_per_turn"] = df["gt"] / df["turns"]

    e1 = df[df.experiment == "e1_rtk_compaction"].copy()
    e2 = df[df.experiment == "e1b_rtk_cod"].copy()

    tab_e1 = cell_table(e1)
    tab_e2 = cell_table(e2)
    pd.concat(
        [tab_e1.assign(experiment="e1_rtk_compaction"), tab_e2.assign(experiment="e1b_rtk_cod")]
    ).to_csv(OUT_CELLS, index=False)

    # ---- PRIMARY (frozen) ----
    primary = block_ci(e1, "pt_per_turn")
    primary["excludes_zero"] = bool(primary["ci_low"] > 0 or primary["ci_high"] < 0)

    # ---- pre-specified post-hoc ----
    turns_int = block_ci(e1, "turns")
    turns_int["excludes_zero"] = bool(turns_int["ci_low"] > 0 or turns_int["ci_high"] < 0)

    # ---- descriptive: E2 gt_per_turn (collider caveat), unfiltered ----
    e2_int = block_ci(e2, "gt_per_turn")
    e2_int["excludes_zero"] = bool(e2_int["ci_low"] > 0 or e2_int["ci_high"] < 0)

    # ---- descriptive: success-only E1 pt_per_turn (collider; point estimate only) ----
    e1_succ = e1[e1.success]
    try:
        succ_point = interaction_stat(e1_succ, "pt_per_turn")
    except (KeyError, IndexError):
        succ_point = None

    result = {
        "input_data_sha256": rule["meta"]["input_data"]["sha256"],
        "rule_sha256_file": "reanalysis/rule_frozen.sha256",
        "primary": {
            "experiment": "e1_rtk_compaction",
            "outcome": "pt_per_turn",
            "estimand": "interaction Y11-Y10-Y01+Y00",
            "point_estimate": primary["point_estimate"],
            "ci95": [primary["ci_low"], primary["ci_high"]],
            "n_blocks": primary["n_blocks"],
            "n_obs": primary["n_obs"],
            "excludes_zero": primary["excludes_zero"],
            "branch": (
                "primary_ci_excludes_zero" if primary["excludes_zero"] else "primary_ci_includes_zero"
            ),
        },
        "secondary_prespecified_posthoc": {
            "turns_interaction_e1": {
                "point_estimate": turns_int["point_estimate"],
                "ci95": [turns_int["ci_low"], turns_int["ci_high"]],
                "excludes_zero": turns_int["excludes_zero"],
            }
        },
        "descriptive": {
            "e2_gt_per_turn_interaction_UNFILTERED": {
                "point_estimate": e2_int["point_estimate"],
                "ci95": [e2_int["ci_low"], e2_int["ci_high"]],
                "caveat": "collider (degeneracy loads on CoD) + gt=11 collapse contamination; descriptive only",
            },
            "success_only_e1_pt_per_turn_interaction": {
                "point_estimate": succ_point,
                "n_success": int(e1.success.sum()),
                "caveat": "success is post-treatment (collider); descriptive only, no inference",
            },
        },
        "oaxaca_e1": oaxaca(tab_e1),
    }
    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print("\n--- E1 cell means ---")
    print(tab_e1.to_string(index=False))


if __name__ == "__main__":
    main()
