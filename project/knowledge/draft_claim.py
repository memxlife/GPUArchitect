from llm.openai_client import call_analysis
import json


def generate_claim_draft(observations_text: str) -> dict:
    prompt = f"""
Given the following benchmark results:

{observations_text}

Generate exactly one JSON object with the following fields:

- description: string
- evidence: object or array
- cause: string
- mechanism: string
- implication: string
- uncertainty: string ("low", "medium", "high")
- type: string ("observation" or "pattern")
- benchmark: string
- source: string ("single_run" or "sweep")

Requirements:
1. Output valid JSON only (no markdown fences).
2. All fields must be present.
3. Ground all statements strictly in the given data.
4. Do NOT invent data.
"""

    response = call_analysis(prompt)

    try:
        return json.loads(response)
    except Exception:
        return {"error": "invalid_json", "raw": response}
