"""Token counting for occupancy and compaction triggers."""

from __future__ import annotations

import os

from cbudget.accounting.qwen_tokenizer import encode_len


def count_tokens(text: str) -> int:
    if os.environ.get("CBUDGET_TOKEN_COUNT", "").lower() == "words":
        return len(text.split()) if text.strip() else 0
    return encode_len(text)
