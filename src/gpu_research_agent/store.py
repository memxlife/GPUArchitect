from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .config import WorkspaceLayout
from .schemas import ClaimRecord, ObservationRecord, RunRecord, VerificationRecord, WorkflowProposal, to_plain_data


class AppendOnlyStore:
    def __init__(self, layout: WorkspaceLayout) -> None:
        self.layout = layout

    def init_workspace(self) -> None:
        for path in [
            self.layout.data_dir,
            self.layout.plans_dir,
            self.layout.runs_dir,
            self.layout.records_dir,
            self.layout.knowledge_dir,
            self.layout.exports_dir,
            self.layout.site_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def run_dir(self, run_id: str) -> Path:
        return self.layout.runs_dir / run_id

    def plan_dir(self, spec_id: str) -> Path:
        return self.layout.plans_dir / spec_id

    def write_plan_artifact(self, spec_id: str, name: str, content: str) -> Path:
        plan_dir = self.plan_dir(spec_id)
        plan_dir.mkdir(parents=True, exist_ok=True)
        target = plan_dir / name
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite existing artifact: {target}")
        target.write_text(content, encoding="utf-8")
        return target

    def write_run_artifact(self, run_id: str, name: str, content: str) -> Path:
        run_dir = self.run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        target = run_dir / name
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite existing artifact: {target}")
        target.write_text(content, encoding="utf-8")
        return target

    def append_jsonl(self, name: str, record: Any) -> Path:
        target = self.layout.records_dir / f"{name}.jsonl"
        payload = json.dumps(to_plain_data(record), ensure_ascii=True, sort_keys=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(payload)
            handle.write("\n")
        return target

    def load_jsonl(self, name: str) -> list[dict[str, Any]]:
        target = self.layout.records_dir / f"{name}.jsonl"
        if not target.exists():
            return []
        rows: list[dict[str, Any]] = []
        with target.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows

    def latest_record(self, name: str) -> dict[str, Any] | None:
        records = self.load_jsonl(name)
        return records[-1] if records else None

    def rebuild_exports(self) -> None:
        questions = self.load_jsonl("questions")
        specs = self.load_jsonl("specs")
        claims = self.load_jsonl("claims")
        observations = self.load_jsonl("observations")
        verifications = self.load_jsonl("verifications")
        runs = self.load_jsonl("runs")
        workflow_proposals = self.load_jsonl("workflow_proposals")

        self._write_markdown_knowledge(questions, specs, claims, observations, verifications)
        self._write_yaml_export(questions, specs, claims, observations, verifications)
        self._write_history_summary(questions, specs, runs, observations, verifications, workflow_proposals)

    def _write_markdown_knowledge(
        self,
        questions: list[dict[str, Any]],
        specs: list[dict[str, Any]],
        claims: list[dict[str, Any]],
        observations: list[dict[str, Any]],
        verifications: list[dict[str, Any]],
    ) -> None:
        claims_dir = self.layout.knowledge_dir / "claims"
        claims_dir.mkdir(parents=True, exist_ok=True)

        question_lookup = {item["id"]: item for item in questions}
        spec_lookup = {item["id"]: item for item in specs}
        observation_lookup = {item["id"]: item for item in observations}
        verification_lookup = {item["claim_id"]: item for item in verifications}
        index_lines = [
            "# Knowledge Base",
            "",
            "This directory contains curated claim documents and derived summaries.",
            "It is not the append-only run history.",
            "",
            f"Questions: {len(questions)}",
            f"Experiment Specs: {len(specs)}",
            f"Claims: {len(claims)}",
            "",
        ]

        for claim in claims:
            question = question_lookup.get(claim["question_id"], {})
            spec = spec_lookup.get(claim["spec_id"], {})
            observation = observation_lookup.get(claim["observation_id"], {})
            verification = verification_lookup.get(claim["id"], {})
            claim_path = claims_dir / f"{claim['id']}.md"
            body = [
                f"# {claim['id']}",
                "",
                f"Question: {question.get('topic', 'unknown')}",
                f"Hypothesis: {spec.get('hypothesis', 'unknown')}",
                "",
                f"Status: {claim['status']}",
                f"Confidence: {claim['confidence']}",
                "",
                "## Statement",
                claim["statement"],
                "",
                "## Support Summary",
                claim["support_summary"],
                "",
                "## Metrics",
                "",
            ]
            for key, value in sorted(observation.get("metrics", {}).items()):
                body.append(f"- {key}: {value}")
            body.extend(
                [
                    "",
                    "## Verification",
                    verification.get("result", "missing"),
                    "",
                    verification.get("notes", "No verification record"),
                    "",
                ]
            )
            claim_path.write_text("\n".join(body), encoding="utf-8")
            index_lines.append(f"- [{claim['id']}](claims/{claim['id']}.md): {claim['statement']}")

        (self.layout.knowledge_dir / "index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    def _write_yaml_export(
        self,
        questions: list[dict[str, Any]],
        specs: list[dict[str, Any]],
        claims: list[dict[str, Any]],
        observations: list[dict[str, Any]],
        verifications: list[dict[str, Any]],
    ) -> None:
        question_lookup = {item["id"]: item for item in questions}
        spec_lookup = {item["id"]: item for item in specs}
        observation_lookup = {item["id"]: item for item in observations}
        verification_lookup = {item["claim_id"]: item for item in verifications}
        payload = {
            "knowledge_base": [
                {
                    "claim_id": claim["id"],
                    "question": question_lookup.get(claim["question_id"], {}).get("topic"),
                    "hypothesis": spec_lookup.get(claim["spec_id"], {}).get("hypothesis"),
                    "statement": claim["statement"],
                    "status": claim["status"],
                    "confidence": claim["confidence"],
                    "support_summary": claim["support_summary"],
                    "counterevidence": claim["counterevidence"],
                    "evidence_paths": claim["provenance_paths"],
                    "metrics": observation_lookup.get(claim["observation_id"], {}).get("metrics", {}),
                    "verification": verification_lookup.get(claim["id"], {}),
                }
                for claim in claims
            ]
        }
        target = self.layout.exports_dir / "knowledge.yaml"
        target.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    def _write_history_summary(
        self,
        questions: list[dict[str, Any]],
        specs: list[dict[str, Any]],
        runs: list[dict[str, Any]],
        observations: list[dict[str, Any]],
        verifications: list[dict[str, Any]],
        workflow_proposals: list[dict[str, Any]],
    ) -> None:
        target = self.layout.exports_dir / "history_summary.yaml"
        payload = {
            "history_summary": {
                "questions": len(questions),
                "specs": len(specs),
                "runs": len(runs),
                "observations": len(observations),
                "verifications": len(verifications),
                "workflow_proposals": len(workflow_proposals),
            },
            "note": "This summary is derived from append-only records in data/records and raw artifacts in data/plans and data/runs.",
        }
        target.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    def append_round(
        self,
        question: Any,
        spec: Any,
        run: RunRecord,
        observation: ObservationRecord,
        claim: ClaimRecord,
        verification: VerificationRecord,
        proposal: WorkflowProposal,
    ) -> None:
        question.validate()
        spec.validate()
        proposal.validate()
        for record in [run, observation, claim, verification]:
            record.validate()
        self.append_jsonl("questions", question)
        self.append_jsonl("specs", spec)
        self.append_jsonl("runs", run)
        self.append_jsonl("observations", observation)
        self.append_jsonl("claims", claim)
        self.append_jsonl("verifications", verification)
        self.append_jsonl("workflow_proposals", proposal)
        self.rebuild_exports()
