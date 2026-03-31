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

Planner input can include:

- a new operator-supplied question
- an operator continuation directive
- continuation context assembled from prior rounds
- available experiment families

This makes repeated rounds resumable from workspace state rather than tied to the original coding session.

### 3. Agent Runtime

`agent_runtime/codex_runner.mjs` runs Codex SDK turns inside the workspace. Python invokes it through `src/gpu_research_agent/codex_client.py`.

The runtime records:

- thread id
- streamed events
- final structured output
- usage

Planner uses non-streamed turn execution in the Codex runtime so planner web search can stay enabled while keeping result handling stable.

### 4. Execution Layer

`Executor` runs deterministic local benchmarks under explicit timeout bounds. The current implementation includes:

- a synthetic fallback probe
- one real CUDA-backed family: `cuda_memory_hierarchy_probe`

The family supplies the execution template and bounded parameter space. The agent still chooses the concrete question and parameterization per round.

### 5. History Layer

`data/` is append-only operational history.

- `data/plans/`: question/spec snapshots, workflow snapshot, planner output, workflow proposals
- `data/runs/`: raw stdout/stderr, analysis record, verification record, rerun artifacts
- `data/records/*.jsonl`: append-only structured logs
- `data/control/session_state.json`: mutable loop-control state used for pause/resume

This layer is the provenance source of truth.

### 6. Knowledge Layer

`knowledge/` and `exports/knowledge.yaml` are curated outputs derived from history.

They are not the source of truth and may be rebuilt from append-only records at any time.

### 7. Presentation Layer

`site/index.html` is a generated dashboard showing workflow state, counts, and recent outputs. It explicitly distinguishes knowledge outputs from append-only history.

## Multi-Round Operation

The system supports both:

- manual one-round execution
- resumable multi-round execution

Control behavior:

- `run-round` executes one round
- `run-round` without a new question continues from prior workspace context
- `run-loop --rounds N` executes a fixed number of rounds
- `run-loop --auto` keeps running until the workflow recommends stopping or a human interrupts it

Interruption is expected. A human can stop the process and later continue from the same workspace because continuation context is rebuilt from append-only history plus mutable session control state.

## Why Knowledge And History Are Separate

The prompt requires both observability and usable outputs for humans and downstream agents. Those needs conflict if they are stored as the same thing:

- history must be complete, raw, append-only, and provenance-rich
- knowledge must be compact, curated, and readable

So the system keeps raw evidence and operation history in `data/`, while exposing derived knowledge in `knowledge/` and `exports/knowledge.yaml`.

## Current Limits

- only one real CUDA/profiler-backed family is implemented so far
- workflow proposals are recorded but not automatically approved or merged
- no kernel backtesting loop yet
