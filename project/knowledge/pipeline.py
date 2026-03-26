from __future__ import annotations

from knowledge.validate import validate_claim
from knowledge.store import add_claim
from knowledge.draft_claim import generate_claim_draft


def process_claim_from_observations(observations_text: str):
    # Step 1: generate draft
    claim = generate_claim_draft(observations_text)

    if "error" in claim:
        print("Draft generation failed:", claim)
        return

    print("\n=== CLAIM DRAFT ===")
    print(claim)

    # Step 2: validate
    ok, msg = validate_claim(claim)

    if not ok:
        print("Claim rejected:", msg)
        return

    # Step 3: promote
    add_claim(claim)

    print("Claim accepted and stored.")
