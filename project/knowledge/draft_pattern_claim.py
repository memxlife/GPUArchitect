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


def parse_metric_from_stdout(stdout: str, key: str):
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith(f"{key}="):
            value = line.split("=", 1)[1]
            if value == "inf":
                return float("inf")
            try:
                return float(value)
            except ValueError:
                return value
    return None


def build_inner_iters_summary(rows: list[dict]) -> str:
    lines: list[str] = []
    lines.append("Sweep summary for compute_fma_like inner_iters sweep:")
    lines.append("Observed rows:")

    for row in rows:
        inner_iters = row.get("inner_iters")

        avg_time_ms = row.get("avg_time_ms")
        checksum = row.get("checksum_1024")

        if avg_time_ms is None and "stdout" in row:
            avg_time_ms = parse_metric_from_stdout(row["stdout"], "avg_time_ms")

        if checksum is None and "stdout" in row:
            checksum = parse_metric_from_stdout(row["stdout"], "checksum_1024")

        lines.append(
            f"- inner_iters={inner_iters}, avg_time_ms={avg_time_ms}, checksum_1024={checksum}"
        )

    return "\n".join(lines)


def generate_pattern_claim_from_sweep(summary_text: str) -> dict:
    template = load_prompt("pattern_claim.txt")
    prompt = template.format(summary_text=summary_text)

    response = call_analysis(prompt)

    try:
        return json.loads(response)
    except Exception:
        return {"error": "invalid_json", "raw": response}
