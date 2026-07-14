"""Coding-repo task workspace reset and artifact collection."""

from __future__ import annotations

import json
import shutil
import subprocess
import tarfile
from dataclasses import dataclass
from pathlib import Path

from cbudget.tasks.base import TaskSpec
from cbudget.tasks.grader import GraderResult, run_grader


class InitialFailureError(RuntimeError):
    """Raised when the grader passes on the base commit (task fixture broken)."""


@dataclass
class WorkspaceManager:
    root: Path
    task: TaskSpec

    @property
    def workspace(self) -> Path:
        return self.root / "workspaces" / self.task.task_id

    @property
    def cache_dir(self) -> Path:
        return self.root / "task_caches" / self.task.task_id

    def reset(self) -> None:
        """Remove workspace and recreate empty directory."""
        if self.workspace.exists():
            shutil.rmtree(self.workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)

    def restore_dependency_cache(self) -> None:
        """Restore pre-built dep cache if present."""
        if not self.cache_dir.exists():
            return
        for item in self.cache_dir.iterdir():
            dest = self.workspace / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

    def apply_task_fixture(self) -> None:
        """Extract workspace snapshot or copy fixture directory."""
        snapshot = self.root / self.task.workspace_snapshot
        if snapshot.exists():
            with tarfile.open(snapshot, "r:gz") as archive:
                archive.extractall(self.workspace)
            self._ensure_git()
            return

        fixture = self.root / "tasks" / self.task.task_id / "fixture"
        if fixture.exists():
            for item in fixture.iterdir():
                if item.name == ".git":
                    continue
                dest = self.workspace / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
            self._ensure_git()

    def _ensure_git(self) -> None:
        if (self.workspace / ".git").exists():
            subprocess.run(
                ["git", "reset", "--hard", self.task.base_commit],
                cwd=self.workspace,
                check=False,
                capture_output=True,
            )
            subprocess.run(["git", "clean", "-xfd"], cwd=self.workspace, check=False, capture_output=True)
            return
        subprocess.run(["git", "init"], cwd=self.workspace, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "cbudget@local"], cwd=self.workspace, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "cbudget"], cwd=self.workspace, check=True, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=self.workspace, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=self.workspace, check=True, capture_output=True)
        subprocess.run(["git", "tag", "-f", self.task.base_commit], cwd=self.workspace, check=False, capture_output=True)
        subprocess.run(["git", "reset", "--hard", self.task.base_commit], cwd=self.workspace, check=False, capture_output=True)

    def verify_initial_failure(self, mock: bool = False) -> GraderResult:
        if mock:
            return GraderResult(success=False, exit_code=1, stdout="mock: initial failure verified", stderr="")
        if not self.workspace.exists():
            raise InitialFailureError(f"Workspace not provisioned for {self.task.task_id}")
        result = run_grader(self.task.grader_command, self.workspace, self.task.grader_timeout)
        if result.success:
            raise InitialFailureError(
                f"Grader passed on base commit for task {self.task.task_id}; fixture is broken."
            )
        return result

    def grade(self, mock: bool = False) -> GraderResult:
        if mock:
            return GraderResult(
                success=True,
                exit_code=0,
                stdout="mock grader: workspace not provisioned",
                stderr="",
            )
        return run_grader(self.task.grader_command, self.workspace, self.task.grader_timeout)

    def save_patch(self, run_dir: Path) -> None:
        if not (self.workspace / ".git").exists():
            return
        result = subprocess.run(
            ["git", "diff"],
            cwd=self.workspace,
            capture_output=True,
            text=True,
            check=False,
        )
        (run_dir / "workspace.patch").write_text(result.stdout, encoding="utf-8")

    def save_test_output(self, run_dir: Path, grader_result: GraderResult) -> None:
        data = {
            "exit_code": grader_result.exit_code,
            "success": grader_result.success,
            "stdout": grader_result.stdout,
            "stderr": grader_result.stderr,
        }
        (run_dir / "grader.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    def archive_workspace_metadata(self, run_dir: Path) -> None:
        meta: dict[str, object] = {"task_id": self.task.task_id, "base_commit": self.task.base_commit}
        if (self.workspace / ".git").exists():
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.workspace,
                capture_output=True,
                text=True,
                check=False,
            )
            meta["workspace_head"] = result.stdout.strip()
        (run_dir / "workspace_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    def destroy_or_reset_workspace(self) -> None:
        self.reset()
