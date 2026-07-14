"""Protocol-neutral agent loop."""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cbudget.accounting.occupancy import count_tokens
from cbudget.accounting.token_accounting import TokenAccounting
from cbudget.accounting.vllm_metrics import VLLMMetricsCollector
from cbudget.agent.prompt_assembler import PromptAssembler
from cbudget.agent.state import AgentState, Message
from cbudget.agents.chain_of_draft import ChainOfDraftPolicy
from cbudget.agents.react import ReactPolicy
from cbudget.interventions.compaction import CompactionConfig, maybe_compact
from cbudget.interventions.rtk import RTKMode, execute_shell
from cbudget.models.client import ModelClient
from cbudget.models.server_config import load_model_config
from cbudget.run_resume import clear_checkpoint, restore_agent_state, save_checkpoint
from cbudget.state_machine import FailureState, RunState, StateMachine
from cbudget.tasks.base import TaskSpec
from cbudget.tasks.coding_repo import InitialFailureError, WorkspaceManager
from cbudget.tasks.fact_probes import load_fact_schema
from cbudget.tasks.grader import run_grader
from cbudget.tracking.events import prompt_hash
from cbudget.tracking.logger import EventLogger
from cbudget.tracking.manifest import RunManifest


@dataclass
class RunConfig:
    experiment_id: str
    run_id: str
    task_id: str
    seed: int
    treatment: dict[str, Any]
    run_dir: Path
    project_root: Path
    resume_checkpoint: dict[str, Any] | None = None


class AgentLoop:
    def __init__(
        self,
        run_config: RunConfig,
        task: TaskSpec,
        state_machine: StateMachine | None = None,
    ) -> None:
        self.run_config = run_config
        self.task = task
        self.sm = state_machine or StateMachine(run_id=run_config.run_id)
        self.logger = EventLogger(run_config.run_dir, run_config.run_id)
        self.accounting = TokenAccounting()
        self.assembler = PromptAssembler()
        self.model_cfg = load_model_config()
        self.use_mock = os.environ.get("CBUDGET_BACKEND", "mock").lower() == "mock"
        self.model = ModelClient(seed=run_config.seed, use_mock=self.use_mock)
        self.workspace = WorkspaceManager(run_config.project_root, task)
        self.metrics = VLLMMetricsCollector(os.environ.get("VLLM_METRICS_URL", "http://localhost:8000/metrics"))
        reasoning = run_config.treatment.get("reasoning", "standard")
        policy_cfg = run_config.treatment.get("policy_config", {})
        self.policy = ChainOfDraftPolicy(policy_cfg) if reasoning == "cod" else ReactPolicy(policy_cfg)
        self.rtk_mode = RTKMode.ON if run_config.treatment.get("rtk") == "on" else RTKMode.OFF
        self.compaction = CompactionConfig(
            enabled=run_config.treatment.get("compaction") not in (None, "off", False),
            trigger_tokens=int(
                run_config.treatment.get("compaction_trigger")
                or self.model_cfg.get("calibration_starting_values", {}).get("compaction_trigger", 8192)
            ),
            hot_tail_tokens=int(run_config.treatment.get("hot_tail_tokens", 2000)),
            max_summary_tokens=int(run_config.treatment.get("max_summary_tokens", 1024)),
            temperature=float(run_config.treatment.get("compaction_temperature", 0.0)),
            recursion_enabled=bool(run_config.treatment.get("recursion_enabled", True)),
            summary_prompt=run_config.treatment.get("summary_prompt", ""),
            hard_stop=int(
                run_config.treatment.get("hard_stop")
                or self.model_cfg.get("calibration_starting_values", {}).get("hard_stop", 16384)
            ),
        )
        self.start_time = time.monotonic()
        self.fact_schema = []
        if task.fact_schema:
            self.fact_schema = load_fact_schema(run_config.project_root / task.fact_schema)

    def _wall_time_exceeded(self) -> bool:
        return (time.monotonic() - self.start_time) >= self.task.max_wall_time_seconds

    def _check_context_limit(self, occupancy: int) -> bool:
        if occupancy >= self.compaction.hard_stop:
            self.logger.emit("run_failed", self.sm.fail(FailureState.CONTEXT_EXHAUSTED))
            return True
        return False

    def run(self) -> dict[str, Any]:
        manifest = RunManifest(
            run_id=self.run_config.run_id,
            experiment_id=self.run_config.experiment_id,
            task_id=self.task.task_id,
            seed=self.run_config.seed,
            treatment=self.run_config.treatment,
            backend="mock" if self.use_mock else "vllm",
        )
        manifest.write(self.run_config.run_dir / "manifest.json")
        self.logger.emit("run_started", {"task_id": self.task.task_id, "seed": self.run_config.seed})

        checkpoint = self.run_config.resume_checkpoint
        if checkpoint:
            state = restore_agent_state(checkpoint)
            sm_data = checkpoint.get("state_machine", {})
            self.sm.state = RunState(sm_data.get("state", RunState.RUNNING.value))
            self.sm.failure_state = None
            self.sm.transitions = list(sm_data.get("transitions", []))
            model_calls = int(checkpoint.get("model_calls", 0))
            acct = checkpoint.get("accounting", {})
            self.accounting.cumulative_serialized_pt = int(acct.get("total_serialized_pt", 0))
            self.accounting.cumulative_gt = int(acct.get("total_gt", 0))
            self.accounting.cumulative_compaction_gt = int(acct.get("total_compaction_gt", 0))
            self.accounting.peak_occupancy = int(acct.get("peak_occupancy", 0))
            run_failed = False
        else:
            self.sm.transition(RunState.ENVIRONMENT_RESET)
            self.workspace.reset()
            self.workspace.restore_dependency_cache()
            self.workspace.apply_task_fixture()

            if not self.use_mock:
                self.sm.transition(RunState.MODEL_READY)
                metrics_before = self.metrics.scrape()
                (self.run_config.run_dir / "vllm_metrics_before.prom").write_text(metrics_before, encoding="utf-8")
                self.model.generate("warmup", max_tokens=1, temperature=0.0)

            self.sm.transition(RunState.TASK_INITIALIZED)
            try:
                self.workspace.verify_initial_failure(mock=self.use_mock)
            except InitialFailureError as exc:
                payload = self.sm.fail(FailureState.TOOL_RUNNER_FAILURE, str(exc))
                self.logger.emit("run_failed", payload)
                return {"status": FailureState.TOOL_RUNNER_FAILURE.value, "task_success": False, **self.accounting.summary()}

            self.sm.transition(RunState.ACCOUNTING_VERIFIED)
            base_system = "You are a coding agent with shell access."
            state = AgentState(
                task_instruction=self.task.read_instruction(self.run_config.project_root),
                system_prompt=self.policy.system_prompt(base_system),
                tool_schema='{"tools":[{"name":"shell"}]}',
                task_fact_schema=[f.__dict__ for f in self.fact_schema],
            )

            self.sm.transition(RunState.RUNNING)
            model_calls = 0
            run_failed = False

        while model_calls < self.task.max_model_calls and state.turn < self.task.max_agent_turns:
            if self._wall_time_exceeded():
                self.logger.emit("run_failed", self.sm.fail(FailureState.TIMEOUT))
                run_failed = True
                break

            prompt = self.assembler.render(state)
            prompt_tokens = count_tokens(prompt)
            occupancy = prompt_tokens

            if self._check_context_limit(occupancy):
                run_failed = True
                break

            self.logger.emit(
                "model_request",
                {
                    "turn": state.turn,
                    "prompt_hash": prompt_hash(prompt),
                    "prompt_tokens_serialized": prompt_tokens,
                    "occupancy": occupancy,
                    "regions": self.assembler.regions(state),
                    "treatment": {
                        "rtk": self.run_config.treatment.get("rtk") == "on",
                        "compaction": self.compaction.enabled,
                        "reasoning": self.run_config.treatment.get("reasoning", "standard"),
                    },
                    "model": {
                        "repository": self.model_cfg.get("repository", ""),
                        "revision": self.model_cfg.get("revision"),
                        "seed": self.run_config.seed,
                    },
                },
            )
            (self.run_config.run_dir / "prompts").mkdir(exist_ok=True)
            (self.run_config.run_dir / "prompts" / f"turn_{state.turn:03d}.txt").write_text(prompt, encoding="utf-8")

            gen_cfg = self.model_cfg.get("generation", {})
            try:
                response = self.model.generate(
                    prompt,
                    max_tokens=int(gen_cfg.get("max_tokens", 2048)),
                    temperature=float(gen_cfg.get("temperature", 0.2)),
                    messages=self.assembler.to_chat_messages(state),
                )
            except Exception as exc:
                self.logger.emit("run_failed", self.sm.fail(FailureState.MODEL_ERROR, str(exc)))
                run_failed = True
                break

            model_calls += 1
            self.accounting.record_turn(prompt_tokens, response.generated_tokens)
            self.logger.emit(
                "model_response",
                {
                    "turn": state.turn,
                    "generated_tokens": response.generated_tokens,
                    "finish_reason": response.finish_reason,
                },
            )

            parsed = self.policy.parse_response(response.text, state)
            state.messages.append(Message(role="assistant", content=response.text))

            if parsed.get("action") == "tool":
                command = parsed.get("command", "")
                if "shell" not in self.task.allowed_tools:
                    self.logger.emit("run_failed", self.sm.fail(FailureState.TOOL_COMMAND_INVALID, "shell not allowed"))
                    run_failed = True
                    break
                self.logger.emit("tool_request", {"turn": state.turn, "original_command": command})
                try:
                    tool_result = execute_shell(
                        command,
                        self.rtk_mode,
                        rtk_binary=self.run_config.treatment.get("rtk_binary", "rtk"),
                        cwd=self.workspace.workspace,
                        timeout=min(300, self.task.max_wall_time_seconds),
                    )
                except subprocess.TimeoutExpired:
                    self.logger.emit("run_failed", self.sm.fail(FailureState.TOOL_TIMEOUT))
                    run_failed = True
                    break

                self.logger.emit(
                    "tool_result",
                    {
                        "turn": state.turn,
                        "original_command": command,
                        "executed_command": tool_result.executed_command or command,
                        "rtk_supported": tool_result.rtk_supported,
                        "fallback_used": tool_result.fallback_used,
                        "exit_code": tool_result.exit_code,
                        "output_tokens": count_tokens(tool_result.output),
                    },
                )
                state.messages.append(Message(role="tool", content=tool_result.output))
            elif parsed.get("action") == "final":
                state.done = True
                break
            else:
                self.logger.emit("run_failed", self.sm.fail(FailureState.PARSER_ERROR))
                run_failed = True
                break

            while True:
                compact_result = maybe_compact(
                    state,
                    self.compaction,
                    self.assembler,
                    self.model,
                    self.compaction.summary_prompt,
                )
                if compact_result is None:
                    break
                self.logger.emit("compaction_started", {"turn": state.turn})
                self.logger.emit(
                    "compaction_call",
                    {
                        "turn": state.turn,
                        "prompt_tokens": compact_result.input_tokens,
                        "generated_tokens": compact_result.output_tokens,
                        "cost_usd_simulated": 0.0,
                    },
                )
                self.accounting.record_compaction(compact_result.output_tokens)
                self.logger.emit(
                    "compaction_completed",
                    {
                        "turn": state.turn,
                        "input_tokens": compact_result.input_tokens,
                        "output_tokens": compact_result.output_tokens,
                        "fact_probe_result": compact_result.fact_probe_result,
                    },
                )
                state = compact_result.new_state
                if not self.compaction.recursion_enabled:
                    break
                if count_tokens(self.assembler.render(state)) < self.compaction.trigger_tokens:
                    break

            state.turn += 1
            save_checkpoint(
                self.run_config.run_dir,
                state=state,
                state_machine=self.sm,
                accounting_summary=self.accounting.summary(),
                model_calls=model_calls,
            )

        self.sm.transition(RunState.GRADING)
        grader_result = self.workspace.grade(mock=self.use_mock)
        self.logger.emit(
            "grader_result",
            {
                "success": grader_result.success,
                "exit_code": grader_result.exit_code,
                "stdout_tail": grader_result.stdout[-500:],
            },
        )

        self.sm.transition(RunState.ARTIFACT_COLLECTION)
        self.workspace.save_patch(self.run_config.run_dir)
        self.workspace.save_test_output(self.run_config.run_dir, grader_result)
        self.workspace.archive_workspace_metadata(self.run_config.run_dir)
        self.workspace.destroy_or_reset_workspace()

        if not self.use_mock:
            metrics_after = self.metrics.scrape()
            (self.run_config.run_dir / "vllm_metrics_after.prom").write_text(metrics_after, encoding="utf-8")

        summary = self.accounting.summary()
        status = {
            "status": RunState.COMPLETED.value if not run_failed else self.sm.failure_state.value if self.sm.failure_state else "FAILED",
            "task_success": grader_result.success and not run_failed,
            "state_machine": self.sm.to_status(),
            **summary,
        }
        (self.run_config.run_dir / "status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
        if not run_failed:
            self.sm.transition(RunState.COMPLETED)
            clear_checkpoint(self.run_config.run_dir)
        self.logger.emit("run_completed", status)
        return status
