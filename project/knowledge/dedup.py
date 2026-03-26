def is_duplicate_claim(new_claim: dict, existing_claims: list[dict]) -> bool:
    for c in existing_claims:
        if (
            c.get("type") == new_claim.get("type") and
            c.get("benchmark") == new_claim.get("benchmark") and
            c.get("description")[:80] == new_claim.get("description")[:80]
        ):
            return True
    return False
