from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CLAIMS_FILE = ROOT / "data" / "knowledge" / "claims.jsonl"
AGENDAS_DIR = ROOT / "specs" / "agendas"
NORMALIZED_PROPOSED_FILE = ROOT / "data" / "planning" / "normalized_proposed_agendas.json"
OUTPUT_FILE = ROOT / "data" / "planning" / "planning_state.json"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def load_builtin_agendas() -> list[dict[str, Any]]:
    agendas: list[dict[str, Any]] = []
    if not AGENDAS_DIR.exists():
        return agendas

    for path in sorted(AGENDAS_DIR.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            agendas.append(json.load(f))
    return agendas


def load_normalized_proposed_agendas() -> list[dict[str, Any]]:
    if not NORMALIZED_PROPOSED_FILE.exists():
        return []

    with open(NORMALIZED_PROPOSED_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise RuntimeError("normalized_proposed_agendas.json must contain a JSON array.")

    return data


def merge_agendas(
    builtin_agendas: list[dict[str, Any]],
    proposed_agendas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}

    for agenda in builtin_agendas:
        merged[agenda["id"]] = agenda

    # Proposed agendas only fill new IDs; built-ins remain authoritative for same IDs.
    for agenda in proposed_agendas:
        if agenda["id"] not in merged:
            merged[agenda["id"]] = agenda

    return list(merged.values())


def pattern_claims_for_benchmark(claims: list[dict[str, Any]], benchmark_name: str) -> list[dict[str, Any]]:
    return [
        c for c in claims
        if c.get("type") == "pattern" and c.get("benchmark") == benchmark_name
    ]


def claim_text(claim: dict[str, Any]) -> str:
    return " ".join(
        str(claim.get(k, "")) for k in ["description", "cause", "mechanism", "implication"]
    ).lower()


def any_keyword_match(text: str, keywords: list[str]) -> bool:
    text = text.lower()
    return any(k.lower() in text for k in keywords)


def agenda_completed(agenda: dict[str, Any], claims: list[dict[str, Any]]) -> bool:
    benchmark_name = agenda.get("benchmark_name", "")
    relevant_claims = pattern_claims_for_benchmark(claims, benchmark_name)
    completion = agenda.get("completion", {})
    keywords = completion.get("pattern_keywords_any", [])

    if not keywords:
        return False

    for claim in relevant_claims:
        if any_keyword_match(claim_text(claim), keywords):
            return True
    return False


def agenda_activated(
    agenda: dict[str, Any],
    claims: list[dict[str, Any]],
    completed_ids: set[str],
) -> bool:
    activation = agenda.get("activation", {})

    required_ids = activation.get("requires_resolved_agenda_ids", [])
    if any(req not in completed_ids for req in required_ids):
        return False

    if activation.get("requires_pattern_claim", False):
        benchmark_name = agenda.get("benchmark_name", "")
        relevant_claims = pattern_claims_for_benchmark(claims, benchmark_name)
        if not relevant_claims:
            return False

        keywords = activation.get("pattern_keywords_any", [])
        if keywords:
            for claim in relevant_claims:
                if any_keyword_match(claim_text(claim), keywords):
                    return True
            return False

    return True


def build_active_questions(claims: list[dict[str, Any]], agendas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    completed_ids = {agenda["id"] for agenda in agendas if agenda_completed(agenda, claims)}

    active: list[dict[str, Any]] = []
    for agenda in agendas:
        if agenda.get("status") != "enabled":
            continue
        if agenda["id"] in completed_ids:
            continue
        if agenda_activated(agenda, claims, completed_ids):
            active_agenda = dict(agenda)
            active_agenda["status"] = "active"
            active.append(active_agenda)

    return active


def build_planning_state() -> dict[str, Any]:
    claims = load_jsonl(CLAIMS_FILE)
    builtin_agendas = load_builtin_agendas()
    proposed_agendas = load_normalized_proposed_agendas()
    agendas = merge_agendas(builtin_agendas, proposed_agendas)

    active_questions = build_active_questions(claims, agendas)

    return {
        "version": "v0.6",
        "defaults": {
            "n": 1 << 24,
            "iterations": 20
        },
        "active_questions": active_questions,
        "metadata": {
            "num_claims": len(claims),
            "num_builtin_agendas": len(builtin_agendas),
            "num_proposed_agendas": len(proposed_agendas),
            "num_total_agendas": len(agendas),
            "source_claims": str(CLAIMS_FILE),
            "source_builtin_agendas": str(AGENDAS_DIR),
            "source_proposed_agendas": str(NORMALIZED_PROPOSED_FILE),
        }
    }


def main() -> None:
    state = build_planning_state()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    print(f"Planning state written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
