"""vLLM /metrics scrape-before/after delta collector."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class VllmMetricsSnapshot:
    prefix_hit_tokens: int = 0
    prefix_miss_tokens: int = 0
    prefill_latency_ms: float = 0.0
    ttft_ms: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class VllmMetricsDelta:
    before: VllmMetricsSnapshot
    after: VllmMetricsSnapshot
    valid: bool = True

    def delta_prefix_hits(self) -> int:
        return self.after.prefix_hit_tokens - self.before.prefix_hit_tokens


def parse_prom_metrics(text: str) -> dict[str, float]:
    values: dict[str, float] = {}
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 2:
            try:
                values[parts[0]] = float(parts[-1])
            except ValueError:
                continue
    return values


def snapshot_from_prom(text: str) -> VllmMetricsSnapshot:
    values = parse_prom_metrics(text)
    hit = 0
    miss = 0
    for key, val in values.items():
        if "prefix_cache" in key and "hit" in key:
            hit += int(val)
        if "prefix_cache" in key and "miss" in key:
            miss += int(val)
    return VllmMetricsSnapshot(prefix_hit_tokens=hit, prefix_miss_tokens=miss, raw=values)


@dataclass
class VLLMMetricsCollector:
    metrics_url: str

    def scrape(self) -> str:
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(self.metrics_url)
                response.raise_for_status()
                return response.text
        except Exception:
            return ""

    def delta(self, before_text: str, after_text: str) -> VllmMetricsDelta:
        before = snapshot_from_prom(before_text)
        after = snapshot_from_prom(after_text)
        valid = bool(before_text and after_text)
        return VllmMetricsDelta(before=before, after=after, valid=valid)
