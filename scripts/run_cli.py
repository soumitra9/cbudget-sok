"""Shared CLI flags for matrix runners."""

from __future__ import annotations

import argparse


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


def maybe_preflight(args: argparse.Namespace) -> None:
    if args.no_preflight:
        return
    import os

    if args.preflight or os.environ.get("CBUDGET_BACKEND", "mock").lower() == "vllm":
        from cbudget.accounting.qwen_tokenizer import require_tokenizer

        preflight_backend()
        require_tokenizer()
        print("Preflight OK (vLLM + Qwen tokenizer)")
