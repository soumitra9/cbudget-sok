"""Simple word-count tokenizer proxy until HF tokenizer is wired."""

from __future__ import annotations


def count_tokens(text: str) -> int:
    if not text.strip():
        return 0
    return len(text.split())
