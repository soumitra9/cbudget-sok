"""Environment validation for RunPod A40 + vLLM."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import httpx
import yaml

from cbudget.models.client import ModelClient


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    assert cfg.get("provider") == "runpod", "provider must be runpod"
    assert cfg.get("gpu"), "gpu must be configured"
    print(f"Environment config OK: gpu={cfg.get('gpu')}")

    base_url = os.environ.get("VLLM_BASE_URL", cfg.get("vllm_base_url", "http://localhost:8000"))
    client = ModelClient(base_url=base_url, use_mock=False)
    try:
        result = client.generate("Respond with OK only.", max_tokens=8, temperature=0.0)
        print(f"vLLM smoke OK: {result.text[:80]!r}")
    except Exception as exc:
        print(f"vLLM smoke FAILED: {exc}")
        sys.exit(1)

    metrics_url = os.environ.get("VLLM_METRICS_URL", f"{base_url}/metrics")
    try:
        with httpx.Client(timeout=10.0) as http:
            response = http.get(metrics_url)
            response.raise_for_status()
            print(f"Metrics endpoint OK ({len(response.text)} bytes)")
    except Exception as exc:
        print(f"Metrics endpoint FAILED: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
