from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .config import DEFAULT_ROUND_BUDGET_SECONDS, PACKAGE_ROOT


WORKFLOW_PATH = PACKAGE_ROOT / "workflow" / "active.yaml"


@dataclass(frozen=True)
class AgentProfile:
    name: str
    instructions: str
    context_sections: list[str]
    sandbox_mode: str
    web_search_enabled: bool


@dataclass(frozen=True)
class WorkflowDefinition:
    version: str
    summary: str
    roles: dict[str, AgentProfile]

    def profile(self, name: str) -> AgentProfile:
        try:
            return self.roles[name]
        except KeyError as exc:
            raise KeyError(f"Unknown workflow role: {name}") from exc

    def render_payload(self, role: str, available_sections: dict[str, Any]) -> dict[str, Any]:
        profile = self.profile(role)
        payload: dict[str, Any] = {
            "workflow_version": self.version,
            "workflow_summary": self.summary,
        }
        for section in profile.context_sections:
            if section in available_sections:
                payload[section] = available_sections[section]
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "summary": self.summary,
            "roles": {
                name: {
                    "instructions": profile.instructions,
                    "context_sections": profile.context_sections,
                    "sandbox_mode": profile.sandbox_mode,
                    "web_search_enabled": profile.web_search_enabled,
                }
                for name, profile in self.roles.items()
            },
        }


def load_workflow_definition() -> WorkflowDefinition:
    payload = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    roles = {
        name: AgentProfile(
            name=name,
            instructions=str(config["instructions"]),
            context_sections=list(config["context_sections"]),
            sandbox_mode=str(config.get("sandbox_mode", "read-only")),
            web_search_enabled=bool(config.get("web_search_enabled", False)),
        )
        for name, config in payload["roles"].items()
    }
    return WorkflowDefinition(
        version=str(payload["version"]),
        summary=str(payload["summary"]),
        roles=roles,
    )


def workflow_constraints() -> dict[str, Any]:
    return {
        "single_gpu_scope": True,
        "append_only_history_required": True,
        "knowledge_base_separate_from_history": True,
        "max_round_budget_seconds": DEFAULT_ROUND_BUDGET_SECONDS,
        "must_preserve_workflow_stages": [
            "select_question",
            "form_hypothesis",
            "generate_spec",
            "execute_benchmark",
            "extract_observations",
            "analyze",
            "verify",
            "curate_knowledge",
            "plan_next_step",
        ],
    }
