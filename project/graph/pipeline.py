from __future__ import annotations

from typing import TypedDict


class PipelineState(TypedDict, total=False):
    benchmark: str
    program_args: list[str]
    raw_output: str
    parsed_output: dict
