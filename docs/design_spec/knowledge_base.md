# Knowledge Base

## Purpose

Transform raw measurements into causal understanding.

## Structure

### Observation

- benchmark
- parameters
- metrics

### Claim

Each claim must contain:

- description
- evidence
- cause
- mechanism
- implication
- uncertainty

## Causal Model

Knowledge is structured as:

- What → observation
- Why → cause
- How → mechanism
- So What → implication

## Current Knowledge

From inner_iters sweep:

- flat regime for inner_iters ≤ 64
- transition between 64 and 256
- compute scaling beyond 256
- overflow at very large values

## Known Issues

- compute kernel instability
- lack of uncertainty tracking
- no graph linking between claims

## Next Step

- introduce claim linking
- introduce uncertainty frontier
- move from observation-level to pattern-level knowledge
