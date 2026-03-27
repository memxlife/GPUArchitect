from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.agenda_schema import validate_agenda_list


ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "data" / "planning" / "proposed_agendas.json"
OUTPUT_FILE = ROOT / "data" / "planning" / "normalized_proposed_agendas.json"


def load_proposed_agendas() -> list[dict[str, Any]]:
    if not INPUT_FILE.exists():
        return []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise RuntimeError("proposed_agendas.json must contain a JSON array.")

    return data


def normalize_activation(raw_activation: dict[str, Any] | None) -> dict[str, Any]:
    if not raw_activation:
        return {}

    normalized: dict[str, Any] = {}

    # Preserve fields already compatible with the planner schema.
    if "requires_resolved_agenda_ids" in raw_activation:
        normalized["requires_resolved_agenda_ids"] = raw_activation["requires_resolved_agenda_ids"]

    if "requires_pattern_claim" in raw_activation:
        normalized["requires_pattern_claim"] = raw_activation["requires_pattern_claim"]

    if "pattern_keywords_any" in raw_activation:
        normalized["pattern_keywords_any"] = raw_activation["pattern_keywords_any"]

    # Ignore free-form fields like "when" and "evidence_required" for now.
    return normalized


def normalize_completion(raw_completion: dict[str, Any] | None) -> dict[str, Any]:
    if not raw_completion:
        return {"pattern_keywords_any": []}

    normalized: dict[str, Any] = {}

    if "pattern_keywords_any" in raw_completion:
        normalized["pattern_keywords_any"] = raw_completion["pattern_keywords_any"]
    else:
        # Future: convert success_criteria into claim-generation prompts or structured checks.
        normalized["pattern_keywords_any"] = []

    return normalized


def normalize_parameter_space(raw_parameter_space: dict[str, Any] | None) -> dict[str, Any]:
    if not raw_parameter_space:
        return {}

    normalized = dict(raw_parameter_space)

    # Remove "benchmark" if the proposer nested it here redundantly.
    normalized.pop("benchmark", None)

    # Ensure common parameter values are lists.
    for key in ["n", "threads_per_block", "inner_iters", "iterations"]:
        if key in normalized and not isinstance(normalized[key], list):
            normalized[key] = [normalized[key]]

    return normalized


def normalize_one_agenda(raw_agenda: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {
        "id": raw_agenda["id"],
        "name": raw_agenda["name"],
        "status": raw_agenda.get("status", "enabled"),
        "benchmark": raw_agenda["benchmark"],
        "benchmark_name": raw_agenda["benchmark_name"],
        "type": raw_agenda["type"],
        "priority": float(raw_agenda["priority"]),
        "uncertainty": float(raw_agenda["uncertainty"]),
        "readiness": float(raw_agenda["readiness"]),
        "estimated_cost": float(raw_agenda["estimated_cost"]),
        "rationale": raw_agenda["rationale"],
        "parameter_space": normalize_parameter_space(raw_agenda.get("parameter_space")),
        "activation": normalize_activation(raw_agenda.get("activation")),
        "completion": normalize_completion(raw_agenda.get("completion")),
        "next_if_resolved": raw_agenda.get("next_if_resolved", []),
    }

    return normalized


def normalize_agendas(raw_agendas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [normalize_one_agenda(a) for a in raw_agendas]


def main() -> None:
    raw_agendas = load_proposed_agendas()
    normalized_agendas = normalize_agendas(raw_agendas)

    ok, msg = validate_agenda_list(normalized_agendas)
    if not ok:
        raise RuntimeError(f"Normalized agendas failed validation: {msg}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(normalized_agendas, f, indent=2)

    print(f"Normalized agendas written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
