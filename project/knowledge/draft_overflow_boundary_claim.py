from __future__ import annotations

import json
from pathlib import Path

from llm.openai_client import call_analysis
from core.prompt_loader import load_prompt


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"


def load_sweep_file(filename: str) -> list[dict]:
    path = RESULTS_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_summary(rows: list[dict]) -> str:
    lines = []
    lines.append("Overflow boundary sweep results:")

    for row in rows:
        inner_iters = row.get("inner_iters")
        avg_time = row.get("avg_time_ms")
        checksum = row.get("checksum_1024")

        lines.append(
            f"- inner_iters={inner_iters}, avg_time_ms={avg_time}, checksum_1024={checksum}"
        )

    return "\n".join(lines)


def generate_overflow_claim(summary_text: str) -> dict:
    template = load_prompt("overflow_boundary_claim.txt")
    prompt = template.format(summary_text=summary_text)

    response = call_analysis(prompt)

    try:
        return json.loads(response)
    except Exception:
        return {"error": "invalid_json", "raw": response}
