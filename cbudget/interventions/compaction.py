"""Configurable compaction policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cbudget.accounting.occupancy import count_tokens
from cbudget.agent.prompt_assembler import PromptAssembler
from cbudget.agent.state import AgentState, Message
from cbudget.models.client import ModelClient
from cbudget.tasks.fact_probes import FactSpec, run_probes


@dataclass
class CompactionConfig:
    enabled: bool = False
    trigger_tokens: int = 8192
    hot_tail_tokens: int = 2000
    max_summary_tokens: int = 1024
    temperature: float = 0.0
    recursion_enabled: bool = True
    summary_prompt: str = ""
    hard_stop: int = 16384


@dataclass
class CompactionResult:
    old_state: AgentState
    new_state: AgentState
    input_tokens: int
    output_tokens: int
    fact_probe_result: list[dict[str, Any]]


def select_hot_tail(messages: list[Message], max_tokens: int) -> list[Message]:
    tail: list[Message] = []
    used = 0
    for message in reversed(messages):
        tokens = count_tokens(message.content)
        if used + tokens > max_tokens and tail:
            break
        tail.insert(0, message)
        used += tokens
    return tail


def build_summary_prompt(task_instruction: str, task_facts: list[dict], messages: list[Message]) -> str:
    history = "\n".join(f"{m.role}: {m.content}" for m in messages)
    facts = "\n".join(f"- {f.get('id')}: {f.get('value')}" for f in task_facts)
    return (
        "Summarize the conversation for continuation.\n"
        f"Task: {task_instruction}\n"
        f"Facts:\n{facts}\n"
        f"History:\n{history}"
    )


def maybe_compact(
    state: AgentState,
    config: CompactionConfig,
    assembler: PromptAssembler,
    model: ModelClient,
    summary_prompt_prefix: str,
) -> CompactionResult | None:
    if not config.enabled:
        return None

    occupancy = count_tokens(assembler.render(state))
    if occupancy < config.trigger_tokens:
        return None

    tail = select_hot_tail(state.messages, config.hot_tail_tokens)
    tail_ids = {id(m) for m in tail}
    candidates = [m for m in state.messages if id(m) not in tail_ids]

    prompt = summary_prompt_prefix + build_summary_prompt(
        state.task_instruction,
        state.task_fact_schema,
        candidates,
    )
    result = model.generate(prompt, max_tokens=config.max_summary_tokens, temperature=config.temperature)

    new_state = AgentState(
        task_instruction=state.task_instruction,
        system_prompt=state.system_prompt,
        tool_schema=state.tool_schema,
        compacted_summary=result.text,
        messages=tail,
        task_fact_schema=state.task_fact_schema,
        turn=state.turn,
        done=state.done,
        success=state.success,
    )

    fact_schema: list[FactSpec] = state.task_fact_schema  # type: ignore[assignment]
    probe_results = run_probes(fact_schema, result.text)

    return CompactionResult(
        old_state=state,
        new_state=new_state,
        input_tokens=count_tokens(prompt),
        output_tokens=result.generated_tokens,
        fact_probe_result=probe_results,
    )
