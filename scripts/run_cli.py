"""Shared CLI flags for matrix runners."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


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


def maybe_preflight(args: argparse.Namespace) -> None:
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
        print("Preflight OK (vLLM + Qwen tokenizer + RTK binary + hypothesis hashes)")
