from __future__ import annotations

from llm.openai_client import call_analysis


def interpret_result(text: str) -> str:
    prompt = f"""
Here is the benchmark output:

{text}

Please answer:
1. What kind of benchmark is this?
2. Is it more likely compute-bound or memory-bound?
3. What evidence supports that conclusion?
4. What next experiment should we run next to learn more?
5. What parameters should we vary next?
"""

    return call_analysis(prompt)
