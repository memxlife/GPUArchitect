from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .config import DEFAULT_MODEL, DEFAULT_ROUND_BUDGET_SECONDS, WorkspaceLayout
from .loop import run_research_round
from .schemas import new_id
from .session import (
    append_operator_directive,
    build_continuation_context,
    load_session_state,
    save_session_state,
)
from .site import rebuild_site
from .store import AppendOnlyStore
from .workflow import load_workflow_definition


def _log(message: str) -> None:
    print(f"[gpuarchitect] {message}", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPUArchitect research loop CLI")
    parser.add_argument("--root", default=".", help="Workspace root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize workspace directories")

    run_parser = subparsers.add_parser("run-round", help="Run one research round")
    run_parser.add_argument("--question", help="Research question")
    run_parser.add_argument("--directive", help="Operator continuation instruction")

    loop_parser = subparsers.add_parser("run-loop", help="Run multiple research rounds")
    loop_parser.add_argument("--question", help="Initial research question")
    loop_parser.add_argument("--directive", help="Operator continuation instruction")
    loop_parser.add_argument("--rounds", type=int, help="Number of rounds to run")
    loop_parser.add_argument("--auto", action="store_true", help="Run until the workflow recommends stopping")

    verify_parser = subparsers.add_parser("verify-claim", help="Show verification record for a claim")
    verify_parser.add_argument("--claim-id", required=True, help="Claim identifier")

    subparsers.add_parser("show-workflow", help="Show active workflow definition")
    subparsers.add_parser("rebuild-site", help="Rebuild static knowledge exports")
    subparsers.add_parser("status", help="Show repository research status")
    return parser.parse_args()


def command_init(layout: WorkspaceLayout) -> None:
    store = AppendOnlyStore(layout)
    store.init_workspace()
    if not layout.config_path.exists():
        layout.config_path.write_text(
            yaml.safe_dump(
                {
                    "default_model": DEFAULT_MODEL,
                    "round_budget_seconds": DEFAULT_ROUND_BUDGET_SECONDS,
                    "agent_runtime_dir": str(layout.agent_runtime_dir),
                    "site_entrypoint": str(layout.site_dir / "index.html"),
                    "knowledge_index": str(layout.knowledge_dir / "index.md"),
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
    state = load_session_state(layout)
    if state.get("session_id") is None:
        save_session_state(
            layout,
            {
                "session_id": new_id("session"),
                "status": "idle",
                "rounds_completed": 0,
                "mode": None,
            },
        )
    _log(f"initialized root={layout.root}")
    print(f"Initialized workspace at {layout.root}")


def _run_loop(
    layout: WorkspaceLayout,
    *,
    question: str | None,
    directive: str | None,
    rounds: int | None,
    auto: bool,
) -> list[dict[str, str]]:
    store = AppendOnlyStore(layout)
    store.init_workspace()
    state = load_session_state(layout)
    if state.get("session_id") is None:
        state["session_id"] = new_id("session")
    state["status"] = "running"
    state["mode"] = "auto" if auto else ("finite" if rounds not in (None, 1) else "manual")
    state["target_rounds"] = rounds
    save_session_state(layout, state)

    if directive:
        append_operator_directive(
            store,
            session_id=state["session_id"],
            directive=directive,
            round_index=state.get("rounds_completed"),
        )

    outputs: list[dict[str, str]] = []
    initial_question = question
    round_counter = 0

    try:
        while True:
            if rounds is not None and round_counter >= rounds:
                break
            _log(f"loop_round index={round_counter + 1} mode={state['mode']}")
            result = run_research_round(
                layout,
                initial_question if round_counter == 0 else None,
                operator_directive=directive if round_counter == 0 else None,
            )
            round_counter += 1
            state["rounds_completed"] = int(state.get("rounds_completed", 0)) + 1
            state["last_question_id"] = result.question.id
            state["last_claim_id"] = result.claim.id
            state["last_workflow_proposal_id"] = result.next_step.id
            save_session_state(layout, state)
            outputs.append(
                {
                    "question_id": result.question.id,
                    "spec_id": result.spec.id,
                    "run_id": result.run.id,
                    "observation_id": result.observation.id,
                    "claim_id": result.claim.id,
                    "verification_id": result.verification.id,
                    "workflow_proposal_id": result.next_step.id,
                    "claim_status": result.claim.status,
                }
            )
            if not auto and rounds in (None, 1):
                break
            if auto and not result.next_step.continue_recommended:
                state["status"] = "completed"
                state["stop_reason"] = result.next_step.stop_reason or "workflow_recommended_stop"
                save_session_state(layout, state)
                _log(f"loop_stop reason={state['stop_reason']}")
                break
        else:
            state["status"] = "completed"
            save_session_state(layout, state)
    except KeyboardInterrupt:
        state["status"] = "paused"
        save_session_state(layout, state)
        _log("loop_interrupted status=paused")
        raise

    if state.get("status") == "running":
        state["status"] = "idle" if not auto else "completed"
        save_session_state(layout, state)
    return outputs


def command_run_round(layout: WorkspaceLayout, question: str | None, directive: str | None) -> None:
    _log(f"run_round question={question or '<continue>'}")
    result_rows = _run_loop(layout, question=question, directive=directive, rounds=1, auto=False)
    result = result_rows[-1]
    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    )


def command_run_loop(layout: WorkspaceLayout, question: str | None, directive: str | None, rounds: int | None, auto: bool) -> None:
    if auto and rounds is not None:
        raise SystemExit("Use either --auto or --rounds, not both.")
    effective_rounds = None if auto else (rounds or 1)
    _log(
        f"run_loop question={question or '<continue>'} rounds={effective_rounds if effective_rounds is not None else 'auto'}"
    )
    results = _run_loop(layout, question=question, directive=directive, rounds=effective_rounds, auto=auto)
    print(json.dumps({"rounds": results}, indent=2, sort_keys=True))


def command_verify_claim(layout: WorkspaceLayout, claim_id: str) -> None:
    store = AppendOnlyStore(layout)
    verifications = store.load_jsonl("verifications")
    for record in reversed(verifications):
        if record["claim_id"] == claim_id:
            print(json.dumps(record, indent=2, sort_keys=True))
            return
    raise SystemExit(f"Verification record not found for claim {claim_id}")


def command_rebuild_site(layout: WorkspaceLayout) -> None:
    rebuild_site(layout)
    _log(f"rebuild_site root={layout.root}")
    print(f"Rebuilt exports in {layout.site_dir}")


def command_show_workflow() -> None:
    workflow = load_workflow_definition()
    print(json.dumps(workflow.to_dict(), indent=2, sort_keys=True))


def command_status(layout: WorkspaceLayout) -> None:
    store = AppendOnlyStore(layout)
    workflow = load_workflow_definition()
    runs = store.load_jsonl("runs")
    claims = store.load_jsonl("claims")
    verifications = store.load_jsonl("verifications")
    session_state = load_session_state(layout)
    latest_claim = claims[-1]["id"] if claims else None
    print(
        json.dumps(
            {
                "runs": len(runs),
                "questions": len(store.load_jsonl("questions")),
                "specs": len(store.load_jsonl("specs")),
                "claims": len(claims),
                "verifications": len(verifications),
                "latest_claim": latest_claim,
                "workflow_version": workflow.version,
                "session_state": session_state,
                "agent_runtime_dir": str(layout.agent_runtime_dir),
                "site_index": str(layout.site_dir / "index.html"),
                "knowledge_index": str(layout.knowledge_dir / "index.md"),
                "yaml_export": str(layout.exports_dir / "knowledge.yaml"),
            },
            indent=2,
            sort_keys=True,
        )
    )


def main() -> None:
    args = parse_args()
    layout = WorkspaceLayout(root=Path(args.root).resolve())

    if args.command == "init":
        command_init(layout)
        return
    if args.command == "run-round":
        command_run_round(layout, args.question, args.directive)
        return
    if args.command == "run-loop":
        command_run_loop(layout, args.question, args.directive, args.rounds, args.auto)
        return
    if args.command == "verify-claim":
        command_verify_claim(layout, args.claim_id)
        return
    if args.command == "show-workflow":
        command_show_workflow()
        return
    if args.command == "rebuild-site":
        command_rebuild_site(layout)
        return
    if args.command == "status":
        command_status(layout)
        return

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
