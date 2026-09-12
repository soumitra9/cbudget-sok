"""Falsifiable calibration test of the recurrence model (Eqs 4-7), NOT the Eq-8 identity.

Eq.5: a tool-output reduction dO_k at turn k propagates to dPT = dO_k * (T-k) under
FULL RETENTION. This script computes the model's predicted tool-output contribution to
cumulative PT using the ACTUAL per-turn tool-output positions (the real (T-1-k) weights),
compares it to the observed dPT for the RTK contrasts, and contrasts that with the naive
uniform-spread prediction. It also measures actual history retention from the per-turn
region telemetry, to diagnose WHY the model mis-predicts.

Unlike the Oaxaca split (an algebraic identity), this test could fail: if the weighted
prediction does not match the observed saving, the model is wrong for this dataset.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNS = PROJECT_ROOT / "runs" / "e1_rtk_compaction"
OUT = PROJECT_ROOT / "reanalysis" / "calibration_eq5.json"

def _comp_on(v) -> int:  # E1 factor_b = compaction on/off (matches extract_enriched)
    return 0 if str(v) in ("off", "standard", "none", "None", "") else 1


def parse_run(run_dir: Path) -> dict | None:
    ev = run_dir / "events.jsonl"
    man = run_dir / "manifest.json"
    st = run_dir / "status.json"
    if not (ev.exists() and man.exists() and st.exists()):
        return None
    manifest = json.loads(man.read_text())
    status = json.loads(st.read_text())
    treat = manifest.get("treatment", {})

    tool_by_turn: dict[int, int] = {}
    gen_by_turn: dict[int, int] = {}
    hist_by_turn: dict[int, int] = {}      # actual serialized history region per model_request
    serialized_by_turn: dict[int, int] = {}
    n_requests = 0
    for line in ev.open():
        line = line.strip()
        if not line:
            continue
        e = json.loads(line)
        et = e.get("event_type")
        if et == "model_request":
            n_requests += 1
            t = e.get("turn")
            serialized_by_turn[t] = int(e.get("prompt_tokens_serialized", 0) or 0)
            regions = e.get("regions", {}) or {}
            hist_by_turn[t] = int(regions.get("history", 0) or 0)
        elif et == "tool_result":
            tool_by_turn[e.get("turn")] = int(e.get("output_tokens", 0) or 0)
        elif et == "model_response":
            gen_by_turn[e.get("turn")] = int(e.get("generated_tokens", 0) or 0)

    T = n_requests
    # weighted (actual positions): a token produced at turn k is re-served at turns k+1..T-1
    W_tool = sum(o * (T - 1 - k) for k, o in tool_by_turn.items() if k < T)
    W_gen = sum(g * (T - 1 - k) for k, g in gen_by_turn.items() if k < T)
    O_total = sum(tool_by_turn.values())
    uniform_tool = O_total * (T - 1) / 2 if T > 1 else 0.0
    # actual replayed tool volume is not directly separable; use history-region retention as a proxy:
    # ratio of actual summed history region to the full-retention cumulative content
    cum_content = 0
    full_ret_hist = 0
    for k in range(T):
        full_ret_hist += cum_content                      # history the model WOULD serialize at turn k
        cum_content += gen_by_turn.get(k, 0) + tool_by_turn.get(k, 0)
    actual_hist = sum(hist_by_turn.values())
    retention = actual_hist / full_ret_hist if full_ret_hist else float("nan")

    return {
        "run_id": manifest.get("run_id", run_dir.name),
        "task_id": manifest.get("task_id"),
        "seed": manifest.get("seed"),
        "rtk_on": 1 if treat.get("rtk") == "on" else 0,
        "factor_b_on": _comp_on(treat.get("compaction", "off")),
        "T": T,
        "pt": float(status.get("total_serialized_pt", 0)),
        "O_total": O_total,
        "W_tool_weighted": W_tool,
        "W_gen_weighted": W_gen,
        "uniform_tool": uniform_tool,
        "actual_history_sum": actual_hist,
        "full_retention_history": full_ret_hist,
        "retention_ratio": retention,
    }


def contrast(cells: pd.DataFrame, ref, treat, label):
    def m(cell, col):
        return float(cells[(cells.rtk_on == cell[0]) & (cells.factor_b_on == cell[1])][col].iloc[0])

    obs = m(treat, "pt") - m(ref, "pt")
    weighted = m(treat, "W_tool_weighted") - m(ref, "W_tool_weighted")
    uniform = m(treat, "uniform_tool") - m(ref, "uniform_tool")
    d_gen = m(treat, "W_gen_weighted") - m(ref, "W_gen_weighted")
    return {
        "contrast": label,
        "observed_dPT": obs,
        "uniform_pred_dPT": uniform,
        "weighted_pred_dPT": weighted,
        "uniform_over_observed": uniform / obs if obs else float("nan"),
        "weighted_over_observed": weighted / obs if obs else float("nan"),
        "d_gen_amplified": d_gen,   # change in generation-replay term (downstream behaviour)
        "gen_offset_of_tool_saving": d_gen / -weighted if weighted else float("nan"),
        "toolplusgen_pred_dPT": weighted + d_gen,   # if downstream behaviour is the only other channel
        "toolplusgen_over_observed": (weighted + d_gen) / obs if obs else float("nan"),
        "mean_retention_ref": m(ref, "retention_ratio"),
        "mean_retention_treat": m(treat, "retention_ratio"),
    }


def main() -> None:
    rows = [r for d in sorted(RUNS.iterdir()) if d.is_dir() and (r := parse_run(d))]
    df = pd.DataFrame(rows)
    cells = (
        df.groupby(["rtk_on", "factor_b_on"])
        .agg(
            pt=("pt", "mean"),
            O_total=("O_total", "mean"),
            W_tool_weighted=("W_tool_weighted", "mean"),
            W_gen_weighted=("W_gen_weighted", "mean"),
            uniform_tool=("uniform_tool", "mean"),
            retention_ratio=("retention_ratio", "mean"),
            T=("T", "mean"),
        )
        .reset_index()
    )
    result = {
        "test": "Eq.5 full-retention prediction vs observed dPT for RTK (falsifiable)",
        "cell_means": cells.to_dict(orient="records"),
        "rtk_contrasts": [
            contrast(cells, (0, 0), (1, 0), "RTK at compaction_off (Y00->Y10)"),
            contrast(cells, (0, 1), (1, 1), "RTK at compaction_on (Y01->Y11)"),
        ],
    }
    OUT.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
