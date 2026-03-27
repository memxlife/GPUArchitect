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
    lines.append("Iterations stability sweep results:")

    for row in rows:
        inner_iters = row.get("inner_iters")
        iterations = row.get("iterations")
        avg_time_ms = row.get("avg_time_ms")

        lines.append(
            f"- inner_iters={inner_iters}, iterations={iterations}, avg_time_ms={avg_time_ms}"
        )

    return "\n".join(lines)


def generate_iterations_stability_claim(summary_text: str) -> dict:
    template = load_prompt("iterations_stability_claim.txt")
    prompt = template.format(summary_text=summary_text)

    response = call_analysis(prompt)

    try:
        return json.loads(response)
    except Exception:
        return {"error": "invalid_json", "raw": response}
