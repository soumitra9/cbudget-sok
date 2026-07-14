"""Run skip/resume helpers for fault-tolerant matrix execution."""

from __future__ import annotations

import json
import os
import shutil
from enum import Enum
from pathlib import Path
from typing import Any

import httpx

from cbudget.agent.state import AgentState, Message
from cbudget.state_machine import RunState, StateMachine


class RunDisposition(str, Enum):
    SKIP = "skip"
    RESUME = "resume"
    FRESH = "fresh"


def preflight_vllm(base_url: str | None = None) -> None:
    url = base_url or os.environ.get("VLLM_BASE_URL", "http://localhost:8000")
    with httpx.Client(timeout=15.0) as client:
        response = client.get(f"{url.rstrip('/')}/v1/models")
        response.raise_for_status()


def preflight_backend() -> None:
    backend = os.environ.get("CBUDGET_BACKEND", "mock").lower()
    if backend == "vllm":
        preflight_vllm()


def load_status(run_dir: Path) -> dict[str, Any] | None:
    path = run_dir / "status.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_disposition(
    run_dir: Path,
    *,
    resume: bool = True,
    retry_failed: bool = False,
    force: bool = False,
) -> RunDisposition:
    if force:
        return RunDisposition.FRESH

    status = load_status(run_dir)
    checkpoint = run_dir / "checkpoint.json"

    if resume and status and status.get("task_success"):
        return RunDisposition.SKIP

    if resume and checkpoint.exists():
        data = json.loads(checkpoint.read_text(encoding="utf-8"))
        if data.get("state_machine", {}).get("state") == RunState.RUNNING.value:
            return RunDisposition.RESUME

    if retry_failed and status and not status.get("task_success"):
        return RunDisposition.FRESH

    if status is not None:
        return RunDisposition.SKIP

    return RunDisposition.FRESH


def archive_run_dir(run_dir: Path) -> None:
    if not run_dir.exists():
        return
    attempt = 1
    while True:
        dest = run_dir.parent / f"{run_dir.name}.attempt{attempt:02d}"
        if not dest.exists():
            shutil.move(str(run_dir), str(dest))
            return
        attempt += 1


def save_checkpoint(
    run_dir: Path,
    *,
    state: AgentState,
    state_machine: StateMachine,
    accounting_summary: dict[str, Any],
    model_calls: int,
) -> None:
    payload = {
        "turn": state.turn,
        "model_calls": model_calls,
        "state": {
            "task_instruction": state.task_instruction,
            "system_prompt": state.system_prompt,
            "tool_schema": state.tool_schema,
            "messages": [{"role": m.role, "content": m.content} for m in state.messages],
            "compacted_summary": state.compacted_summary,
            "task_fact_schema": state.task_fact_schema,
            "turn": state.turn,
            "done": state.done,
            "success": state.success,
        },
        "state_machine": state_machine.to_status(),
        "accounting": accounting_summary,
    }
    (run_dir / "checkpoint.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_checkpoint(run_dir: Path) -> dict[str, Any] | None:
    path = run_dir / "checkpoint.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def restore_agent_state(data: dict[str, Any]) -> AgentState:
    raw = data["state"]
    return AgentState(
        task_instruction=raw["task_instruction"],
        system_prompt=raw["system_prompt"],
        tool_schema=raw["tool_schema"],
        messages=[Message(role=m["role"], content=m["content"]) for m in raw.get("messages", [])],
        compacted_summary=raw.get("compacted_summary"),
        task_fact_schema=raw.get("task_fact_schema", []),
        turn=int(raw.get("turn", 0)),
        done=bool(raw.get("done", False)),
        success=raw.get("success"),
    )


def clear_checkpoint(run_dir: Path) -> None:
    path = run_dir / "checkpoint.json"
    if path.exists():
        path.unlink()
