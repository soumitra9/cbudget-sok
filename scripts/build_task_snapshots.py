"""Build workspace snapshot tarballs from task fixture directories."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tarfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TASKS_ROOT = PROJECT_ROOT / "tasks"


def build_snapshot(task_id: str) -> Path:
    fixture = TASKS_ROOT / task_id / "fixture"
    if not fixture.exists():
        raise FileNotFoundError(f"Missing fixture: {fixture}")

    snapshot_path = TASKS_ROOT / task_id / "snapshot.tar.gz"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)

    if (fixture / ".git").exists():
        subprocess.run(["git", "add", "-A"], cwd=fixture, check=False, capture_output=True)
        subprocess.run(["git", "commit", "-m", "snapshot", "--allow-empty"], cwd=fixture, check=False, capture_output=True)

    with tarfile.open(snapshot_path, "w:gz") as archive:
        for item in fixture.rglob("*"):
            if item.is_file() and ".git" not in item.parts:
                archive.add(item, arcname=item.relative_to(fixture))

    return snapshot_path


def init_git_fixture(task_id: str, base_commit: str) -> None:
    fixture = TASKS_ROOT / task_id / "fixture"
    if not fixture.exists():
        return
    if not (fixture / ".git").exists():
        subprocess.run(["git", "init"], cwd=fixture, check=True, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=fixture, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=fixture, check=True, capture_output=True)
    subprocess.run(["git", "tag", "-f", base_commit], cwd=fixture, check=False, capture_output=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", action="append", default=[], help="Task ID (repeatable)")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    task_ids = args.task
    if args.all:
        task_ids = [p.name for p in TASKS_ROOT.iterdir() if p.is_dir() and (p / "fixture").exists()]

    for task_id in task_ids:
        init_git_fixture(task_id, "base")
        path = build_snapshot(task_id)
        print(f"Built {path}")


if __name__ == "__main__":
    main()
