"""Token accounting: PT_serialized, GT, PO."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TokenAccounting:
    cumulative_serialized_pt: int = 0
    cumulative_gt: int = 0
    cumulative_compaction_gt: int = 0
    peak_occupancy: int = 0
    per_turn_pt: list[int] = field(default_factory=list)
    per_turn_gt: list[int] = field(default_factory=list)

    def record_turn(self, prompt_tokens: int, generated_tokens: int) -> None:
        self.cumulative_serialized_pt += prompt_tokens
        self.cumulative_gt += generated_tokens
        self.peak_occupancy = max(self.peak_occupancy, prompt_tokens)
        self.per_turn_pt.append(prompt_tokens)
        self.per_turn_gt.append(generated_tokens)

    def record_compaction(self, generated_tokens: int) -> None:
        self.cumulative_compaction_gt += generated_tokens
        self.cumulative_gt += generated_tokens

    def net_pt_savings(self, baseline_pt: int) -> int:
        return baseline_pt - self.cumulative_serialized_pt - self.cumulative_compaction_gt

    def summary(self) -> dict[str, int]:
        return {
            "total_serialized_pt": self.cumulative_serialized_pt,
            "total_gt": self.cumulative_gt,
            "total_compaction_gt": self.cumulative_compaction_gt,
            "peak_occupancy": self.peak_occupancy,
        }
