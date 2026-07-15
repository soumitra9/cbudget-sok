"""Debug turn-0 model response and parsing on live vLLM."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cbudget.agent.prompt_assembler import PromptAssembler
from cbudget.agent.state import AgentState
from cbudget.agents.react import ReactPolicy
from cbudget.models.client import ModelClient
from cbudget.tasks.base import TaskSpec


def main() -> None:
    task_id = sys.argv[1] if len(sys.argv) > 1 else "repo_task_cal_001"
    task = TaskSpec.from_config(task_id)
    base = (
        "You are a coding agent with non-interactive shell access. "
        "The environment has no TTY; use sed, heredocs, or python for file edits."
    )
    policy = ReactPolicy()
    state = AgentState(
        task_instruction=task.read_instruction(PROJECT_ROOT),
        system_prompt=policy.system_prompt(base),
        tool_schema='{"tools":[{"name":"shell"}]}',
    )
    assembler = PromptAssembler()
    messages = assembler.to_chat_messages(state)
    print("=== CHAT MESSAGES ===")
    for m in messages:
        print(f"[{m['role']}] {m['content'][:200]}...")
    print()

    client = ModelClient(
        base_url=os.environ.get("VLLM_BASE_URL", "http://127.0.0.1:8000"),
        use_mock=False,
    )
    resp = client.generate("", messages=messages, max_tokens=2048, temperature=0.2)
    print("=== RAW RESPONSE ===")
    print(repr(resp.text))
    print()
    print("=== PARSE ===")
    print(policy.parse_response(resp.text, state))


if __name__ == "__main__":
    main()
