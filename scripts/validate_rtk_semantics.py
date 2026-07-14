"""RTK paired-workspace semantic validation."""

from __future__ import annotations

import argparse
import shutil
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path

from cbudget.interventions.rtk import RTKMode, execute_shell

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class PairedResult:
    command: str
    raw_exit: int
    rtk_exit: int
    rtk_fallback: bool
    exit_code_match: bool
    content_ok: bool
    notes: str = ""


# (command, required_fragment, expect_rtk_support)
VALIDATION_SUITE: list[tuple[str, str, bool]] = [
    ("git --version", "git version", True),
    ("pytest --version", "pytest", True),
    ("echo hello", "hello", False),
    ("this_command_does_not_exist_zzz", "", False),
]


def provision_workspace(template_task: str = "repo_task_cal_001") -> Path:
    snapshot = PROJECT_ROOT / "tasks" / template_task / "snapshot.tar.gz"
    workspace = Path(tempfile.mkdtemp(prefix="rtk_val_"))
    if snapshot.exists():
        with tarfile.open(snapshot, "r:gz") as archive:
            archive.extractall(workspace, filter="data")
    return workspace


def run_paired(command: str, required_fragment: str, expect_support: bool, rtk_bin: str) -> PairedResult:
    ws_a = provision_workspace()
    ws_b = provision_workspace()
    try:
        raw_result = execute_shell(command, RTKMode.OFF, rtk_binary=rtk_bin, cwd=ws_a)
        rtk_result = execute_shell(command, RTKMode.ON, rtk_binary=rtk_bin, cwd=ws_b)
    finally:
        shutil.rmtree(ws_a, ignore_errors=True)
        shutil.rmtree(ws_b, ignore_errors=True)

    if expect_support:
        match = raw_result.exit_code == rtk_result.exit_code
    else:
        # Unsupported commands must fall back with identical behavior.
        match = raw_result.exit_code == rtk_result.exit_code and rtk_result.fallback_used

    content_ok = True
    if required_fragment:
        content_ok = required_fragment in (rtk_result.output if expect_support else raw_result.output)

    notes = ""
    if not match:
        notes = f"raw={raw_result.exit_code} rtk={rtk_result.exit_code} fallback={rtk_result.fallback_used}"

    return PairedResult(
        command=command,
        raw_exit=raw_result.exit_code,
        rtk_exit=rtk_result.exit_code,
        rtk_fallback=rtk_result.fallback_used,
        exit_code_match=match,
        content_ok=content_ok,
        notes=notes,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="RTK paired-workspace semantic validation.")
    parser.add_argument("--rtk-bin", default=str(PROJECT_ROOT / "external/rtk/target/release/rtk"))
    args = parser.parse_args()

    passed = 0
    failed = 0
    for command, fragment, expect_support in VALIDATION_SUITE:
        result = run_paired(command, fragment, expect_support, args.rtk_bin)
        ok = result.exit_code_match and result.content_ok
        status = "PASS" if ok else "FAIL"
        fallback_tag = " [fallback]" if result.rtk_fallback else ""
        print(f"[{status}]{fallback_tag} {command!r:50s} raw={result.raw_exit} rtk={result.rtk_exit} {result.notes}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n{passed}/{passed + failed} commands passed.")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
