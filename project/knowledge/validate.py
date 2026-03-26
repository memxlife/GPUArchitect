def validate_claim(claim: dict) -> tuple[bool, str]:
    if not claim.get("id"):
        return False, "Missing id"

    if not claim.get("type"):
        return False, "Missing type"

    if not claim.get("benchmark"):
        return False, "Missing benchmark"

    if not claim.get("source"):
        return False, "Missing source"

    if not claim.get("evidence"):
        return False, "Missing evidence"

    if not claim.get("cause"):
        return False, "Missing cause"

    if not claim.get("mechanism"):
        return False, "Missing mechanism"

    if not claim.get("implication"):
        return False, "Missing implication"

    if claim.get("uncertainty") not in ["low", "medium", "high"]:
        return False, "Invalid uncertainty"

    return True, "OK"
