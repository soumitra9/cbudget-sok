"""theta -> token-count cost model per channel.

This is intentionally the first thing you should replace with something
measured rather than assumed: run a small pilot (e.g., 50 BFCL multi_turn
tasks) computing ACTUAL token counts for a few theta values per channel with
a real tokenizer, then fit a simple monotonic curve (piecewise-linear is
fine to start) instead of the placeholder linear model below.

For channel R specifically: calibrate against Extra-CoT (arXiv:2602.08324)
or CtrlCoT's reported accuracy-vs-ratio curves, not TokenSkip's -- TokenSkip
is the historically-first method here but is now beaten at every reported
compression ratio by both, and collapses sharply (>20-point accuracy drops)
at aggressive ratios in third-party comparisons. Using TokenSkip's curve
shape would understate how much R can realistically be compressed before
hitting a real accuracy cliff.

The placeholder assumes cost is linear in theta and proportional to the
"full" (uncompressed) token count of that channel's raw content, which is
almost certainly wrong for S and H (schema compression and summarization
are not linear operations) but is a reasonable placeholder to get the
allocation loop running end-to-end before investing in real measurement.
"""
from __future__ import annotations

from allocators.types import Channel, TaskInstance

# Rough chars-per-token constant for a placeholder estimate; replace with a
# real tokenizer call (tiktoken / the target model's tokenizer) before
# reporting any numbers.
CHARS_PER_TOKEN = 4


def _raw_channel_chars(channel: Channel, task: TaskInstance) -> int:
    if channel == Channel.TOOL_SCHEMA:
        return sum(len(str(t)) for t in task.available_tools)
    if channel == Channel.HISTORY:
        return sum(len(str(h)) for h in task.history)
    if channel == Channel.REASONING:
        # No "raw" reasoning exists yet at allocation time; use a rough
        # per-difficulty proxy for the UNCOMPRESSED reasoning-token budget
        # a model would spend on a task of this difficulty. This constant
        # needs calibration against real model traces -- placeholder only.
        base_reasoning_tokens = 500
        difficulty_multiplier = 1 + (task.difficulty_proxy or 0) * 0.5
        return int(base_reasoning_tokens * difficulty_multiplier * CHARS_PER_TOKEN)
    raise ValueError(channel)


def linear_cost_model(channel: Channel, theta: float, task: TaskInstance) -> int:
    """tokens(theta) = theta * full_channel_tokens. See module docstring:
    replace before trusting any downstream numbers."""
    raw_chars = _raw_channel_chars(channel, task)
    full_tokens = raw_chars // CHARS_PER_TOKEN
    return int(theta * full_tokens)
