from __future__ import annotations

import sys

from .config import WorkspaceLayout
from .schemas import ResearchRoundResult
from .session import build_continuation_context
from .store import AppendOnlyStore
from .site import rebuild_site
from .roles import build_roles


def _log(message: str) -> None:
    print(f"[gpuarchitect] {message}", file=sys.stderr)


def run_research_round(
    layout: WorkspaceLayout,
    question_text: str | None,
    *,
    operator_directive: str | None = None,
) -> ResearchRoundResult:
    _log(f"starting_round root={layout.root}")
    store = AppendOnlyStore(layout)
    store.init_workspace()
    continuation_context = build_continuation_context(store)
    planner, executor, analyzer, verifier, curator = build_roles(layout)
    _log("stage=planner status=started")
    question, spec = planner.plan(question_text, continuation_context=continuation_context, operator_directive=operator_directive)
    _log(f"stage=planner status=completed question_id={question.id} spec_id={spec.id}")
    _log("stage=executor status=started")
    run = executor.run(question, spec)
    _log(f"stage=executor status=completed run_id={run.id} exit_code={run.exit_code} elapsed={run.elapsed_seconds:.4f}s")
    _log("stage=analyzer status=started")
    observation, claim = analyzer.analyze(question, spec, run)
    _log(f"stage=analyzer status=completed observation_id={observation.id} claim_id={claim.id}")
    _log("stage=verifier status=started")
    verification = verifier.verify(spec, run, claim)
    _log(f"stage=verifier status=completed verification_id={verification.id} result={verification.result}")
    _log("stage=curator status=started")
    next_step = curator.curate(
        question,
        spec,
        run,
        observation,
        claim,
        verification,
        continuation_context=build_continuation_context(store),
    )
    _log(f"stage=curator status=completed workflow_proposal_id={next_step.id}")
    _log("stage=site status=started")
    rebuild_site(layout)
    _log("stage=site status=completed")
    return ResearchRoundResult(
        question=question,
        spec=spec,
        run=run,
        observation=observation,
        claim=claim,
        verification=verification,
        next_step=next_step,
    )
