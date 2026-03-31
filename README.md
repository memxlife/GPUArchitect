# GPUArchitect

GPUArchitect is a local-first scaffold for a single-GPU research loop focused on reproducible microbenchmarking, evidence-backed claims, append-only knowledge curation, and Codex-SDK-driven agent roles.

The current implementation delivers a minimal but complete vertical slice:

- plan one research question into a structured experiment spec
- execute one bounded benchmark run
- parse raw evidence into observations
- analyze and draft a claim candidate
- verify the claim independently
- append records into a local knowledge base
- generate a static dashboard plus YAML export
- route planner, analyzer, verifier, and next-step proposal tasks through the Codex SDK when API credentials are available

## Project Layout

- `src/gpu_research_agent/`: orchestration, schemas, storage, CLI, and site generation
- `agent_runtime/`: workspace-local Codex SDK runtime used by research roles
- `workflow/`: active workflow definition, including per-agent input structure and capability flags
- `tests/`: unit and workflow tests
- `prompt.md`: product brief and constraints
- `data/`: append-only runtime records and run artifacts
- `knowledge/`: generated Markdown knowledge base
- `exports/`: generated YAML export
- `site/`: generated static dashboard

## Quick Start

1. Install Python dependencies:

```bash
uv pip install -e .
```

2. Install the local Codex runtime dependencies:

```bash
npm install --prefix agent_runtime
```

3. Initialize local workspace directories:

```bash
gpuarchitect init
```

4. Run one research round:

```bash
gpuarchitect run-round --question "How does the synthetic memory probe react to larger working sets?"
```

5. Inspect outputs:

```bash
gpuarchitect status
gpuarchitect rebuild-site
```

During execution, progress and backend details are printed to `stderr` so you can monitor the active stage without breaking the JSON result emitted on `stdout`.

## Runtime Model

The system always keeps the same workflow stages:

1. select a question
2. create a falsifiable hypothesis and experiment spec
3. execute a deterministic benchmark within budget
4. persist raw observations
5. analyze evidence into structured findings
6. verify with an independent rerun or counter-check
7. append records to the knowledge base
8. plan the next step

Source-of-truth records are append-only inside `data/records/` and `data/runs/`. Generated Markdown, YAML, and HTML can be rebuilt at any time from those records.

## LLM Integration

The scaffold prefers the Codex SDK for agent roles. Planner, analyzer, verifier, and next-step proposal run through the workspace-local Node runtime when either `CODEX_API_KEY` or `OPENAI_API_KEY` is configured and the `agent_runtime/` dependencies are installed.

When credentials or runtime dependencies are unavailable, the system falls back to deterministic local defaults so the workflow, tests, and append-only record model still operate.

If environment variables are not set, the runtime also checks `~/.codex/auth.json` for `CODEX_API_KEY` or `OPENAI_API_KEY`.

## Workflow-Configured Agent Inputs

Agent instructions and input structure are not hardcoded only in Python. The active workflow lives in `workflow/active.yaml`, where each role declares:

- instructions
- ordered `context_sections`
- sandbox mode
- web-search enablement

Each run snapshots the active workflow into `data/plans/<spec_id>/workflow_snapshot.yaml`. Workflow proposals may include `proposed_profile_updates` so the system can propose changes to agent input structure inside the workflow itself, without auto-applying them.

## Knowledge Base vs History

These are intentionally different products:

- `data/`: append-only operational history, raw plans, runs, records, and verification traces
- `knowledge/` and `exports/knowledge.yaml`: curated knowledge outputs derived from history

The history is the source of truth. The knowledge base is a derived, human/agent-facing view.

## Commands

- `gpuarchitect init`
- `gpuarchitect run-round --question "..."`
- `gpuarchitect verify-claim --claim-id <id>`
- `gpuarchitect rebuild-site`
- `gpuarchitect status`
- `gpuarchitect show-workflow`

## Safety And Limits

- run time per experiment is bounded by the spec timeout
- the default round budget is 120 seconds
- verification is always a separate stage from analysis
- raw evidence is written before claims are promoted
- records are never updated in place in the append-only store

## Current Benchmark

The initial vertical slice uses a deterministic synthetic probe so the full research loop works on any machine. The executor and parser are structured so real CUDA microbenchmarks can replace or extend the sample benchmark without changing the core loop.

## Current Limits

- the benchmark path is still synthetic rather than CUDA-backed
- verifier support for external sources is limited to what the Codex role can inspect in one turn
- there is no daemonized multi-round scheduler yet
