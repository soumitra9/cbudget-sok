"""Segment provenance tracking."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SegmentProvenance:
    segment_id: str
    source: str
    retained: bool = True
    compacted_away: bool = False
    tags: list[str] = field(default_factory=list)
