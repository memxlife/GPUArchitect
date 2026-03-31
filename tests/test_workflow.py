from __future__ import annotations

from gpu_research_agent.workflow import load_workflow_definition


def test_workflow_definition_has_role_context_sections() -> None:
    workflow = load_workflow_definition()

    planner = workflow.profile("planner")
    analyzer = workflow.profile("analyzer")

    assert workflow.version == "workflow_v1"
    assert "question" in planner.context_sections
    assert "raw_output" in analyzer.context_sections


def test_workflow_render_payload_uses_declared_sections_only() -> None:
    workflow = load_workflow_definition()

    payload = workflow.render_payload(
        "planner",
        {
            "question": "q",
            "workflow_constraints": {"max_round_budget_seconds": 120},
            "defaults": {"benchmark_type": "synthetic_memory_probe"},
            "unused": "ignore-me",
        },
    )

    assert payload["question"] == "q"
    assert "unused" not in payload
