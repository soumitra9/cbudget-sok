"""Lazy Qwen2.5 tokenizer for occupancy accounting."""

from __future__ import annotations

import os
from functools import lru_cache

from cbudget.models.server_config import load_model_config


@lru_cache(maxsize=1)
def get_tokenizer():
    cfg = load_model_config()
    repo = cfg.get("repository", "Qwen/Qwen2.5-7B-Instruct")
    revision = cfg.get("tokenizer_revision") or cfg.get("revision")
    from transformers import AutoTokenizer

    kwargs = {"trust_remote_code": False}
    if revision:
        kwargs["revision"] = revision
    return AutoTokenizer.from_pretrained(repo, **kwargs)


def encode_len(text: str) -> int:
    if not text.strip():
        return 0
    return len(get_tokenizer().encode(text, add_special_tokens=False))


def require_tokenizer() -> None:
    """Fail fast before GPU runs if transformers is not installed."""
    get_tokenizer()
