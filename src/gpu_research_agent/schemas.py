from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def to_plain_data(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_plain_data(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: to_plain_data(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_plain_data(item) for item in value]
    return value


def require_fields(record: dict[str, Any], fields: list[str]) -> None:
    missing = [field for field in fields if field not in record or record[field] in (None, "", [])]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")


@dataclass(slots=True)
class ResearchQuestion:
    topic: str
    rationale: str
    scope: str
    priority: int = 1
    id: str = field(default_factory=lambda: new_id("question"))
    created_at: str = field(default_factory=utc_now)

    def validate(self) -> None:
        payload = to_plain_data(self)
        require_fields(payload, ["topic", "rationale", "scope", "priority"])


@dataclass(slots=True)
class ExperimentSpec:
    question_id: str
    hypothesis: str
    benchmark_type: str
    parameters: dict[str, Any]
    deterministic_controls: dict[str, Any]
    budget_seconds: int
    expected_outputs: list[str]
    executor_ref: str
    id: str = field(default_factory=lambda: new_id("spec"))
    created_at: str = field(default_factory=utc_now)

    def validate(self) -> None:
        payload = to_plain_data(self)
        require_fields(
            payload,
            [
                "question_id",
                "hypothesis",
                "benchmark_type",
                "parameters",
                "deterministic_controls",
                "budget_seconds",
                "expected_outputs",
                "executor_ref",
            ],
        )
        if self.budget_seconds <= 0:
            raise ValueError("budget_seconds must be positive")


@dataclass(slots=True)
class RunRecord:
    spec_id: str
    question_id: str
    command: list[str]
    artifact_paths: dict[str, str]
    elapsed_seconds: float
    exit_code: int
    environment: dict[str, Any]
    id: str = field(default_factory=lambda: new_id("run"))
    created_at: str = field(default_factory=utc_now)

    def validate(self) -> None:
        payload = to_plain_data(self)
        require_fields(
            payload,
            [
                "spec_id",
                "question_id",
                "command",
                "artifact_paths",
                "elapsed_seconds",
                "exit_code",
                "environment",
            ],
        )


@dataclass(slots=True)
class ObservationRecord:
    run_id: str
    spec_id: str
    parser_version: str
    metrics: dict[str, Any]
    evidence_paths: list[str]
    id: str = field(default_factory=lambda: new_id("observation"))
    created_at: str = field(default_factory=utc_now)

    def validate(self) -> None:
        payload = to_plain_data(self)
        require_fields(payload, ["run_id", "spec_id", "parser_version", "metrics", "evidence_paths"])


@dataclass(slots=True)
class ClaimRecord:
    question_id: str
    spec_id: str
    observation_id: str
    statement: str
    status: str
    confidence: str
    support_summary: str
    counterevidence: list[str]
    provenance_paths: list[str]
    id: str = field(default_factory=lambda: new_id("claim"))
    created_at: str = field(default_factory=utc_now)

    def validate(self) -> None:
        payload = to_plain_data(self)
        require_fields(
            payload,
            [
                "question_id",
                "spec_id",
                "observation_id",
                "statement",
                "status",
                "confidence",
                "support_summary",
                "provenance_paths",
            ],
        )
        if self.status not in {"candidate", "accepted", "disputed", "pending"}:
            raise ValueError(f"Unsupported claim status: {self.status}")


@dataclass(slots=True)
class VerificationRecord:
    claim_id: str
    spec_id: str
    method: str
    result: str
    notes: str
    evidence_paths: list[str]
    rerun_run_id: str | None = None
    id: str = field(default_factory=lambda: new_id("verification"))
    created_at: str = field(default_factory=utc_now)

    def validate(self) -> None:
        payload = to_plain_data(self)
        require_fields(payload, ["claim_id", "spec_id", "method", "result", "notes", "evidence_paths"])
        if self.result not in {"accepted", "disputed", "pending"}:
            raise ValueError(f"Unsupported verification result: {self.result}")


@dataclass(slots=True)
class WorkflowProposal:
    bottleneck: str
    proposal: str
    expected_gain: str
    risk: str
    rollback_condition: str
    approval_state: str = "proposed"
    target_workflow_version: str | None = None
    proposed_profile_updates: list[dict[str, Any]] = field(default_factory=list)
    continue_recommended: bool = True
    stop_reason: str | None = None
    id: str = field(default_factory=lambda: new_id("workflow"))
    created_at: str = field(default_factory=utc_now)

    def validate(self) -> None:
        payload = to_plain_data(self)
        require_fields(
            payload,
            ["bottleneck", "proposal", "expected_gain", "risk", "rollback_condition", "approval_state"],
        )


@dataclass(slots=True)
class ResearchRoundResult:
    question: ResearchQuestion
    spec: ExperimentSpec
    run: RunRecord
    observation: ObservationRecord
    claim: ClaimRecord
    verification: VerificationRecord
    next_step: WorkflowProposal
