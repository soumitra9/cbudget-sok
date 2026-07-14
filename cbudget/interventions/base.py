"""Intervention base types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ToolResult:
    output: str
    exit_code: int
    rtk_applied: bool = False
    rtk_supported: bool = False
    fallback_used: bool = False
    executed_command: str = ""


class Intervention(ABC):
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError
