from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import yaml

from .codex_client import CodexClient
from .config import DEFAULT_MODEL, DEFAULT_ROUND_BUDGET_SECONDS, WorkspaceLayout
from .families import families_for_prompt, load_experiment_families
from .schemas import (
    ClaimRecord,
    ExperimentSpec,
    ObservationRecord,
    ResearchQuestion,
    RunRecord,
    VerificationRecord,
    WorkflowProposal,
    to_plain_data,
)
from .store import AppendOnlyStore
from .workflow import WorkflowDefinition, load_workflow_definition, workflow_constraints


PARSER_VERSION = "v1"


@dataclass(slots=True)
class Planner:
    store: AppendOnlyStore
    codex: CodexClient
    workflow: WorkflowDefinition

    def plan(
        self,
        question_text: str | None,
        *,
        continuation_context: dict,
        operator_directive: str | None,
    ) -> tuple[ResearchQuestion, ExperimentSpec]:
        topic = (question_text or "").strip()
        family_registry = load_experiment_families()
        preferred_family = "synthetic_memory_probe" if os.getenv("GPUARCHITECT_FORCE_SYNTHETIC") == "1" else "cuda_memory_hierarchy_probe"
        default_payload = {
            "selected_question": topic or "Continue the latest GPU research thread with one bounded follow-up experiment.",
            "rationale": "Capture a bounded, reproducible first research question for the vertical slice.",
            "scope": "single_gpu_microbenchmark",
            "hypothesis": (
                "Increasing working-set size and stride will lower effective bandwidth in a bounded CUDA memory probe."
                if preferred_family == "cuda_memory_hierarchy_probe"
                else "Larger working sets will reduce synthetic throughput while keeping the signal deterministic."
            ),
            "benchmark_type": preferred_family,
            "working_set_kb": 256,
            "stride_bytes": 64,
            "iterations": 20000 if preferred_family == "cuda_memory_hierarchy_probe" else 40000,
            "sleep_ms": 10,
            "threads_per_block": 128,
            "blocks": 80,
            "repeat_count": 3,
            "seed": 7,
            "expected_outputs": family_registry[preferred_family].expected_outputs,
            "executor_ref": family_registry[preferred_family].executor_ref,
        }
        output_schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "selected_question": {"type": "string"},
                "rationale": {"type": "string"},
                "scope": {"type": "string"},
                "hypothesis": {"type": "string"},
                "benchmark_type": {
                    "type": "string",
                    "enum": sorted(family_registry.keys()),
                },
                "working_set_kb": {"type": "integer"},
                "stride_bytes": {"type": "integer"},
                "iterations": {"type": "integer"},
                "sleep_ms": {"type": "integer"},
                "threads_per_block": {"type": "integer"},
                "blocks": {"type": "integer"},
                "repeat_count": {"type": "integer"},
                "seed": {"type": "integer"},
                "expected_outputs": {"type": "array", "items": {"type": "string"}},
                "executor_ref": {"type": "string"},
            },
            "required": [
                "rationale",
                "scope",
                "hypothesis",
                "selected_question",
                "benchmark_type",
                "working_set_kb",
                "stride_bytes",
                "iterations",
                "sleep_ms",
                "threads_per_block",
                "blocks",
                "repeat_count",
                "seed",
                "expected_outputs",
                "executor_ref",
            ],
        }
        profile = self.workflow.profile("planner")
        result = self.codex.invoke_json(
            role="planner",
            instructions=profile.instructions,
            payload=self.workflow.render_payload(
                "planner",
                {
                    "question": topic,
                    "operator_directive": operator_directive,
                    "continuation_context": continuation_context,
                    "experiment_families": families_for_prompt(),
                    "workflow_constraints": workflow_constraints(),
                    "defaults": default_payload,
                },
            ),
            output_schema=output_schema,
            fallback_output=default_payload,
            sandbox_mode=profile.sandbox_mode,
            web_search_enabled=profile.web_search_enabled,
            stream_mode="turn",
        )
        payload = result.output
        question = ResearchQuestion(
            topic=str(payload.get("selected_question", topic or default_payload["selected_question"])),
            rationale=str(payload.get("rationale", default_payload["rationale"])),
            scope=str(payload.get("scope", default_payload["scope"])),
        )
        spec = ExperimentSpec(
            question_id=question.id,
            hypothesis=str(payload.get("hypothesis", default_payload["hypothesis"])),
            benchmark_type=str(payload.get("benchmark_type", default_payload["benchmark_type"])),
            parameters={
                "working_set_kb": int(payload.get("working_set_kb", default_payload["working_set_kb"])),
                "stride_bytes": int(payload.get("stride_bytes", default_payload["stride_bytes"])),
                "iterations": int(payload.get("iterations", default_payload["iterations"])),
                "sleep_ms": int(payload.get("sleep_ms", default_payload["sleep_ms"])),
                "threads_per_block": int(payload.get("threads_per_block", default_payload["threads_per_block"])),
                "blocks": int(payload.get("blocks", default_payload["blocks"])),
            },
            deterministic_controls={
                "seed": int(payload.get("seed", default_payload["seed"])),
                "repeat_count": int(payload.get("repeat_count", default_payload["repeat_count"])),
            },
            budget_seconds=min(int(payload.get("budget_seconds", DEFAULT_ROUND_BUDGET_SECONDS)), DEFAULT_ROUND_BUDGET_SECONDS),
            expected_outputs=list(payload.get("expected_outputs", default_payload["expected_outputs"])),
            executor_ref=str(payload.get("executor_ref", default_payload["executor_ref"])),
        )
        question.validate()
        spec.validate()
        self.store.write_plan_artifact(spec.id, "question.json", json.dumps(to_plain_data(question), indent=2, sort_keys=True))
        self.store.write_plan_artifact(spec.id, "spec.json", json.dumps(to_plain_data(spec), indent=2, sort_keys=True))
        self.store.write_plan_artifact(
            spec.id,
            "planner_output.json",
            json.dumps(
                {
                    "backend": result.backend,
                    "thread_id": result.thread_id,
                    "usage": result.usage,
                    "output": payload,
                },
                indent=2,
                sort_keys=True,
            ),
        )
        self.store.write_plan_artifact(
            spec.id,
            "workflow_snapshot.yaml",
            yaml.safe_dump(self.workflow.to_dict(), sort_keys=False),
        )
        self.store.write_plan_artifact(spec.id, "planner_events.jsonl", _events_to_jsonl(result.events))
        return question, spec


@dataclass(slots=True)
class Executor:
    layout: WorkspaceLayout
    store: AppendOnlyStore

    def run(self, question: ResearchQuestion, spec: ExperimentSpec) -> RunRecord:
        compile_log_path = self.store.run_dir("compile_placeholder") / "compile.log"
        run = RunRecord(
            spec_id=spec.id,
            question_id=question.id,
            command=[],
            artifact_paths={},
            elapsed_seconds=0.0,
            exit_code=-1,
            environment=self._environment_snapshot(),
        )
        run.command, compile_log_path = self._build_command(run.id, spec)

        self.store.write_run_artifact(run.id, "question.json", json.dumps(to_plain_data(question), indent=2, sort_keys=True))
        self.store.write_run_artifact(run.id, "spec.json", json.dumps(to_plain_data(spec), indent=2, sort_keys=True))

        start = time.perf_counter()
        try:
            result = subprocess.run(
                run.command,
                cwd=str(self.layout.root),
                capture_output=True,
                text=True,
                check=False,
                timeout=spec.budget_seconds,
            )
            elapsed = time.perf_counter() - start
            stdout_text = result.stdout
            stderr_text = result.stderr
            exit_code = result.returncode
        except subprocess.TimeoutExpired as exc:
            elapsed = time.perf_counter() - start
            stdout_text = exc.stdout or ""
            stderr_text = (exc.stderr or "") + "\nExecution timed out."
            exit_code = 124
        stdout_path = self.store.write_run_artifact(run.id, "stdout.json", stdout_text)
        stderr_path = self.store.write_run_artifact(run.id, "stderr.txt", stderr_text)
        run.elapsed_seconds = elapsed
        run.exit_code = exit_code
        run.artifact_paths = {
            "question": str(self.store.run_dir(run.id) / "question.json"),
            "spec": str(self.store.run_dir(run.id) / "spec.json"),
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
        }
        if compile_log_path.exists():
            run.artifact_paths["compile_log"] = str(compile_log_path)
        run.validate()
        return run

    def _build_command(self, run_id: str, spec: ExperimentSpec) -> tuple[list[str], Path]:
        params = spec.parameters
        if spec.benchmark_type == "cuda_memory_hierarchy_probe":
            benchmark_script = Path(__file__).resolve().parent / "benchmarks" / "cuda_memory_hierarchy_probe.py"
            build_dir = self.layout.root / "build"
            compile_log = self.store.run_dir(run_id) / "compile.log"
            return ([
                sys.executable,
                str(benchmark_script),
                "--working-set-kb",
                str(params["working_set_kb"]),
                "--stride-bytes",
                str(params["stride_bytes"]),
                "--iterations",
                str(params["iterations"]),
                "--threads-per-block",
                str(params["threads_per_block"]),
                "--blocks",
                str(params["blocks"]),
                "--repeat-count",
                str(spec.deterministic_controls.get("repeat_count", 3)),
                "--seed",
                str(spec.deterministic_controls.get("seed", 7)),
                "--build-dir",
                str(build_dir),
                "--compile-log",
                str(compile_log),
            ], compile_log)

        benchmark_script = Path(__file__).resolve().parent / "benchmarks" / "synthetic_memory_probe.py"
        return ([
            sys.executable,
            str(benchmark_script),
            "--working-set-kb",
            str(params["working_set_kb"]),
            "--stride-bytes",
            str(params["stride_bytes"]),
            "--iterations",
            str(params["iterations"]),
            "--sleep-ms",
            str(params["sleep_ms"]),
            "--seed",
            str(spec.deterministic_controls.get("seed", 7)),
            "--repeat-count",
            str(spec.deterministic_controls.get("repeat_count", 3)),
        ], self.store.run_dir(run_id) / "compile.log")

    def _environment_snapshot(self) -> dict[str, str]:
        return {
            "python": sys.version.split()[0],
            "cwd": str(self.layout.root),
            "pid": str(os.getpid()),
        }


@dataclass(slots=True)
class Analyzer:
    codex: CodexClient
    store: AppendOnlyStore
    workflow: WorkflowDefinition

    def analyze(self, question: ResearchQuestion, spec: ExperimentSpec, run: RunRecord) -> tuple[ObservationRecord, ClaimRecord]:
        if run.exit_code != 0:
            raise RuntimeError(f"Execution failed for run {run.id}")

        raw_text = Path(run.artifact_paths["stdout"]).read_text(encoding="utf-8")
        payload = json.loads(raw_text)
        if spec.benchmark_type == "cuda_memory_hierarchy_probe":
            metrics = {
                "estimated_bandwidth_gb_s": payload["estimated_bandwidth_gb_s"],
                "avg_elapsed_ms": payload["avg_elapsed_ms"],
                "working_set_kb": payload["working_set_kb"],
                "stride_bytes": payload["stride_bytes"],
                "repeat_count": payload["repeat_count"],
                "threads_per_block": payload["threads_per_block"],
                "blocks": payload["blocks"],
            }
            default_claim = {
                "statement": (
                    f"For working set {payload['working_set_kb']} KB and stride {payload['stride_bytes']} bytes, "
                    f"the CUDA memory probe measured {payload['estimated_bandwidth_gb_s']} GB/s "
                    f"over {payload['repeat_count']} timed launches."
                ),
                "confidence": "medium",
                "support_summary": "Bounded CUDA probe completed successfully and produced repeatable timing output in one run.",
                "counterevidence": [],
            }
        else:
            metrics = {
                "throughput_score": payload["throughput_score"],
                "mean_latency_ms": payload["mean_latency_ms"],
                "working_set_kb": payload["working_set_kb"],
                "stride_bytes": payload["stride_bytes"],
                "repeat_count": payload["repeat_count"],
            }
            default_claim = {
                "statement": (
                    f"For working set {payload['working_set_kb']} KB and stride {payload['stride_bytes']} bytes, "
                    f"the synthetic probe reports throughput {payload['throughput_score']} with bounded latency."
                ),
                "confidence": "medium",
                "support_summary": "Observed deterministic output across repeated trials in one bounded run.",
                "counterevidence": [],
            }
        observation = ObservationRecord(
            run_id=run.id,
            spec_id=spec.id,
            parser_version=PARSER_VERSION,
            metrics=metrics,
            evidence_paths=[run.artifact_paths["stdout"], run.artifact_paths["spec"]],
        )
        observation.validate()
        profile = self.workflow.profile("analyzer")
        result = self.codex.invoke_json(
            role="analyzer",
            instructions=profile.instructions,
            payload=self.workflow.render_payload(
                "analyzer",
                {
                    "question": to_plain_data(question),
                    "spec": to_plain_data(spec),
                    "observation_metrics": metrics,
                    "raw_output": payload,
                    "workflow_constraints": workflow_constraints(),
                    "defaults": default_claim,
                },
            ),
            output_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "statement": {"type": "string"},
                    "confidence": {"type": "string"},
                    "support_summary": {"type": "string"},
                    "counterevidence": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["statement", "confidence", "support_summary", "counterevidence"],
            },
            fallback_output=default_claim,
            sandbox_mode=profile.sandbox_mode,
            web_search_enabled=profile.web_search_enabled,
        )
        claim_payload = result.output
        claim = ClaimRecord(
            question_id=question.id,
            spec_id=spec.id,
            observation_id=observation.id,
            statement=str(claim_payload.get("statement", default_claim["statement"])),
            status="candidate",
            confidence=str(claim_payload.get("confidence", default_claim["confidence"])),
            support_summary=str(claim_payload.get("support_summary", default_claim["support_summary"])),
            counterevidence=list(claim_payload.get("counterevidence", [])),
            provenance_paths=[run.artifact_paths["stdout"], run.artifact_paths["spec"]],
        )
        claim.validate()

        self.store.write_run_artifact(run.id, "analysis.json", json.dumps(
            {
                "observation": to_plain_data(observation),
                "claim": to_plain_data(claim),
                "agent_backend": result.backend,
                "thread_id": result.thread_id,
                "usage": result.usage,
            },
            indent=2,
            sort_keys=True,
        ))
        self.store.write_run_artifact(run.id, "analysis_events.jsonl", _events_to_jsonl(result.events))
        return observation, claim


@dataclass(slots=True)
class Verifier:
    layout: WorkspaceLayout
    store: AppendOnlyStore
    codex: CodexClient
    workflow: WorkflowDefinition

    def verify(self, spec: ExperimentSpec, run: RunRecord, claim: ClaimRecord) -> VerificationRecord:
        rerun = RunRecord(
            spec_id=spec.id,
            question_id=run.question_id,
            command=run.command,
            artifact_paths={},
            elapsed_seconds=0.0,
            exit_code=-1,
            environment=run.environment,
        )
        start = time.perf_counter()
        try:
            result = subprocess.run(
                rerun.command,
                cwd=str(self.layout.root),
                capture_output=True,
                text=True,
                check=False,
                timeout=spec.budget_seconds,
            )
            rerun_stdout_text = result.stdout
            rerun_stderr_text = result.stderr
            rerun_exit_code = result.returncode
        except subprocess.TimeoutExpired as exc:
            rerun_stdout_text = exc.stdout or ""
            rerun_stderr_text = (exc.stderr or "") + "\nVerification rerun timed out."
            rerun_exit_code = 124
        rerun.elapsed_seconds = time.perf_counter() - start
        rerun.exit_code = rerun_exit_code
        rerun_stdout = self.store.write_run_artifact(rerun.id, "stdout.json", rerun_stdout_text)
        rerun_stderr = self.store.write_run_artifact(rerun.id, "stderr.txt", rerun_stderr_text)
        rerun.artifact_paths = {
            "stdout": str(rerun_stdout),
            "stderr": str(rerun_stderr),
        }
        rerun.validate()
        self.store.append_jsonl("runs", rerun)

        if rerun.exit_code != 0:
            verification = VerificationRecord(
                claim_id=claim.id,
                spec_id=spec.id,
                method="independent_rerun",
                result="pending",
                notes="Verification rerun did not complete successfully.",
                evidence_paths=[str(rerun_stdout), str(rerun_stderr)],
                rerun_run_id=rerun.id,
            )
            verification.validate()
            return verification

        result_payload = json.loads(rerun_stdout_text)
        baseline_payload = json.loads(Path(run.artifact_paths["stdout"]).read_text(encoding="utf-8"))
        if spec.benchmark_type == "cuda_memory_hierarchy_probe":
            primary_metric = "estimated_bandwidth_gb_s"
            baseline_value = float(baseline_payload[primary_metric])
            rerun_value = float(result_payload[primary_metric])
            metric_delta = abs(rerun_value - baseline_value)
            relative_delta = metric_delta / max(abs(baseline_value), 1e-9)
            default_verification = {
                "result": "accepted" if relative_delta < 0.05 else "pending",
                "notes": (
                    f"Independent rerun matched the original bandwidth signal within 5% (relative_delta={relative_delta:.6f})."
                    if relative_delta < 0.05
                    else f"Rerun bandwidth drift was {relative_delta:.6f}; keep the claim pending."
                ),
            }
        else:
            primary_metric = "throughput_score"
            baseline_value = float(baseline_payload[primary_metric])
            rerun_value = float(result_payload[primary_metric])
            metric_delta = abs(rerun_value - baseline_value)
            relative_delta = metric_delta / max(abs(baseline_value), 1e-9)
            default_verification = {
                "result": "accepted" if metric_delta < 1e-6 else "pending",
                "notes": (
                    "Independent rerun matched the initial throughput signal."
                    if metric_delta < 1e-6
                    else "Rerun drift exceeded deterministic tolerance; keep the claim pending."
                ),
            }
        profile = self.workflow.profile("verifier")
        agent_result = self.codex.invoke_json(
            role="verifier",
            instructions=profile.instructions,
            payload=self.workflow.render_payload(
                "verifier",
                {
                    "spec": to_plain_data(spec),
                    "claim": to_plain_data(claim),
                    "baseline_metrics": baseline_payload,
                    "rerun_metrics": result_payload,
                    "throughput_delta": metric_delta,
                    "relative_delta": relative_delta,
                    "primary_metric": primary_metric,
                    "workflow_constraints": workflow_constraints(),
                    "defaults": default_verification,
                },
            ),
            output_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "result": {"type": "string", "enum": ["accepted", "disputed", "pending"]},
                    "notes": {"type": "string"},
                },
                "required": ["result", "notes"],
            },
            fallback_output=default_verification,
            sandbox_mode=profile.sandbox_mode,
            web_search_enabled=profile.web_search_enabled,
        )
        verification = VerificationRecord(
            claim_id=claim.id,
            spec_id=spec.id,
            method="independent_rerun",
            result=str(agent_result.output["result"]),
            notes=str(agent_result.output["notes"]),
            evidence_paths=[str(rerun_stdout), run.artifact_paths["stdout"]],
            rerun_run_id=rerun.id,
        )
        verification.validate()
        self.store.write_run_artifact(
            run.id,
            "verification.json",
            json.dumps(
                {
                    "verification": to_plain_data(verification),
                    "backend": agent_result.backend,
                    "thread_id": agent_result.thread_id,
                    "usage": agent_result.usage,
                    "primary_metric": primary_metric,
                    "metric_delta": metric_delta,
                    "relative_delta": relative_delta,
                },
                indent=2,
                sort_keys=True,
            ),
        )
        self.store.write_run_artifact(run.id, "verification_events.jsonl", _events_to_jsonl(agent_result.events))
        return verification


@dataclass(slots=True)
class Curator:
    store: AppendOnlyStore
    codex: CodexClient
    workflow: WorkflowDefinition

    def curate(
        self,
        question: ResearchQuestion,
        spec: ExperimentSpec,
        run: RunRecord,
        observation: ObservationRecord,
        claim: ClaimRecord,
        verification: VerificationRecord,
        *,
        continuation_context: dict,
    ) -> WorkflowProposal:
        if verification.result == "accepted":
            claim.status = "accepted"
        elif verification.result == "disputed":
            claim.status = "disputed"
        else:
            claim.status = "pending"
        claim.validate()

        default_proposal = {
            "bottleneck": "Only one synthetic benchmark family is active.",
            "proposal": "Add a CUDA-backed experiment handler next while preserving the same append-only record model.",
            "expected_gain": "Increase relevance to real GPU architecture measurements.",
            "risk": "CUDA toolchain differences may reduce determinism or portability.",
            "rollback_condition": "Keep the synthetic handler as the default fallback if CUDA execution fails.",
            "approval_state": "proposed",
            "target_workflow_version": self.workflow.version,
            "proposed_profile_updates": [],
            "continue_recommended": True,
            "stop_reason": None,
        }
        profile = self.workflow.profile("next_step")
        agent_result = self.codex.invoke_json(
            role="next_step",
            instructions=profile.instructions,
            payload=self.workflow.render_payload(
                "next_step",
                {
                    "question": to_plain_data(question),
                    "spec": to_plain_data(spec),
                    "claim": to_plain_data(claim),
                    "verification": to_plain_data(verification),
                    "continuation_context": continuation_context,
                    "workflow_constraints": workflow_constraints(),
                    "defaults": default_proposal,
                },
            ),
            output_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "bottleneck": {"type": "string"},
                    "proposal": {"type": "string"},
                    "expected_gain": {"type": "string"},
                    "risk": {"type": "string"},
                    "rollback_condition": {"type": "string"},
                    "approval_state": {"type": "string"},
                    "target_workflow_version": {"type": ["string", "null"]},
                    "continue_recommended": {"type": "boolean"},
                    "stop_reason": {"type": ["string", "null"]},
                    "proposed_profile_updates": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "role": {"type": "string"},
                                "reason": {"type": "string"},
                                "context_sections": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "web_search_enabled": {"type": "boolean"},
                                "sandbox_mode": {"type": "string"},
                                "instruction_note": {"type": "string"},
                            },
                            "required": [
                                "role",
                                "reason",
                                "context_sections",
                                "web_search_enabled",
                                "sandbox_mode",
                                "instruction_note",
                            ],
                        },
                    },
                },
                "required": [
                    "bottleneck",
                    "proposal",
                    "expected_gain",
                    "risk",
                    "rollback_condition",
                    "approval_state",
                    "target_workflow_version",
                    "continue_recommended",
                    "stop_reason",
                    "proposed_profile_updates",
                ],
            },
            fallback_output=default_proposal,
            sandbox_mode=profile.sandbox_mode,
            web_search_enabled=profile.web_search_enabled,
        )
        proposal = WorkflowProposal(
            bottleneck=str(agent_result.output["bottleneck"]),
            proposal=str(agent_result.output["proposal"]),
            expected_gain=str(agent_result.output["expected_gain"]),
            risk=str(agent_result.output["risk"]),
            rollback_condition=str(agent_result.output["rollback_condition"]),
            approval_state=str(agent_result.output["approval_state"]),
            target_workflow_version=agent_result.output.get("target_workflow_version"),
            proposed_profile_updates=list(agent_result.output.get("proposed_profile_updates", [])),
            continue_recommended=bool(agent_result.output.get("continue_recommended", True)),
            stop_reason=agent_result.output.get("stop_reason"),
        )
        proposal.validate()
        self.store.write_plan_artifact(
            spec.id,
            "next_step.json",
            json.dumps(
                {
                    "proposal": to_plain_data(proposal),
                    "backend": agent_result.backend,
                    "thread_id": agent_result.thread_id,
                    "usage": agent_result.usage,
                },
                indent=2,
                sort_keys=True,
            ),
        )
        self.store.write_plan_artifact(spec.id, "next_step_events.jsonl", _events_to_jsonl(agent_result.events))
        self.store.append_round(question, spec, run, observation, claim, verification, proposal)
        return proposal


def build_roles(layout: WorkspaceLayout) -> tuple[Planner, Executor, Analyzer, Verifier, Curator]:
    store = AppendOnlyStore(layout)
    store.init_workspace()
    codex = CodexClient(layout=layout, model=DEFAULT_MODEL)
    workflow = load_workflow_definition()
    return (
        Planner(store=store, codex=codex, workflow=workflow),
        Executor(layout=layout, store=store),
        Analyzer(codex=codex, store=store, workflow=workflow),
        Verifier(layout=layout, store=store, codex=codex, workflow=workflow),
        Curator(store=store, codex=codex, workflow=workflow),
    )


def _events_to_jsonl(events: list[dict]) -> str:
    if not events:
        return ""
    return "".join(json.dumps(event, sort_keys=True) + "\n" for event in events)
