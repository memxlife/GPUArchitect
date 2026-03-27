from __future__ import annotations

import time
import uuid

from knowledge.store import add_claim
from knowledge.validate import validate_claim
from llm.openai_client import call_analysis
from core.prompt_loader import load_prompt
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"


def load_sweep(filename: str):
    with open(RESULTS_DIR / filename, "r") as f:
        return json.load(f)


def build_generic_summary(rows: list[dict]) -> str:
    lines = ["Sweep results:"]

    for row in rows:
        # print all relevant fields generically
        parts = []
        for k, v in row.items():
            if k != "stdout":
                parts.append(f"{k}={v}")
        lines.append("- " + ", ".join(parts))

    return "\n".join(lines)


def process_pattern_claim(
    filename: str,
    prompt_template: str,
    benchmark: str,
    source: str,
):
    rows = load_sweep(filename)
    summary = build_generic_summary(rows)

    template = load_prompt(prompt_template)
    prompt = template.format(summary_text=summary)

    response = call_analysis(prompt)

    try:
        claim = json.loads(response)
    except Exception:
        print("Invalid JSON:", response)
        return

    claim["id"] = f"claim_{uuid.uuid4().hex[:8]}"
    claim["timestamp"] = time.time()
    claim["type"] = "pattern"
    claim["benchmark"] = benchmark
    claim["source"] = source

    ok, msg = validate_claim(claim)
    if not ok:
        print("Rejected:", msg)
        return

    add_claim(claim)
    print("Stored claim.")
