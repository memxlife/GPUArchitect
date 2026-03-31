from __future__ import annotations

import json

from gpu_research_agent.config import WorkspaceLayout
from gpu_research_agent.schemas import (
    ClaimRecord,
    ExperimentSpec,
    ObservationRecord,
    ResearchQuestion,
    RunRecord,
    VerificationRecord,
    WorkflowProposal,
)
from gpu_research_agent.store import AppendOnlyStore


def test_append_only_artifact_write(tmp_path) -> None:
    layout = WorkspaceLayout(root=tmp_path)
    store = AppendOnlyStore(layout)
    store.init_workspace()

    target = store.write_run_artifact("run_1", "stdout.json", "{}")
    assert target.exists()

    try:
        store.write_run_artifact("run_1", "stdout.json", "{}")
    except FileExistsError:
        pass
    else:
        raise AssertionError("Expected append-only artifact protection")


def test_export_rebuild(tmp_path) -> None:
    layout = WorkspaceLayout(root=tmp_path)
    store = AppendOnlyStore(layout)
    store.init_workspace()

    question = ResearchQuestion(
        topic="Synthetic probe question",
        rationale="test",
        scope="single_gpu_microbenchmark",
        id="question_1",
    )
    spec = ExperimentSpec(
        question_id="question_1",
        hypothesis="Synthetic throughput is stable.",
        benchmark_type="synthetic_memory_probe",
        parameters={"working_set_kb": 256},
        deterministic_controls={"seed": 7},
        budget_seconds=120,
        expected_outputs=["stdout.json"],
        executor_ref="python_module:test",
        id="spec_1",
    )
    run = RunRecord(
        spec_id="spec_1",
        question_id="question_1",
        command=["python", "-m", "demo"],
        artifact_paths={"stdout": "data/runs/run_1/stdout.json"},
        elapsed_seconds=0.1,
        exit_code=0,
        environment={"python": "3.11"},
        id="run_1",
    )
    observation = ObservationRecord(
        run_id="run_1",
        spec_id="spec_1",
        parser_version="v1",
        metrics={"throughput_score": 1.2},
        evidence_paths=["data/runs/run_1/stdout.json"],
        id="observation_1",
    )
    claim = ClaimRecord(
        question_id="question_1",
        spec_id="spec_1",
        observation_id="observation_1",
        statement="Synthetic throughput stayed stable.",
        status="accepted",
        confidence="medium",
        support_summary="Single deterministic sample.",
        counterevidence=[],
        provenance_paths=["data/runs/run_1/stdout.json"],
        id="claim_1",
    )
    verification = VerificationRecord(
        claim_id="claim_1",
        spec_id="spec_1",
        method="independent_rerun",
        result="accepted",
        notes="Matched.",
        evidence_paths=["data/runs/run_1/stdout.json"],
        id="verification_1",
    )
    proposal = WorkflowProposal(
        bottleneck="none",
        proposal="add benchmark",
        expected_gain="coverage",
        risk="low",
        rollback_condition="remove",
        id="workflow_1",
    )

    store.append_round(question, spec, run, observation, claim, verification, proposal)

    yaml_export = (layout.exports_dir / "knowledge.yaml").read_text(encoding="utf-8")
    assert "knowledge_base:" in yaml_export
    assert "claim_1" in yaml_export
    history_summary = (layout.exports_dir / "history_summary.yaml").read_text(encoding="utf-8")
    assert "history_summary:" in history_summary
    knowledge_index = (layout.knowledge_dir / "index.md").read_text(encoding="utf-8")
    assert "claim_1" in knowledge_index
