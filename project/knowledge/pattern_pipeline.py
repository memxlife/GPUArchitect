from __future__ import annotations

from knowledge.draft_pattern_claim import (
    load_sweep_file,
    build_inner_iters_summary,
    generate_pattern_claim_from_sweep,
)
from knowledge.store import add_claim
from knowledge.validate import validate_claim


def process_pattern_claim_from_sweep(filename: str) -> None:
    sweep_rows = load_sweep_file(filename)
    summary_text = build_inner_iters_summary(sweep_rows)
    claim = generate_pattern_claim_from_sweep(summary_text)

    if "error" in claim:
        print("Pattern claim draft failed:")
        print(claim)
        return

    print("\n=== PATTERN CLAIM DRAFT ===")
    print(claim)

    ok, msg = validate_claim(claim)
    if not ok:
        print("Pattern claim rejected:", msg)
        return

    add_claim(claim)
    print("Pattern claim accepted and stored.")
