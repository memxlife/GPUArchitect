from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import WorkspaceLayout
from .schemas import utc_now
from .store import AppendOnlyStore


def session_state_path(layout: WorkspaceLayout) -> Path:
    return layout.control_dir / "session_state.json"


def load_session_state(layout: WorkspaceLayout) -> dict[str, Any]:
    path = session_state_path(layout)
    if not path.exists():
        return {
            "session_id": None,
            "status": "idle",
            "rounds_completed": 0,
            "mode": None,
            "updated_at": utc_now(),
        }
    return json.loads(path.read_text(encoding="utf-8"))


def save_session_state(layout: WorkspaceLayout, state: dict[str, Any]) -> None:
    layout.control_dir.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = utc_now()
    session_state_path(layout).write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def append_operator_directive(
    store: AppendOnlyStore,
    *,
    session_id: str | None,
    directive: str,
    round_index: int | None,
) -> None:
    record = {
        "id": f"directive_{utc_now()}",
        "session_id": session_id,
        "directive": directive,
        "round_index": round_index,
        "created_at": utc_now(),
    }
    store.append_jsonl("operator_directives", record)


def build_continuation_context(store: AppendOnlyStore) -> dict[str, Any]:
    questions = store.load_jsonl("questions")
    specs = store.load_jsonl("specs")
    claims = store.load_jsonl("claims")
    verifications = store.load_jsonl("verifications")
    workflow_proposals = store.load_jsonl("workflow_proposals")
    directives = store.load_jsonl("operator_directives")

    latest_question = questions[-1] if questions else None
    latest_spec = specs[-1] if specs else None
    latest_claim = claims[-1] if claims else None
    latest_verification = verifications[-1] if verifications else None
    latest_proposal = workflow_proposals[-1] if workflow_proposals else None
    latest_directive = directives[-1] if directives else None

    return {
        "history_counts": {
            "questions": len(questions),
            "specs": len(specs),
            "claims": len(claims),
            "verifications": len(verifications),
            "workflow_proposals": len(workflow_proposals),
        },
        "latest_question": latest_question,
        "latest_spec": latest_spec,
        "latest_claim": latest_claim,
        "latest_verification": latest_verification,
        "latest_workflow_proposal": latest_proposal,
        "latest_operator_directive": latest_directive,
        "recent_claims": claims[-5:],
    }
