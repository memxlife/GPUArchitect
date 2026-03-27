from __future__ import annotations

import time
import uuid

from knowledge.draft_iterations_stability_claim import (
    load_sweep_file,
    build_summary,
    generate_iterations_stability_claim,
)
from knowledge.store import add_claim
from knowledge.validate import validate_claim


def process_iterations_stability_claim(
    filename: str = "compute_iterations_stability_sweep.json",
    benchmark: str = "compute_fma_like",
    source: str = "iterations_sweep",
) -> None:
    rows = load_sweep_file(filename)
    summary_text = build_summary(rows)
    claim = generate_iterations_stability_claim(summary_text)

    if "error" in claim:
        print("Iterations stability claim failed:")
        print(claim)
        return

    # enforce schema
    claim["id"] = f"claim_{uuid.uuid4().hex[:8]}"
    claim["timestamp"] = time.time()
    claim["type"] = "pattern"
    claim["benchmark"] = benchmark
    claim["source"] = source

    print("\n=== ITERATIONS STABILITY CLAIM ===")
    print(claim)

    ok, msg = validate_claim(claim)
    if not ok:
        print("Rejected:", msg)
        return

    add_claim(claim)
    print("Claim stored.")


def main():
    process_iterations_stability_claim()


if __name__ == "__main__":
    main()
