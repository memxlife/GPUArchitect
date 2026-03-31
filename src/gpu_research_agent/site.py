from __future__ import annotations

from html import escape

from .config import WorkspaceLayout
from .store import AppendOnlyStore


STYLE = """
body {
  font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
  margin: 0;
  background: linear-gradient(180deg, #f6f2ea 0%, #fffaf4 100%);
  color: #1b1f23;
}
main {
  max-width: 980px;
  margin: 0 auto;
  padding: 48px 24px 64px;
}
h1, h2 {
  letter-spacing: -0.03em;
}
.hero {
  background: #11212d;
  color: #f3efe7;
  border-radius: 20px;
  padding: 28px;
  margin-bottom: 28px;
}
.panel {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid #dfd2bd;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 18px;
}
code, pre {
  font-family: "IBM Plex Mono", monospace;
}
pre {
  overflow-x: auto;
  background: #f7f1e5;
  padding: 16px;
  border-radius: 12px;
}
ul {
  padding-left: 20px;
}
a {
  color: #8b3d12;
}
"""


def rebuild_site(layout: WorkspaceLayout) -> None:
    store = AppendOnlyStore(layout)
    store.rebuild_exports()

    runs = store.load_jsonl("runs")
    questions = store.load_jsonl("questions")
    specs = store.load_jsonl("specs")
    claims = store.load_jsonl("claims")
    verifications = store.load_jsonl("verifications")
    proposals = store.load_jsonl("workflow_proposals")

    accepted_claims = sum(1 for claim in claims if claim["status"] == "accepted")
    pending_claims = sum(1 for claim in claims if claim["status"] == "pending")
    disputed_claims = sum(1 for claim in claims if claim["status"] == "disputed")

    workflow_graph = """Select Question
  -> Create Hypothesis
  -> Build Spec
  -> Execute Benchmark
  -> Extract Observations
  -> Analyze Claim Candidate
  -> Verify Independently
  -> Curate Knowledge
  -> Plan Next Step"""

    latest_runs = "\n".join(
        f"<li><strong>{escape(run['id'])}</strong> exit={run['exit_code']} elapsed={run['elapsed_seconds']:.4f}s</li>"
        for run in runs[-5:]
    ) or "<li>No runs yet</li>"

    latest_claims = "\n".join(
        f"<li><a href=\"../knowledge/claims/{escape(claim['id'])}.md\">{escape(claim['id'])}</a>: {escape(claim['statement'])}</li>"
        for claim in claims[-5:]
    ) or "<li>No claims yet</li>"

    latest_proposals = "\n".join(
        f"<li>{escape(item['proposal'])}</li>"
        for item in proposals[-3:]
    ) or "<li>No workflow proposals yet</li>"

    verification_count = len(verifications)

    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>GPUArchitect Dashboard</title>
    <style>{STYLE}</style>
  </head>
  <body>
    <main>
      <section class="hero">
        <h1>GPUArchitect</h1>
        <p>Append-only research loop for bounded GPU microbenchmarking and evidence-backed claims.</p>
      </section>
      <section class="panel">
        <h2>Status</h2>
        <ul>
          <li>Total runs: {len(runs)}</li>
          <li>Total questions: {len(questions)}</li>
          <li>Total experiment specs: {len(specs)}</li>
          <li>Accepted claims: {accepted_claims}</li>
          <li>Pending claims: {pending_claims}</li>
          <li>Disputed claims: {disputed_claims}</li>
          <li>Verification records: {verification_count}</li>
        </ul>
      </section>
      <section class="panel">
        <h2>Data Model</h2>
        <ul>
          <li>Knowledge base: curated claim documents in <code>knowledge/</code> plus <code>exports/knowledge.yaml</code>.</li>
          <li>Append-only history: raw plans, runs, records, and verification traces in <code>data/</code>.</li>
        </ul>
      </section>
      <section class="panel">
        <h2>Workflow Graph</h2>
        <pre>{escape(workflow_graph)}</pre>
      </section>
      <section class="panel">
        <h2>Recent Runs</h2>
        <ul>{latest_runs}</ul>
      </section>
      <section class="panel">
        <h2>Recent Claims</h2>
        <ul>{latest_claims}</ul>
      </section>
      <section class="panel">
        <h2>Next Workflow Proposals</h2>
        <ul>{latest_proposals}</ul>
      </section>
    </main>
  </body>
</html>
"""
    (layout.site_dir / "index.html").write_text(html, encoding="utf-8")
