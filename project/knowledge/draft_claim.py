from __future__ import annotations

import json

from llm.openai_client import call_analysis
from core.prompt_loader import load_prompt


def generate_claim_draft(observations_text: str) -> dict:
    template = load_prompt("claim_draft.txt")
    prompt = template.format(observations_text=observations_text)

    response = call_analysis(prompt)

    try:
        return json.loads(response)
    except Exception:
        return {"error": "invalid_json", "raw": response}
