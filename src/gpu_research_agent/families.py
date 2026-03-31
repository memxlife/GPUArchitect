from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .config import PACKAGE_ROOT


FAMILIES_PATH = PACKAGE_ROOT / "workflow" / "experiment_families.yaml"


@dataclass(frozen=True)
class ExperimentFamily:
    name: str
    description: str
    template_type: str
    tunable_parameters: dict[str, Any]
    execution_notes: str
    expected_outputs: list[str]
    executor_ref: str


def load_experiment_families() -> dict[str, ExperimentFamily]:
    payload = yaml.safe_load(FAMILIES_PATH.read_text(encoding="utf-8"))
    families: dict[str, ExperimentFamily] = {}
    for item in payload["families"]:
        family = ExperimentFamily(
            name=str(item["name"]),
            description=str(item["description"]),
            template_type=str(item["template_type"]),
            tunable_parameters=dict(item["tunable_parameters"]),
            execution_notes=str(item["execution_notes"]),
            expected_outputs=list(item["expected_outputs"]),
            executor_ref=str(item["executor_ref"]),
        )
        families[family.name] = family
    return families


def families_for_prompt() -> list[dict[str, Any]]:
    return [
        {
            "name": family.name,
            "description": family.description,
            "template_type": family.template_type,
            "tunable_parameters": family.tunable_parameters,
            "execution_notes": family.execution_notes,
            "expected_outputs": family.expected_outputs,
            "executor_ref": family.executor_ref,
        }
        for family in load_experiment_families().values()
    ]
