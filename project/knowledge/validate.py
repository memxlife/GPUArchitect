def validate_claim(claim: dict) -> tuple[bool, str]:
    # Rule 1: evidence
    if not claim.get("evidence"):
        return False, "Missing evidence"

    # Rule 2: cause
    if not claim.get("cause"):
        return False, "Missing cause"

    # Rule 3: mechanism
    if not claim.get("mechanism"):
        return False, "Missing mechanism"

    # Rule 4: implication
    if not claim.get("implication"):
        return False, "Missing implication"

    # Rule 5: uncertainty
    if claim.get("uncertainty") not in ["low", "medium", "high"]:
        return False, "Invalid uncertainty"

    return True, "OK"
