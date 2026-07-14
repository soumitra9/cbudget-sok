"""Run lifecycle state machine with failure taxonomy and retry rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RunState(str, Enum):
    CREATED = "CREATED"
    ENVIRONMENT_RESET = "ENVIRONMENT_RESET"
    MODEL_READY = "MODEL_READY"
    TASK_INITIALIZED = "TASK_INITIALIZED"
    ACCOUNTING_VERIFIED = "ACCOUNTING_VERIFIED"
    RUNNING = "RUNNING"
    GRADING = "GRADING"
    ARTIFACT_COLLECTION = "ARTIFACT_COLLECTION"
    COMPLETED = "COMPLETED"


class FailureState(str, Enum):
    MODEL_ERROR = "MODEL_ERROR"
    TOOL_COMMAND_NONZERO = "TOOL_COMMAND_NONZERO"
    TOOL_COMMAND_INVALID = "TOOL_COMMAND_INVALID"
    TOOL_TIMEOUT = "TOOL_TIMEOUT"
    TOOL_RUNNER_FAILURE = "TOOL_RUNNER_FAILURE"
    PARSER_ERROR = "PARSER_ERROR"
    CONTEXT_EXHAUSTED = "CONTEXT_EXHAUSTED"
    TIMEOUT = "TIMEOUT"
    GRADER_ERROR = "GRADER_ERROR"
    COMPACTION_ENDPOINT_ERROR = "COMPACTION_ENDPOINT_ERROR"
    COMPACTION_PARSE_ERROR = "COMPACTION_PARSE_ERROR"
    COMPACTION_LENGTH_VIOLATION = "COMPACTION_LENGTH_VIOLATION"
    COMPACTION_FACT_LOSS = "COMPACTION_FACT_LOSS"
    INFRASTRUCTURE_ERROR = "INFRASTRUCTURE_ERROR"


INFRASTRUCTURE_FAILURES = {
    FailureState.MODEL_ERROR,
    FailureState.TOOL_RUNNER_FAILURE,
    FailureState.GRADER_ERROR,
    FailureState.COMPACTION_ENDPOINT_ERROR,
    FailureState.INFRASTRUCTURE_ERROR,
}

AGENT_FAILURES = {
    FailureState.TOOL_COMMAND_INVALID,
    FailureState.TOOL_TIMEOUT,
    FailureState.PARSER_ERROR,
    FailureState.CONTEXT_EXHAUSTED,
    FailureState.TIMEOUT,
}

TREATMENT_FAILURES = {
    FailureState.COMPACTION_PARSE_ERROR,
    FailureState.COMPACTION_LENGTH_VIOLATION,
}


@dataclass
class StateMachine:
    run_id: str
    state: RunState = RunState.CREATED
    failure_state: FailureState | None = None
    transitions: list[dict[str, Any]] = field(default_factory=list)

    def transition(self, new_state: RunState, **meta: Any) -> None:
        self.transitions.append({"from": self.state.value, "to": new_state.value, **meta})
        self.state = new_state

    def fail(self, failure: FailureState, message: str = "", **meta: Any) -> dict[str, Any]:
        self.failure_state = failure
        return {
            "failure_state": failure.value,
            "message": message,
            "retry_eligible": failure in INFRASTRUCTURE_FAILURES,
            **meta,
        }

    def to_status(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "state": self.state.value,
            "failure_state": self.failure_state.value if self.failure_state else None,
            "transitions": self.transitions,
        }
