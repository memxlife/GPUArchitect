## Planner Specification

### 1. Planner Objective

The planner is the core decision-making component of the system. Its objective is to maximize the system’s quantitative understanding of the underlying GPU architecture under limited experimental budget, validity constraints, and curriculum constraints.

More precisely, the planner should select the next experiment so that it maximally improves the system’s latent architectural model. The planner is not optimizing for kernel speed, throughput, or benchmark score directly. Instead, it is optimizing for **understanding**. That understanding includes the ability to identify performance regimes, infer mechanisms, localize boundaries, disambiguate competing explanations, and determine what architectural knowledge is still missing.

The planner therefore solves the following problem:

> choose the next valid experiment that maximizes expected information gain about the latent GPU model, while respecting causal dependencies, experiment cost, and interpretability constraints.

---

### 2. Planner Role in the Overall System

The planner sits above the benchmark and execution layers. It does not directly run CUDA code, parse profiler outputs, or write claims. Instead, it consumes the structured outputs of those components and decides what question should be addressed next.

Its role is to transform the current state of the knowledge base into an experimental agenda.

The planner should therefore answer two questions:

1. **What should the system try to learn next?**
2. **What specific experiment should be run to learn it most effectively?**

These two questions are different and should be handled separately.

---

### 3. Hybrid Planner Philosophy

The planner should be hybrid. It should combine:

- **large language model reasoning** for high-level causal and semantic planning
- **Bayesian or active-learning style optimization** for low-level numerical experiment selection

The rationale is that these two layers solve different problems.

The large language model is well suited for:
- reading the current knowledge graph
- identifying unresolved causal questions
- reasoning about prerequisite structure
- deciding which subsystem or benchmark family should be explored next
- choosing the global learning agenda

The quantitative optimization layer is well suited for:
- choosing parameter values within a fixed benchmark family
- balancing local exploration and exploitation
- refining thresholds, boundaries, or response curves
- selecting sample locations that reduce uncertainty most efficiently

Thus, the planner should follow this principle:

> The LLM decides **which uncertainty frontier to attack next**.  
> The Bayesian or active-learning layer decides **where to sample on that frontier**.

---

### 4. Hierarchical Planner Structure

The planner should operate in two levels.

#### 4.1 Agenda Selection Level

At the top level, the planner selects the most important unresolved knowledge target. This target is not a specific benchmark parameter, but a scientific question such as:

- What is the exact transition boundary between low-intensity and compute-dominated behavior?
- Is the low-`inner_iters` regime dominated by launch overhead or memory effects?
- How sensitive is the compute-dominated regime to block size?
- Is the current benchmark numerically stable over the intended range?

This level of planning is causal, semantic, and curriculum-aware. It should be driven primarily by the large language model, using the current knowledge base, uncertainty frontier, and dependency graph as context.

#### 4.2 Local Experiment Optimization Level

Once a knowledge target has been selected, the planner chooses a specific experiment inside the relevant benchmark family. This may involve choosing:

- `inner_iters`
- `threads_per_block`
- problem size `n`
- benchmark family
- profiler mode

This level is quantitative. It should use uncertainty-aware local optimization to choose the most informative next sample. At this stage, the planner is not choosing among broad scientific questions; it is choosing among candidate experimental points.

---

### 5. Planner State

The planner should operate over a structured internal state derived from the knowledge base. That state should contain at least the following components.

#### 5.1 Claim Graph

The set of accepted claims, including:

- claim description
- evidence
- cause
- mechanism
- implication
- uncertainty

This defines what the system currently believes.

#### 5.2 Uncertainty Frontier

A structured list of unresolved questions. Examples include:

- exact transition point between flat and compute-scaling regimes is unknown
- contribution of launch overhead versus memory effects in the low-`inner_iters` regime is unresolved
- block-size sensitivity in the compute regime has not been measured
- numerical instability appears at high `inner_iters`

This defines what the system does not yet know.

#### 5.3 Dependency Graph

A graph of prerequisite relationships among learning objectives. For example:

- “measure block-size sensitivity in compute regime” depends on “identify compute regime”
- “study mixed compute-memory behavior” depends on “calibrate compute-only and memory-only baselines”

This prevents the planner from prematurely jumping into higher-level questions before foundational knowledge is established.

#### 5.4 Experiment Registry

A record of experiments already performed, including:

- benchmark family
- parameter settings
- outputs
- derived observations
- validity status

This prevents redundant experiments and supports estimation of marginal value.

#### 5.5 Benchmark Grammar

The set of available experiment families and their valid parameter spaces. This defines the planner’s action space.

---

### 6. Planner Output

The planner should output a structured experiment plan with fields such as:

- target question
- benchmark family
- parameter values
- rationale
- expected evidence type
- expected information gain category
- estimated cost
- validity considerations

A planner output should not simply say “run another benchmark.” It should say why that benchmark is the next one, what it is intended to clarify, and how it connects to the current uncertainty frontier.

---

### 7. Planner Objective Function

The planner should score candidate experiments using a combination of four factors:

#### 7.1 Expected Information Gain

How much is the experiment expected to reduce uncertainty in the latent architectural model?

Examples:
- refining a suspected transition boundary has high information gain if the boundary is still broad
- rerunning a well-understood point has low information gain

#### 7.2 Foundational Importance

How important is this uncertainty to the broader learning agenda?

Examples:
- locating the compute-regime boundary is foundational
- studying block-size sensitivity is less valuable until the compute regime is identified

#### 7.3 Experiment Cost

How expensive is the experiment in terms of runtime, profiling cost, and implementation complexity?

Examples:
- simple benchmark sweep point = low cost
- profiler-heavy or multi-family experiment = higher cost

#### 7.4 Validity / Interpretability Risk

How likely is the experiment to produce interpretable results?

Examples:
- known overflow region at high `inner_iters` = high risk
- benchmark family with known confounding = high risk
- simple regime-boundary refinement = low risk

Thus, the planner should prefer experiments that are:
- highly informative
- foundationally important
- cheap enough to run
- likely to yield interpretable evidence

---

### 8. Exploration and Exploitation

The planner must balance two forms of exploration and exploitation.

#### 8.1 Local Exploration vs Exploitation

Within a fixed question family, the planner should balance:

- exploitation: refining already identified but unresolved structure
- exploration: probing less-certain parts of the current parameter space

For example, once a transition between `64` and `256` is known, the planner should exploit that finding by sampling inside the interval rather than sampling far outside it.

This balance should be handled by the local quantitative planner.

#### 8.2 Global Exploration vs Exploitation

Across benchmark families and knowledge targets, the planner must decide whether to:

- continue refining the current subsystem
- expand into a new subsystem

For example:
- keep refining the compute transition
- or move to block-size sensitivity
- or shift to memory benchmarking

This balance should be handled by the top-level reasoning layer.

---

### 9. Staged Algorithmic Strategy

The planner should evolve in three stages.

#### Stage 1: Rule-Based Causal Planner

At the beginning, the planner should use explicit logic:

- read accepted claims
- identify unresolved uncertainty
- select highest-priority next question
- choose candidate experiments by simple heuristics

This stage is interpretable and easy to debug.

#### Stage 2: Scored Active-Learning Planner

The planner should then introduce quantitative scoring:

- assign uncertainty values to unresolved questions
- assign expected gain scores to candidate experiments
- rank experiments by gain, cost, and validity

This stage is still mostly heuristic, but more principled.

#### Stage 3: Probabilistic / Bayesian Planner

Eventually, the planner should maintain explicit uncertainty over latent architectural parameters and use formal acquisition functions to select experiments.

Examples:
- boundary posterior
- slope uncertainty in compute regime
- parameter sensitivity surfaces

This stage enables true Bayesian experimental design.

---

### 10. Current Planner Instantiation (Based on Existing Results)

At the current state of the project, the planner should identify the following as the top unresolved question:

> What is the exact transition boundary between the flat-runtime regime and the compute-dominated scaling regime in the `compute_fma_like` benchmark?

The system already has evidence that:

- runtime is flat up to `inner_iters <= 64`
- runtime rises significantly by `256`
- runtime scales approximately linearly beyond that
- very large `inner_iters` may overflow

Therefore, the top-level planner should select:

- **agenda item**: refine regime transition boundary

Then the local planner should propose:

- `inner_iters = 96, 128, 160, 192, 224, 256`

This is a good local choice because:
- it refines the highest-value unresolved interval
- it stays below the known overflow region
- it is cheap and interpretable
- it improves one of the system’s most foundational claims

After that, if the transition is localized more precisely, the planner should likely select:

- **agenda item**: measure block-size sensitivity in the compute-dominated regime

using values such as:

- `threads_per_block = 64, 128, 256, 512`

at a safe compute-dominated point such as:

- `inner_iters = 1024`

---

### 11. Summary

The planner is an uncertainty-aware, curriculum-constrained, causal experiment designer for latent GPU model identification.

Its design is hierarchical:

- the large language model selects the global learning agenda
- the Bayesian or active-learning layer selects local experiment parameters

Its state is defined by:

- accepted claims
- uncertainty frontier
- dependency graph
- experiment registry
- benchmark grammar

Its objective is:

> maximize expected information gain about the GPU architecture while preserving interpretability, respecting cost, and following a causally valid learning sequence.
