"""RTK middleware: single execution path."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from cbudget.interventions.base import ToolResult

# Commands RTK supports via subcommand mapping (see `rtk --help`).
RTK_SUPPORTED_PREFIXES = (
    "git",
    "gh",
    "glab",
    "aws",
    "docker",
    "kubectl",
    "pytest",
    "pnpm",
    "dotnet",
    "ls",
    "find",
    "grep",
    "rg",
    "diff",
)


class RTKMode(Enum):
    OFF = "off"
    ON = "on"


@dataclass
class RTKRewriter:
    rtk_binary: str

    def rewrite(self, command: str) -> str | None:
        binary = self._resolve_binary()
        if binary is None:
            return None
        parts = command.strip().split()
        if not parts:
            return None

        quoted_binary = shlex.quote(binary)
        head = parts[0]

        if head == "git":
            return f"{quoted_binary} git {' '.join(shlex.quote(p) for p in parts[1:])}".strip()
        if head == "pytest":
            tail = " ".join(shlex.quote(p) for p in parts[1:])
            return f"{quoted_binary} test pytest {tail}".strip()
        if head == "python3" and len(parts) > 2 and parts[1] == "-m" and parts[2] == "pytest":
            tail = " ".join(shlex.quote(p) for p in parts[3:])
            return f"{quoted_binary} test pytest {tail}".strip()
        if head in RTK_SUPPORTED_PREFIXES:
            return f"{quoted_binary} {head} {' '.join(shlex.quote(p) for p in parts[1:])}".strip()

        return None

    def _resolve_binary(self) -> str | None:
        path = Path(self.rtk_binary)
        if path.exists():
            return str(path.resolve())
        return shutil.which(self.rtk_binary)


def execute_shell(
    command: str,
    treatment: RTKMode,
    rtk_binary: str = "rtk",
    cwd: Path | None = None,
    timeout: int = 300,
) -> ToolResult:
    if treatment == RTKMode.OFF:
        result = _raw_shell(command, cwd=cwd, timeout=timeout)
        return ToolResult(
            output=result.stdout + result.stderr,
            exit_code=result.returncode,
            rtk_applied=False,
            executed_command=command,
        )

    rewriter = RTKRewriter(rtk_binary=rtk_binary)
    rewritten = rewriter.rewrite(command)

    if rewritten is None:
        result = _raw_shell(command, cwd=cwd, timeout=timeout)
        return ToolResult(
            output=result.stdout + result.stderr,
            exit_code=result.returncode,
            rtk_applied=False,
            rtk_supported=False,
            fallback_used=True,
            executed_command=command,
        )

    result = _raw_shell(rewritten, cwd=cwd, timeout=timeout)
    return ToolResult(
        output=result.stdout + result.stderr,
        exit_code=result.returncode,
        rtk_applied=True,
        rtk_supported=True,
        executed_command=rewritten,
    )


def _raw_shell(command: str, cwd: Path | None = None, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if cwd is not None:
        env["PYTHONPATH"] = str(cwd)
    return subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(cwd) if cwd else None,
        env=env,
    )
