"""Bootstrap CI helper."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--column", default="pt")
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    values = df[args.column].to_numpy()
    if len(values) == 0:
        raise SystemExit("No values to bootstrap.")

    rng = np.random.default_rng(0)
    samples = []
    for _ in range(args.n):
        draw = rng.choice(values, size=len(values), replace=True)
        samples.append(float(np.mean(draw)))

    result = {
        "mean": float(np.mean(values)),
        "ci_low": float(np.percentile(samples, 2.5)),
        "ci_high": float(np.percentile(samples, 97.5)),
        "n": int(len(values)),
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
