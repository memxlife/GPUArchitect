from __future__ import annotations

import time
import uuid

from knowledge.validate import validate_claim
from knowledge.store import add_claim
from knowledge.draft_claim import generate_claim_draft


def process_claim_from_observations(
    observations_text: str,
    benchmark: str = "compute_fma_like",
    source: str = "single_run",
    claim_type: str = "observation",
) -> None:
    # Step 1: generate draft
    claim = generate_claim_draft(observations_text)

    if "error" in claim:
        print("Draft generation failed:", claim)
        return

    # Step 2: enforce schema fields
    claim["id"] = f"claim_{uuid.uuid4().hex[:8]}"
    claim["timestamp"] = time.time()
    claim.setdefault("type", claim_type)
    claim.setdefault("benchmark", benchmark)
    claim.setdefault("source", source)

    print("\n=== CLAIM DRAFT ===")
    print(claim)

    # Step 3: validate
    ok, msg = validate_claim(claim)

    if not ok:
        print("Claim rejected:", msg)
        return

    # Step 4: promote
    add_claim(claim)
    print("Claim accepted and stored.")
