from __future__ import annotations

import json

from gpu_research_agent.config import WorkspaceLayout
from gpu_research_agent.loop import run_research_round


def test_full_round_generates_records_and_site(tmp_path) -> None:
    layout = WorkspaceLayout(root=tmp_path)
    result = run_research_round(layout, "How does the synthetic probe behave?")

    assert result.run.exit_code == 0
    assert result.claim.status in {"accepted", "pending"}
    assert (layout.site_dir / "index.html").exists()
    assert (layout.exports_dir / "knowledge.yaml").exists()
    assert (layout.knowledge_dir / "index.md").exists()

    runs_path = layout.records_dir / "runs.jsonl"
    assert runs_path.exists()
    lines = runs_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    first_run = json.loads(lines[0])
    assert first_run["spec_id"] == result.spec.id
