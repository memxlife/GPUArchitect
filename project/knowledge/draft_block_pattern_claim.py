from __future__ import annotations

import json
from pathlib import Path

from llm.openai_client import call_analysis


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"


def load_block_sweep_file(filename: str) -> list[dict]:
    path = RESULTS_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_block_sweep_summary(rows: list[dict]) -> str:
    lines: list[str] = []
    lines.append("Sweep summary for compute_fma_like block sensitivity:")
    lines.append("Observed rows:")

    for row in rows:
        tpb = row.get("threads_per_block")
        inner_iters = row.get("inner_iters")
        avg_time_ms = row.get("avg_time_ms")
        checksum = row.get("checksum_1024")

        lines.append(
            f"- threads_per_block={tpb}, inner_iters={inner_iters}, "
            f"avg_time_ms={avg_time_ms}, checksum_1024={checksum}"
        )

    return "\n".join(lines)


def generate_block_pattern_claim_from_summary(summary_text: str) -> dict:
    prompt = f"""
Given the following block-sensitivity sweep results:

{summary_text}

Generate exactly one JSON object with these fields:
- description: string
- evidence: array
- cause: string
- mechanism: string
- implication: string
- uncertainty: string ("low", "medium", "high")
- type: string ("pattern")
- benchmark: string
- source: string ("block_sweep")

Requirements:
1. Output valid JSON only.
2. Do not include markdown fences.
3. Ground the claim strictly in the provided sweep data.
4. This is a pattern-level claim, not a single-run claim.
5. Keep evidence concise and specific.
"""

    response = call_analysis(prompt)

    try:
        return json.loads(response)
    except Exception:
        return {"error": "invalid_json", "raw": response}
