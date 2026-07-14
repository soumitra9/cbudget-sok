"""Estimate 2x2 interaction effects with fixed blocking factors."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from analysis.bootstrap import bootstrap_block_statistic, write_bootstrap_result


def _factor_b_on(value: str, factor_key: str) -> int:
    if factor_key == "compaction":
        return 0 if value in ("off", "", None) else 1
    if factor_key == "reasoning":
        return 1 if value == "cod" else 0
    return 0 if value in ("off", "standard", "", None) else 1


def load_runs(runs_dir: Path) -> pd.DataFrame:
    rows = []
    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir() or ".attempt" in run_dir.name:
            continue
        status_path = run_dir / "status.json"
        manifest_path = run_dir / "manifest.json"
        if not status_path.exists() or not manifest_path.exists():
            continue
        status = json.loads(status_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        treatment = manifest.get("treatment", {})
        if "compaction" in treatment:
            factor_key = "compaction"
            factor_b = treatment.get("compaction", "off")
        else:
            factor_key = "reasoning"
            factor_b = treatment.get("reasoning", "standard")
        rows.append(
            {
                "run_id": manifest.get("run_id", run_dir.name),
                "task_id": manifest.get("task_id"),
                "seed": manifest.get("seed"),
                "rtk": treatment.get("rtk", "off"),
                "factor_key": factor_key,
                "factor_b": factor_b,
                "rtk_on": 1 if treatment.get("rtk", "off") == "on" else 0,
                "factor_b_on": _factor_b_on(str(factor_b), factor_key),
                "pt": float(status.get("total_serialized_pt", 0)),
                "gt": float(status.get("total_gt", 0)),
                "success": bool(status.get("task_success", False)),
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df["interaction_on"] = df["rtk_on"] * df["factor_b_on"]
    return df


def cell_means(df: pd.DataFrame, value_col: str = "pt") -> dict[str, float]:
    means: dict[str, float] = {}
    for rtk_on in (0, 1):
        for factor_b_on in (0, 1):
            sub = df[(df["rtk_on"] == rtk_on) & (df["factor_b_on"] == factor_b_on)]
            key = f"Y{rtk_on}{factor_b_on}"
            means[key] = float(sub[value_col].mean()) if not sub.empty else float("nan")
    return means


def raw_interaction_from_means(means: dict[str, float]) -> float:
    return float(means["Y11"] - means["Y10"] - means["Y01"] + means["Y00"])


def log_multiplicative_interaction_from_means(means: dict[str, float], *, epsilon: float = 1.0) -> float:
    adjusted = {key: max(value, epsilon) for key, value in means.items()}
    return float(
        np.log(adjusted["Y11"])
        - np.log(adjusted["Y10"])
        - np.log(adjusted["Y01"])
        + np.log(adjusted["Y00"])
    )


def success_adjusted_cost(df: pd.DataFrame, value_col: str = "pt") -> float:
    successes = int(df["success"].sum())
    if successes == 0:
        return float("nan")
    return float(df[value_col].sum() / successes)


def success_adjusted_cost_by_cell(df: pd.DataFrame, value_col: str = "pt") -> dict[str, float]:
    costs: dict[str, float] = {}
    for rtk_on in (0, 1):
        for factor_b_on in (0, 1):
            sub = df[(df["rtk_on"] == rtk_on) & (df["factor_b_on"] == factor_b_on)]
            key = f"Y{rtk_on}{factor_b_on}"
            costs[key] = success_adjusted_cost(sub, value_col=value_col) if not sub.empty else float("nan")
    return costs


def fit_ols_interaction_model(df: pd.DataFrame, outcome_col: str = "pt") -> dict[str, Any]:
    if df.empty:
        raise ValueError("Cannot fit model on empty dataframe.")

    task_dummies = pd.get_dummies(df["task_id"], prefix="task", drop_first=True, dtype=float)
    seed_dummies = pd.get_dummies(df["seed"], prefix="seed", drop_first=True, dtype=float)
    design = pd.DataFrame(
        {
            "const": 1.0,
            "rtk_on": df["rtk_on"].astype(float),
            "factor_b_on": df["factor_b_on"].astype(float),
            "interaction_on": df["interaction_on"].astype(float),
        }
    )
    x = pd.concat([design, task_dummies, seed_dummies], axis=1)
    y = df[outcome_col].astype(float).to_numpy()
    beta, _, _, _ = np.linalg.lstsq(x.to_numpy(), y, rcond=None)
    y_hat = x.to_numpy() @ beta
    resid = y - y_hat
    n_obs, n_params = x.shape
    dof = max(n_obs - n_params, 1)
    sigma2 = float(np.sum(resid**2) / dof)
    xtx_inv = np.linalg.pinv(x.to_numpy().T @ x.to_numpy())
    se = np.sqrt(np.clip(np.diag(sigma2 * xtx_inv), 0.0, None))

    coef_names = list(x.columns)
    coefficients = {
        name: {"estimate": float(est), "std_error": float(err)}
        for name, est, err in zip(coef_names, beta, se, strict=True)
    }
    return {
        "formula": "PT_trajectory ~ rtk + factor_b + rtk:factor_b + task + seed",
        "outcome": outcome_col,
        "n_obs": int(n_obs),
        "n_params": int(n_params),
        "r_squared": float(1.0 - np.sum(resid**2) / np.sum((y - y.mean()) ** 2)) if n_obs > 1 else float("nan"),
        "coefficients": coefficients,
    }


def compute_estimands(df: pd.DataFrame, outcome_col: str = "pt") -> dict[str, Any]:
    outcome_means = cell_means(df, outcome_col)
    sac_by_cell = success_adjusted_cost_by_cell(df, outcome_col)
    return {
        "raw_interaction": {
            "formula": "Y11 - Y10 - Y01 + Y00",
            "cell_means": outcome_means,
            "value": raw_interaction_from_means(outcome_means),
        },
        "log_multiplicative_interaction": {
            "formula": "log Y11 - log Y10 - log Y01 + log Y00",
            "cell_means": outcome_means,
            "value": log_multiplicative_interaction_from_means(outcome_means),
        },
        "success_adjusted_cost": {
            "formula": "sum_i C_i / sum_i 1[success_i]",
            "by_cell": sac_by_cell,
            "overall": success_adjusted_cost(df, outcome_col),
            "interaction_on_sac": raw_interaction_from_means(sac_by_cell),
        },
    }


def outcome_col_from_hypothesis(hypothesis: dict[str, Any]) -> str:
    primary = str(hypothesis.get("primary_outcome", "")).lower()
    if "generated" in primary or primary.endswith("_gt"):
        return "gt"
    return "pt"


def load_hypothesis(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--hypothesis",
        default="configs/hypotheses/e1_frozen.yaml",
        help="Pre-registered hypothesis file for model/estimand metadata",
    )
    parser.add_argument("--bootstrap-n", type=int, default=1000)
    parser.add_argument("--bootstrap-seed", type=int, default=0)
    parser.add_argument("--outcome", choices=("pt", "gt"), default=None, help="Override primary outcome column")
    args = parser.parse_args()

    runs_dir = Path(args.runs)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    df = load_runs(runs_dir)
    df.to_csv(out / "run_summary.csv", index=False)

    hypothesis = load_hypothesis(Path(args.hypothesis))
    outcome_col = args.outcome or outcome_col_from_hypothesis(hypothesis)
    result: dict[str, Any] = {
        "experiment_runs_dir": str(runs_dir),
        "hypothesis_file": args.hypothesis,
        "outcome_col": outcome_col,
        "pre_registered_model": hypothesis.get("statistical_model", {}).get(
            "default", "PT_trajectory ~ rtk + compaction + rtk:compaction + task + seed"
        ),
        "n_runs": int(len(df)),
    }

    if df.empty:
        result["status"] = "no_runs"
        (out / "analysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("No runs found.")
        return

    pivot = df.groupby(["rtk_on", "factor_b_on"])[outcome_col].mean().unstack(fill_value=np.nan)
    pivot.to_csv(out / f"cell_means_{outcome_col}.csv")

    model_fit = fit_ols_interaction_model(df, outcome_col=outcome_col)
    estimands = compute_estimands(df, outcome_col=outcome_col)
    raw_point = estimands["raw_interaction"]["value"]
    raw_bootstrap = bootstrap_block_statistic(
        df,
        statistic=lambda frame: raw_interaction_from_means(cell_means(frame, outcome_col)),
        n=args.bootstrap_n,
        seed=args.bootstrap_seed,
    )
    raw_bootstrap["estimand"] = "raw_interaction"
    raw_bootstrap["pre_registered"] = True

    result.update(
        {
            "status": "ok",
            "model_fit": model_fit,
            "estimands": estimands,
            "raw_interaction_bootstrap": raw_bootstrap,
            "confirmatory_interaction_coefficient": model_fit["coefficients"].get("interaction_on"),
            "hypothesis_direction": hypothesis.get("hypotheses", {}),
        }
    )

    (out / "analysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_bootstrap_result(raw_bootstrap, out / "raw_interaction_bootstrap.json")

    estimand_rows = []
    for name, payload in estimands.items():
        estimand_rows.append({"estimand": name, "value": payload.get("value", payload.get("interaction_on_sac"))})
    pd.DataFrame(estimand_rows).to_csv(out / "estimands.csv", index=False)

    coef_rows = [
        {"term": term, **stats}
        for term, stats in model_fit["coefficients"].items()
    ]
    pd.DataFrame(coef_rows).to_csv(out / "model_coefficients.csv", index=False)

    print(
        f"Wrote analysis to {out}: raw_interaction={raw_point:.4f} "
        f"bootstrap CI [{raw_bootstrap['ci_low']:.4f}, {raw_bootstrap['ci_high']:.4f}]"
    )


if __name__ == "__main__":
    main()
