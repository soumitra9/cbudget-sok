"""Stage 2 GPU integration checklist (RunPod A40 + vLLM)."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_step(label: str, cmd: list[str]) -> bool:
    print(f"\n== {label} ==")
    print("$", " ".join(cmd))
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 2 GPU integration validation.")
    parser.add_argument("--skip-provision", action="store_true", help="Skip RunPod MCP provisioning notes")
    args = parser.parse_args()

    if not args.skip_provision:
        print("RunPod provisioning (via MCP): create-pod/start-pod with A40, then bootstrap.sh <POD_IP>")
        print("Requires valid RUNPOD_API_KEY in MCP server configuration.")

    os.environ.setdefault("CBUDGET_BACKEND", "vllm")
    os.environ.setdefault("VLLM_BASE_URL", "http://localhost:8000")

    steps = [
        ("validate_environment", [sys.executable, "-m", "scripts.validate_environment", "--config", "configs/environment/runpod_a40.yaml"]),
        ("validate_accounting", [sys.executable, "-m", "scripts.validate_accounting", "--config", "configs/validation/accounting.yaml"]),
        ("validate_cache", [sys.executable, "-m", "scripts.validate_cache", "--server", os.environ["VLLM_BASE_URL"]]),
        ("validate_rtk", [sys.executable, "-m", "scripts.validate_rtk_semantics"]),
    ]

    failed = [label for label, cmd in steps if not run_step(label, ["uv", "run", *cmd[1:]])]
    if failed:
        print(f"\nStage 2 FAILED steps: {failed}")
        print("If vLLM is not running, start launch_vllm.sh on the pod and port-forward :8000.")
        raise SystemExit(1)

    print("\nStage 2 GPU integration checks passed.")


if __name__ == "__main__":
    main()
