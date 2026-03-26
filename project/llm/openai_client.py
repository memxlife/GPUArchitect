from __future__ import annotations

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
