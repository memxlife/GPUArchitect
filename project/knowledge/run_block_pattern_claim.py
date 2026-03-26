from __future__ import annotations

import time
import uuid

from knowledge.draft_block_pattern_claim import (
    load_block_sweep_file,
    build_block_sweep_summary,
    generate_block_pattern_claim_from_summary,
)
from knowledge.store import add_claim
from knowledge.validate import validate_claim


def process_block_pattern_claim(
    filename: str = "compute_block_sensitivity_sweep.json",
    benchmark: str = "compute_fma_like",
    source: str = "block_sweep",
    claim_type: str = "pattern",
) -> None:
    rows = load_block_sweep_file(filename)
    summary_text = build_block_sweep_summary(rows)
    claim = generate_block_pattern_claim_from_summary(summary_text)

    if "error" in claim:
        print("Block pattern claim draft failed:")
        print(claim)
        return

    claim["id"] = f"claim_{uuid.uuid4().hex[:8]}"
    claim["timestamp"] = time.time()
    claim.setdefault("type", claim_type)
    claim.setdefault("benchmark", benchmark)
    claim.setdefault("source", source)

    print("\n=== BLOCK PATTERN CLAIM DRAFT ===")
    print(claim)

    ok, msg = validate_claim(claim)
    if not ok:
        print("Block pattern claim rejected:", msg)
        return

    add_claim(claim)
    print("Block pattern claim accepted and stored.")


def main() -> None:
    process_block_pattern_claim()


if __name__ == "__main__":
    main()
