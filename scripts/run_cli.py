"""Shared CLI flags for matrix runners."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAX_INFRA_RETRIES = 2
INFRA_RETRY_SLEEP_SECONDS = 30
INFRA_EXCEPTIONS = (httpx.ConnectError, httpx.RemoteProtocolError, httpx.TimeoutException, OSError)


def add_orchestration_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--no-resume", action="store_true", help="Do not skip completed runs or resume checkpoints")
    parser.add_argument("--retry-failed", action="store_true", help="Re-run failed runs (archives prior attempt)")
    parser.add_argument("--force", action="store_true", help="Re-run all cells (archives prior attempts)")
    parser.add_argument("--preflight", action="store_true", help="Validate backend before starting matrix")
    parser.add_argument("--no-preflight", action="store_true", help="Skip preflight checks")


def orchestration_kwargs(args: argparse.Namespace) -> dict:
    return {
        "resume": not args.no_resume,
        "retry_failed": args.retry_failed,
        "force": args.force,
    }


def _validate_rtk_binary() -> None:
    from cbudget.models.server_config import load_intervention

    rtk_cfg = load_intervention("rtk", "on")
    binary = rtk_cfg.get("rtk_binary", "rtk")
    if not Path(binary).is_absolute():
        binary = str(PROJECT_ROOT / binary)
    try:
        result = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=10)
    except FileNotFoundError:
        raise RuntimeError(f"RTK binary not found at {binary!r} — run pod_setup.sh first")
    if result.returncode != 0:
        raise RuntimeError(f"RTK binary at {binary!r} failed --version (exit {result.returncode}): {result.stderr.strip()}")


def _verify_hypothesis_hashes() -> None:
    hash_file = PROJECT_ROOT / "HYPOTHESIS_HASHES.txt"
    if not hash_file.exists():
        return
    for line in hash_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        expected_hash, rel_path = line.split(None, 1)
        target = PROJECT_ROOT / rel_path
        if not target.exists():
            raise RuntimeError(f"Frozen hypothesis file missing: {rel_path}")
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != expected_hash:
            raise RuntimeError(
                f"Hypothesis file modified after freeze: {rel_path}\n"
                f"  expected {expected_hash}\n"
                f"  got      {actual}"
            )


def validate_task_snapshots(task_ids: list[str]) -> None:
    from cbudget.tasks.base import TaskSpec

    missing: list[str] = []
    for task_id in task_ids:
        spec = TaskSpec.from_config(task_id)
        snapshot = PROJECT_ROOT / spec.workspace_snapshot
        if not snapshot.exists():
            missing.append(str(spec.workspace_snapshot))
    if missing:
        raise RuntimeError(
            "Missing task workspace snapshots (run scripts/build_task_snapshots.py first):\n  "
            + "\n  ".join(sorted(set(missing)))
        )


def orchestrate_run_with_infra_retry(
    orchestrate_run: Callable[..., dict[str, Any]],
    *,
    run_id: str,
    max_retries: int = MAX_INFRA_RETRIES,
    retry_sleep_seconds: int = INFRA_RETRY_SLEEP_SECONDS,
    **kwargs: Any,
) -> dict[str, Any]:
    for attempt in range(max_retries + 1):
        try:
            return orchestrate_run(**kwargs)
        except INFRA_EXCEPTIONS as exc:
            print(f"INFRA ERROR on {run_id} attempt {attempt + 1}: {exc}", flush=True)
            if attempt >= max_retries:
                print(f"Giving up on {run_id} after {max_retries} retries", flush=True)
                return {
                    "task_success": False,
                    "status": "INFRASTRUCTURE_ERROR",
                    "failure_state": "INFRASTRUCTURE_ERROR",
                    "run_id": run_id,
                }
            time.sleep(retry_sleep_seconds)
    raise RuntimeError("unreachable")


def maybe_preflight(args: argparse.Namespace, *, task_ids: list[str] | None = None) -> None:
    if args.no_preflight:
        return
    import os

    if args.preflight or os.environ.get("CBUDGET_BACKEND", "mock").lower() == "vllm":
        from cbudget.accounting.qwen_tokenizer import require_tokenizer
        from cbudget.run_resume import preflight_backend

        preflight_backend()
        require_tokenizer()
        _validate_rtk_binary()
        _verify_hypothesis_hashes()
        if task_ids:
            validate_task_snapshots(task_ids)
        print("Preflight OK (vLLM + Qwen tokenizer + RTK binary + hypothesis hashes)")
