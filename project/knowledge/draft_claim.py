from llm.openai_client import call_analysis
import json

def generate_claim_draft(observations_text: str) -> dict:
    prompt = f"""
Given the following benchmark results:

{observations_text}

Generate exactly one JSON object with the following fields:
- description: string
- evidence: object
- cause: string
- mechanism: string
- implication: string
- uncertainty: string

Requirements:
1. Output valid JSON only.
2. Do not include markdown fences.
3. The uncertainty field must be exactly one of:
   "low", "medium", "high"
4. Keep the claim grounded in the provided results only.
"""

    response = call_analysis(prompt)

    try:
        return json.loads(response)
    except Exception:
        return {{"error": "invalid_json", "raw": response}}
