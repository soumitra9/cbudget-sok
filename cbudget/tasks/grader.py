"""Task grader execution."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GraderResult:
    success: bool
    exit_code: int
    stdout: str
    stderr: str


def run_grader(command: str, workspace: Path, timeout_seconds: int = 300) -> GraderResult:
    try:
        env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
        env["PYTHONPATH"] = str(workspace)
        completed = subprocess.run(
            command,
            shell=True,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=env,
        )
        return GraderResult(
            success=completed.returncode == 0,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return GraderResult(success=False, exit_code=124, stdout=stdout, stderr=stderr)
