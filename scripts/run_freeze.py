"""Stage 4 freeze: hash hypotheses and write frozen config snapshot."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FREEZE_DIR = PROJECT_ROOT / "results" / "freeze"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    FREEZE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()

    hashes = {}
    for rel in ("configs/hypotheses/e1_frozen.yaml", "configs/hypotheses/e1b_frozen.yaml"):
        path = PROJECT_ROOT / rel
        hashes[rel] = sha256(path)

    (PROJECT_ROOT / "HYPOTHESIS_HASHES.txt").write_text(
        "\n".join(f"{h}  {p}" for p, h in hashes.items()) + "\n",
        encoding="utf-8",
    )

    manifest = {
        "frozen_at": timestamp,
        "hypothesis_hashes": hashes,
        "model_config": "configs/models/qwen2.5_7b_instruct.yaml",
        "task_sets": ["coding_calibration_v1", "coding_confirmatory_v1"],
        "seeds": "configs/seeds/seeds_confirmatory_v1.yaml",
    }
    (FREEZE_DIR / "freeze_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    for rel in (
        "configs/hypotheses/e1_frozen.yaml",
        "configs/hypotheses/e1b_frozen.yaml",
        "configs/models/qwen2.5_7b_instruct.yaml",
        "configs/tasks/coding_confirmatory_v1.yaml",
        "configs/seeds/seeds_confirmatory_v1.yaml",
    ):
        src = PROJECT_ROOT / rel
        if src.exists():
            dest = FREEZE_DIR / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)

    print(f"Freeze complete: {FREEZE_DIR}")


if __name__ == "__main__":
    main()
