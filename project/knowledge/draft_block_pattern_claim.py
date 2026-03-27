from __future__ import annotations

import json
from pathlib import Path

from llm.openai_client import call_analysis
from core.prompt_loader import load_prompt


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
    template = load_prompt("block_pattern_claim.txt")
    prompt = template.format(summary_text=summary_text)

    response = call_analysis(prompt)

    try:
        return json.loads(response)
    except Exception:
        return {"error": "invalid_json", "raw": response}
