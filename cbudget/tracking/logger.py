"""Append-only JSONL event logger."""

from __future__ import annotations

import json
from pathlib import Path

from cbudget.tracking.events import Event


class EventLogger:
    def __init__(self, run_dir: Path, run_id: str) -> None:
        self.run_dir = run_dir
        self.run_id = run_id
        self._next_id = 1
        self.events_path = run_dir / "events.jsonl"
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def emit(self, event_type: str, payload: dict | None = None) -> Event:
        event = Event(
            run_id=self.run_id,
            event_id=self._next_id,
            event_type=event_type,
            payload=payload or {},
        )
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict()) + "\n")
        self._next_id += 1
        return event
