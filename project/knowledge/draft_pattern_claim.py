from __future__ import annotations

import json
from pathlib import Path

from llm.openai_client import call_analysis


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"


def load_sweep_file(filename: str) -> list[dict]:
    path = RESULTS_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_inner_iters_summary(sweep_rows: list[dict]) -> str:
    lines = []
    lines.append("Sweep summary for compute_fma_like:")
    lines.append("Fixed parameters:")
    lines.append("- n = 16777216")
    lines.append("- threads_per_block = 256")
    lines.append("")
    lines.append("Observed rows:")

    for row in sweep_rows:
        inner_iters = row.get("inner_iters")
        stdout = row.get("stdout", "")

        avg_time_ms = None
        checksum = None

        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("avg_time_ms="):
                avg_time_ms = line.split("=", 1)[1]
            elif line.startswith("checksum_1024="):
                checksum = line.split("=", 1)[1]

        lines.append(
            f"- inner_iters={inner_iters}, avg_time_ms={avg_time_ms}, checksum_1024={checksum}"
        )

    return "\n".join(lines)


def generate_pattern_claim_from_sweep(summary_text: str) -> dict:
    prompt = f"""
Given the following multi-observation sweep results:

{summary_text}

Generate exactly one JSON object with these fields:
- description: string
- evidence: array
- cause: string
- mechanism: string
- implication: string
- uncertainty: string

Requirements:
1. Output valid JSON only.
2. Do not include markdown fences.
3. The uncertainty field must be exactly one of:
   "low", "medium", "high"
4. Base the claim only on the provided sweep results.
5. This should be a pattern-level claim, not a single-run claim.
6. The evidence field should be an array of concise supporting observations.
"""

    response = call_analysis(prompt)
    try:
        return json.loads(response)
    except Exception:
        return {"error": "invalid_json", "raw": response}
