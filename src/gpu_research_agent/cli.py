from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .config import DEFAULT_MODEL, DEFAULT_ROUND_BUDGET_SECONDS, WorkspaceLayout
from .loop import run_research_round
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
    run_parser.add_argument("--question", required=True, help="Research question")

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
    _log(f"initialized root={layout.root}")
    print(f"Initialized workspace at {layout.root}")


def command_run_round(layout: WorkspaceLayout, question: str) -> None:
    _log(f"run_round question={question}")
    result = run_research_round(layout, question)
    print(
        json.dumps(
            {
                "question_id": result.question.id,
                "spec_id": result.spec.id,
                "run_id": result.run.id,
                "observation_id": result.observation.id,
                "claim_id": result.claim.id,
                "verification_id": result.verification.id,
                "claim_status": result.claim.status,
                "workflow_proposal_id": result.next_step.id,
            },
            indent=2,
            sort_keys=True,
        )
    )


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
        command_run_round(layout, args.question)
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
