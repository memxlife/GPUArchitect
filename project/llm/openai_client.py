from __future__ import annotations

import os
from openai import OpenAI

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client

    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        _client = OpenAI(api_key=api_key)

    return _client


def call_analysis(prompt: str) -> str:
    client = get_client()

    response = client.responses.create(
        model="gpt-5.4",
        input=prompt,
    )

    return response.output_text

from openai import OpenAI


client = OpenAI()


def _extract_text(response) -> str:
    if hasattr(response, "output_text") and response.output_text:
        return response.output_text
    raise RuntimeError("OpenAI response did not contain output_text.")


def call_llm(system_prompt: str, user_prompt: str, model: str = "gpt-5.4") -> str:
    try:
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
        )
        return _extract_text(response)
    except Exception as exc:
        raise RuntimeError(f"LLM call failed for model={model}: {exc}") from exc


def call_codegen(prompt: str) -> str:
    system_prompt = (
        "You are an expert CUDA and systems programming assistant. "
        "Write correct, minimal, runnable code. "
        "Do not add unnecessary explanation unless asked."
    )
    return call_llm(system_prompt, prompt, model="gpt-5.3-codex")


def call_analysis(prompt: str) -> str:
    system_prompt = (
        "You are an expert GPU performance analyst. "
        "Reason carefully from the provided benchmark or profiler output. "
        "State uncertainty when evidence is insufficient."
    )
    return call_llm(system_prompt, prompt, model="gpt-5.4")
