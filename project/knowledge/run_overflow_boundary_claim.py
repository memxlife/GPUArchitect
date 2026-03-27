from __future__ import annotations

import time
import uuid

from knowledge.draft_overflow_boundary_claim import (
    load_sweep_file,
    build_summary,
    generate_overflow_claim,
)
from knowledge.store import add_claim
from knowledge.validate import validate_claim


def process_overflow_claim(
    filename: str = "latest_sweep.json",
    benchmark: str = "compute_fma_like",
    source: str = "overflow_sweep",
) -> None:
    rows = load_sweep_file(filename)
    summary = build_summary(rows)
    claim = generate_overflow_claim(summary)

    if "error" in claim:
        print("Overflow claim failed:", claim)
        return

    claim["id"] = f"claim_{uuid.uuid4().hex[:8]}"
    claim["timestamp"] = time.time()
    claim["type"] = "pattern"
    claim["benchmark"] = benchmark
    claim["source"] = source

    print("\n=== OVERFLOW CLAIM ===")
    print(claim)

    ok, msg = validate_claim(claim)
    if not ok:
        print("Rejected:", msg)
        return

    add_claim(claim)
    print("Stored.")
