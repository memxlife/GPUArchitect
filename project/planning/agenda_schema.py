from __future__ import annotations

from typing import Any


ALLOWED_BENCHMARKS = {"compute", "memory"}
ALLOWED_STATUS = {"enabled", "active", "disabled"}


def validate_agenda(agenda: dict[str, Any]) -> tuple[bool, str]:
    required_fields = [
        "id",
        "name",
        "status",
        "benchmark",
        "benchmark_name",
        "type",
        "priority",
        "uncertainty",
        "readiness",
        "estimated_cost",
        "rationale",
        "parameter_space",
        "activation",
        "completion",
        "next_if_resolved",
    ]

    for field in required_fields:
        if field not in agenda:
            return False, f"Missing field: {field}"

    if agenda["status"] not in ALLOWED_STATUS:
        return False, f"Invalid status: {agenda['status']}"

    if agenda["benchmark"] not in ALLOWED_BENCHMARKS:
        return False, f"Invalid benchmark: {agenda['benchmark']}"

    for field in ["priority", "uncertainty", "readiness", "estimated_cost"]:
        value = agenda[field]
        if not isinstance(value, (int, float)):
            return False, f"Field {field} must be numeric"

    if not isinstance(agenda["parameter_space"], dict):
        return False, "parameter_space must be a dict"

    if not isinstance(agenda["activation"], dict):
        return False, "activation must be a dict"

    if not isinstance(agenda["completion"], dict):
        return False, "completion must be a dict"

    if not isinstance(agenda["next_if_resolved"], list):
        return False, "next_if_resolved must be a list"

    return True, "OK"


def validate_agenda_list(agendas: list[dict[str, Any]]) -> tuple[bool, str]:
    seen_ids: set[str] = set()

    for agenda in agendas:
        ok, msg = validate_agenda(agenda)
        if not ok:
            return False, msg

        agenda_id = agenda["id"]
        if agenda_id in seen_ids:
            return False, f"Duplicate agenda id: {agenda_id}"
        seen_ids.add(agenda_id)

    return True, "OK"
