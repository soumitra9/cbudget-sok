"""Bootstrap helpers for confirmatory estimands."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def bootstrap_statistic(
    values: np.ndarray,
    statistic: Callable[[np.ndarray], float],
    *,
    n: int = 1000,
    seed: int = 0,
) -> dict[str, Any]:
    if len(values) == 0:
        raise ValueError("No values to bootstrap.")
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(n):
        draw = rng.choice(values, size=len(values), replace=True)
        samples.append(float(statistic(draw)))
    point = float(statistic(values))
    return {
        "point_estimate": point,
        "ci_low": float(np.percentile(samples, 2.5)),
        "ci_high": float(np.percentile(samples, 97.5)),
        "n_bootstrap": n,
        "n_obs": int(len(values)),
    }


def bootstrap_block_statistic(
    df: pd.DataFrame,
    statistic: Callable[[pd.DataFrame], float],
    *,
    block_cols: tuple[str, ...] = ("task_id", "seed"),
    n: int = 1000,
    seed: int = 0,
) -> dict[str, Any]:
    if df.empty:
        raise ValueError("Empty dataframe for block bootstrap.")
    blocks = list(df.groupby(list(block_cols), dropna=False))
    if not blocks:
        raise ValueError("No blocks found for block bootstrap.")
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(n):
        chosen = rng.choice(len(blocks), size=len(blocks), replace=True)
        boot_df = pd.concat([blocks[i][1] for i in chosen], ignore_index=True)
        samples.append(float(statistic(boot_df)))
    point = float(statistic(df))
    return {
        "point_estimate": point,
        "ci_low": float(np.percentile(samples, 2.5)),
        "ci_high": float(np.percentile(samples, 97.5)),
        "n_bootstrap": n,
        "n_blocks": len(blocks),
        "n_obs": int(len(df)),
    }


def write_bootstrap_result(result: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(result)
    if "ci_low" in payload and "ci_lower" not in payload:
        payload["ci_lower"] = payload["ci_low"]
    if "ci_high" in payload and "ci_upper" not in payload:
        payload["ci_upper"] = payload["ci_high"]
    if "ci_low" in payload and "ci_high" in payload and "ci_width" not in payload:
        payload["ci_width"] = float(payload["ci_high"]) - float(payload["ci_low"])
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="CSV with run-level rows")
    parser.add_argument("--column", default="pt", help="Column for simple mean bootstrap")
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    if args.column not in df.columns:
        raise SystemExit(f"Column {args.column!r} not found in {args.input}")
    result = bootstrap_statistic(
        df[args.column].to_numpy(),
        statistic=lambda values: float(np.mean(values)),
        n=args.n,
    )
    write_bootstrap_result(result, Path(args.output))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
