"""Run manifest: provenance and config hashing."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def _git_sha() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


@dataclass
class RunManifest:
    run_id: str
    experiment_id: str
    task_id: str
    seed: int
    treatment: dict[str, Any]
    config_hashes: dict[str, str | None] = field(default_factory=dict)
    git_sha: str | None = field(default_factory=_git_sha)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    backend: str = "mock"
    status: str = "CREATED"

    def add_config_hash(self, name: str, path: Path) -> None:
        self.config_hashes[name] = _sha256_file(path)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
