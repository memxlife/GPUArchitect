from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from llm.openai_client import call_analysis
from planning.agenda_schema import validate_agenda_list


ROOT = Path(__file__).resolve().parents[1]
CLAIMS_FILE = ROOT / "knowledge" / "claims.jsonl"
AGENDAS_DIR = ROOT / "planning" / "agendas"
OUTPUT_FILE = ROOT / "planning" / "proposed_agendas.json"


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


def load_existing_agendas() -> list[dict[str, Any]]:
    agendas: list[dict[str, Any]] = []
    if not AGENDAS_DIR.exists():
        return agendas

    for path in sorted(AGENDAS_DIR.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            agendas.append(json.load(f))
    return agendas


def summarize_claims(claims: list[dict[str, Any]], limit: int = 12) -> str:
    lines: list[str] = []
    lines.append("Accepted claims summary:")

    for claim in claims[-limit:]:
        lines.append(
            f"- id={claim.get('id')} "
            f"type={claim.get('type')} "
            f"benchmark={claim.get('benchmark')} "
            f"source={claim.get('source')} "
            f"description={claim.get('description')}"
        )

    return "\n".join(lines)


def summarize_existing_agendas(agendas: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append("Existing agenda specifications:")
    for agenda in agendas:
        lines.append(
            f"- id={agenda.get('id')} "
            f"name={agenda.get('name')} "
            f"benchmark={agenda.get('benchmark')} "
            f"type={agenda.get('type')} "
            f"rationale={agenda.get('rationale')}"
        )
    return "\n".join(lines)


def build_prompt() -> str:
    claims = load_jsonl(CLAIMS_FILE)
    agendas = load_existing_agendas()

    claims_summary = summarize_claims(claims)
    agendas_summary = summarize_existing_agendas(agendas)

    return f"""
You are proposing new experiment agendas for an autonomous GPU architecture learning system.

Current accepted knowledge:
{claims_summary}

Current existing agenda specs:
{agendas_summary}

Goal:
Propose at most 3 NEW agenda items that the system should learn next.
These agendas should target unresolved, high-value architectural knowledge.
Do not repeat existing agendas.
Do not propose agendas that require unavailable tools.
Available benchmark families are:
- compute
- memory

Output must be valid JSON only.
Return a JSON array of agenda objects.

Each agenda object must contain these fields:
- id: string
- name: string
- status: string ("enabled")
- benchmark: string ("compute" or "memory")
- benchmark_name: string
- type: string
- priority: number
- uncertainty: number
- readiness: number
- estimated_cost: number
- rationale: string
- parameter_space: object
- activation: object
- completion: object
- next_if_resolved: array

Guidelines:
1. Prefer agendas that quantify missing GPU behavior.
2. Use benchmark-specific parameter spaces.
3. Keep completion criteria text-based for now.
4. Do not propose more than 3 agendas.
5. Ground proposals in the current claims.
"""


def propose_agendas() -> list[dict[str, Any]]:
    prompt = build_prompt()
    response = call_analysis(prompt)

    try:
        agendas = json.loads(response)
    except Exception:
        raise RuntimeError(f"Failed to parse proposed agendas as JSON:\n{response}")

    if not isinstance(agendas, list):
        raise RuntimeError("Proposed agendas must be a JSON array.")

    ok, msg = validate_agenda_list(agendas)
    if not ok:
        raise RuntimeError(f"Proposed agendas failed validation: {msg}")

    return agendas


def main() -> None:
    agendas = propose_agendas()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(agendas, f, indent=2)

    print(f"Proposed agendas written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
