# GPU Architecture Research Agent: Coding Agent Build Prompt

Build a local-first, single-GPU autonomous research system for GPU architecture reverse engineering and kernel optimization. The system should use documentation, examples, profiling benchmarks, and iterative analysis to produce reproducible, evidence-backed claims about GPU behavior, then organize those claims into a structured knowledge base that is useful for both humans and downstream agents.

The goal is not only to run experiments, but to maintain a long-running research loop with explicit records, deterministic execution where possible, clear provenance, and room for controlled self-improvement. Human supervision must remain possible at all times.

## Core Objectives

### Primary Objective
- Produce reproducible and evidence-traceable claims about GPU architecture, and accumulate them into a knowledge base.

### Secondary Objective
- Use those claims to improve kernel generation, scheduling, and performance-oriented operator design.

### Tertiary Objective
- Improve the research system itself so it becomes more effective over time.

## Research Scope

Focus on a single GPU on a single machine. The current scope includes:
- Memory hierarchy
- Warp scheduling
- Tensor core behavior
- Occupancy and register pressure
- Cache and shared memory behavior
- Topology and interconnect characteristics that are observable at single-card scope
- Other low-level GPU traits worth exploring, such as low-precision behavior, if the system can justify them through planning
- High-level operator behavior and the low-level mechanisms behind operator optimizations such as FlashAttention-like techniques

The system may use prior knowledge gathered from external research and documentation to choose practical research directions.

Out of scope for now:
- Multi-GPU and distributed research
- End-to-end large-model training or inference system studies above the single-card operator level

## Product Philosophy

The system should be a multi-agent research loop that includes testing, evaluation, analysis, search, and documentation. It should be able to improve parts of its own workflow, but must not remove the core loop structure.

The process must be observable and well recorded. It should not rely only on loose LLM instruction-following. Deterministic benchmark generation, profiling, analysis planning, and append-only record keeping should be first-class parts of the design.

The output should include documentation that is both:
- Machine-friendly
- Human-readable

It is desirable to provide:
- A structured Markdown knowledge base
- A YAML export for agent consumption
- A dashboard for current status, workflow structure, and progress summaries
- A website, for example using VitePress or a custom static site, to present the dashboard and knowledge base

It is also desirable to include a kernel backtesting loop: under a fixed budget, use the current knowledge base to generate kernels, evaluate them, and compare the results with broader internet-informed approaches.

## Non-Negotiable Constraints

- Real history must be preserved strictly. Records may be appended and versioned, but not overwritten destructively.
- Every meaningful version must be stored in git.
- Execution is limited to the workspace. CUDA, Python, and bash scripts for launching, running, and profiling are allowed only within that boundary.
- No out-of-scope access or unauthorized modification is allowed.
- Profiling kernel runtime and analysis input sizes must be strictly bounded to avoid deadlocks, GPU hangs, or runaway agent behavior.
- The workflow and agent roles may evolve, but the iterative loop must always remain present.
- Human supervision and correction interfaces must remain available.

## Self-Improvement Boundaries

The system may freely modify:
- Prompts
- Research strategy
- Experiment ranking
- Documentation organization
- Non-destructive extensions to the claim schema

The system may propose, but must not directly apply without dedicated evaluation:
- Agent topology
- Execution flow
- Evaluator weights
- Benchmark synthesis policy
- UI structure

The system must never self-modify:
- Core safety constraints
- Provenance, versioning, and append-only principles
- Raw observation records
- Human-defined resource boundaries
- The root objective function

## Workflow Invariants

Every valid workflow version must contain all of the following stages and may not skip them:

1. Select a question or target
2. Form a falsifiable hypothesis or claim candidate
3. Generate a structured experiment specification
4. Deterministically write and run benchmark and profiling code
5. Extract raw observations
6. Analyze the observations and update claim status or confidence
7. Independently verify, replicate, or refute
8. Write results to the knowledge base and logs in append-only form
9. Plan the next step or propose a workflow modification

Additional invariants:
- Any workflow evolution must still map cleanly to this minimum state machine.
- Analysis and claim generation must not be merged with verification and approval into a single step.
- Final claims must never be written directly from execution output without preserving raw observations first.
- Workflow self-modification must not bypass these invariants.

## Initial Logical Roles

The initial version should preserve these logical roles, even if one implementation agent temporarily covers multiple roles:

### Planner
- Choose research questions
- Propose hypotheses or claim candidates
- Design experiment specifications

### Executor
- Generate benchmark and profiling code
- Compile, run, and collect raw results
- Save full run logs and environment metadata

### Analyzer
- Extract structured observations from raw results
- Analyze whether observations support or weaken the hypothesis
- Generate structured analysis records

### Verifier
- Re-run, challenge, and design counter-experiments
- Resolve conflicts with important external sources or high-confidence prior knowledge
- Decide whether a claim should be accepted, disputed, or kept pending

### Curator
- Append results to the knowledge base, logs, and dashboard index
- Maintain provenance and versioning
- Record workflow modification proposals and their evaluations

The number of agents, topology, and implementation may change later, but these logical responsibilities must not disappear entirely.

## Workflow Upgrade Rules

Workflow changes must be represented as explicit proposals that include:
- Current bottleneck
- Proposed modification
- Expected gain
- Risks
- Rollback conditions

A workflow upgrade may be merged only if it:
- Preserves workflow invariants
- Preserves provenance, versioning, and append-only principles
- Improves at least one of the following under a fixed budget:
  - Success rate
  - Information gain
  - Research efficiency
  - Kernel backtesting effectiveness
- Is rollbackable

The following changes must not be auto-merged and should normally require explicit human confirmation:
- Removing verifier or curator responsibilities
- Changing acceptance rules for accepted knowledge
- Changing resource budgets
- Changing core safety constraints
- Changing the root objective function

## Acceptance Criteria Per Research Loop

### Valid Claim
- A claim must be clear, specific, and testable.
- It must contain a judgment or measurable target that can be supported or falsified through a deterministic experiment.

### Valid Experiment
- An experiment must include test code derived from the claim and current knowledge.
- It must produce interpretable and unambiguous outputs through profiling, program output, or both.
- It should reduce noise from system variation using techniques such as repeated trials, controlled seeds, and stable execution settings where applicable.

### Valid Analysis
- The analysis must produce structured text and records that become part of the knowledge graph or knowledge base.
- It must also determine the next experiment or planning direction.

## Required Deliverables

Build the project so it can generate and maintain:
- A Markdown knowledge base organized through folders and index pages
- A YAML representation of knowledge for LLM or agent consumption
- A dashboard showing research progress, brief status, and the current workflow graph
- A website that exposes the dashboard and structured knowledge base content

## Runtime Environment

Assume:
- Local machine
- Single GPU
- Long-running execution
- Internet access allowed for search and external reference gathering
- The current Python virtual environment may be used
- `uv pip` may be used to install necessary Python packages inside the project workflow
- CUDA profiling tools may be used
- `npm` may be used to install necessary workspace-local web tooling

Do not:
- Modify system configuration
- Install system-level packages or environments

## Per-Round Budget

- Total GPU runtime per round must not exceed 120 seconds
- Each AI agent request must not exceed 180 seconds, except for explicit deep research calls if those are implemented separately

## Failure Model

- If a benchmark run fails, treat it as low-cost: fix or rewrite and retry
- If a claim strongly conflicts with important sources such as NVIDIA documentation, inspect possible error sources, repeat once, and if conflict remains, mark it clearly in the documentation and skip promotion
- If a claim cannot be validated, mark it and skip it

## Engineering Requirements

Build an initial project scaffold that makes this system practical to implement and extend. Prefer a clean monorepo or well-structured single repository with clear boundaries between:
- Agent orchestration
- Experiment specifications
- Benchmark and profiling execution
- Result parsing and analysis
- Knowledge base storage
- Dashboard or website presentation
- Configuration, budgets, and policy constraints

The codebase should make append-only records and provenance easy to enforce. It should also make it easy to:
- Add new experiment types
- Add or replace agent implementations
- Track claim lifecycle states such as candidate, accepted, disputed, and pending
- Store raw observations separately from interpreted claims
- Re-run experiments deterministically when possible

## Suggested First Build Milestone

Implement a minimal but complete vertical slice:

1. A planner can create a structured experiment spec from a research question.
2. An executor can run a bounded benchmark or profiling task and save raw outputs.
3. An analyzer can convert raw outputs into structured observations.
4. A verifier can record an initial verification decision.
5. A curator can append all artifacts into a versioned local knowledge base.
6. A simple dashboard or site can display current runs, claim states, and links to artifacts.

Do not optimize for scale first. Optimize for:
- Correctness
- Auditability
- Reproducibility
- Clear separation of responsibilities
- Safe future self-improvement

## Implementation Guidance

- Preserve a strict distinction between raw evidence and interpreted conclusions.
- Treat git history and append-only artifact storage as part of the product, not as an afterthought.
- Design for long-running operation, resumability, and observable state.
- Make workflow changes explicit and reviewable.
- Keep the system practical for a human operator to inspect, interrupt, and correct.

Your task is to scaffold and implement the project foundation so that this research agent can start operating with a minimal end-to-end loop, while preserving all constraints and invariants above.


## Engineering reference

- In-workflow LLM agent call could directly use [SDK – Codex \| OpenAI Developers](https://developers.openai.com/codex/sdk) first,  Avoid reinventing the wheel. However, this is not set in stone; if you believe there is a better implementation approach—such as using a different agent framework or building from scratch—you are free to use or switch to that alternative method.
- Write precise readme document
