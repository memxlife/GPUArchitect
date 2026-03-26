from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLANNING_STATE_FILE = ROOT / "planning" / "planning_state.json"


def load_planning_state(path: Path = PLANNING_STATE_FILE) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def score_question(question: dict[str, Any]) -> float:
    """
    General planner scoring function.

    Higher is better.
    Current simple formula:
        score = priority * uncertainty * readiness / cost

    This is intentionally simple for v0.4.
    """
    priority = float(question.get("priority", 0.0))
    uncertainty = float(question.get("uncertainty", 0.0))
    readiness = float(question.get("readiness", 0.0))
    cost = float(question.get("estimated_cost", 1.0))

    if cost <= 0:
        cost = 1.0

    return (priority * uncertainty * readiness) / cost


def select_best_question(state: dict[str, Any]) -> dict[str, Any] | None:
    questions = state.get("active_questions", [])
    if not questions:
        return None

    scored = [(score_question(q), q) for q in questions if q.get("status") == "active"]
    if not scored:
        return None

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def generate_experiment_plan(question: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """
    Convert a selected question into a concrete experiment plan.

    The specifics live in planning_state.json.
    The planner engine remains general.
    """
    parameter_space = question.get("parameter_space", {})
    benchmark = question.get("benchmark", "compute")
    benchmark_name = question.get("benchmark_name", "unknown")
    default_n = state.get("defaults", {}).get("n", 1 << 24)
    default_iterations = state.get("defaults", {}).get("iterations", 20)

    plan: dict[str, Any] = {
        "question_id": question.get("id"),
        "reason": question.get("rationale", ""),
        "benchmark": benchmark,
        "benchmark_name": benchmark_name,
        "n": question.get("n", default_n),
        "iterations": question.get("iterations", default_iterations),
        "parameter_space": parameter_space,
    }

    return plan


def select_next_experiment() -> dict[str, Any]:
    state = load_planning_state()
    question = select_best_question(state)

    if question is None:
        return {
            "question_id": None,
            "reason": "No active questions available.",
            "benchmark": "compute",
            "benchmark_name": "compute_fma_like",
            "n": state.get("defaults", {}).get("n", 1 << 24),
            "iterations": state.get("defaults", {}).get("iterations", 20),
            "parameter_space": {},
        }

    return generate_experiment_plan(question, state)


def main() -> None:
    plan = select_next_experiment()
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
