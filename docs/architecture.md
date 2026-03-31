# GPUArchitect Architecture

## Purpose

GPUArchitect is a local-first, single-GPU research workflow scaffold. It separates:

- workflow control
- bounded execution
- append-only historical records
- curated knowledge outputs
- Codex-backed agent reasoning

## Core Subsystems

### 1. Workflow Control

`src/gpu_research_agent/loop.py` executes the invariant research stages:

1. select question
2. form hypothesis
3. generate experiment spec
4. execute bounded benchmark
5. extract observations
6. analyze claim candidate
7. verify independently
8. curate knowledge
9. propose next step

### 2. Workflow Definition

`workflow/active.yaml` is the active workflow definition. It declares, per role:

- instructions
- input structure through ordered `context_sections`
- sandbox mode
- web-search enablement

This lets agent input structure evolve through workflow proposals rather than requiring code edits for every change.

### 3. Agent Runtime

`agent_runtime/codex_runner.mjs` runs Codex SDK turns inside the workspace. Python invokes it through `src/gpu_research_agent/codex_client.py`.

The runtime records:

- thread id
- streamed events
- final structured output
- usage

### 4. Execution Layer

`Executor` runs deterministic local benchmarks under explicit timeout bounds. The current implementation uses a synthetic probe as a placeholder for future CUDA-backed experiment families.

### 5. History Layer

`data/` is append-only operational history.

- `data/plans/`: question/spec snapshots, workflow snapshot, planner output, workflow proposals
- `data/runs/`: raw stdout/stderr, analysis record, verification record, rerun artifacts
- `data/records/*.jsonl`: append-only structured logs

This layer is the provenance source of truth.

### 6. Knowledge Layer

`knowledge/` and `exports/knowledge.yaml` are curated outputs derived from history.

They are not the source of truth and may be rebuilt from append-only records at any time.

### 7. Presentation Layer

`site/index.html` is a generated dashboard showing workflow state, counts, and recent outputs. It explicitly distinguishes knowledge outputs from append-only history.

## Why Knowledge And History Are Separate

The prompt requires both observability and usable outputs for humans and downstream agents. Those needs conflict if they are stored as the same thing:

- history must be complete, raw, append-only, and provenance-rich
- knowledge must be compact, curated, and readable

So the system keeps raw evidence and operation history in `data/`, while exposing derived knowledge in `knowledge/` and `exports/knowledge.yaml`.

## Current Limits

- no CUDA/profiler-backed experiment family yet
- no long-running scheduler yet
- no workflow proposal approval/merge engine yet
- no kernel backtesting loop yet
