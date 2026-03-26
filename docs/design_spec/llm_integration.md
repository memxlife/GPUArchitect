# LLM Integration

## Role

LLM is used for:

- interpretation
- hypothesis generation
- claim drafting

LLM is NOT used for:

- executing experiments
- updating model state
- determining truth

## Pipeline

observation → LLM draft → validation → knowledge

## Validation Rules

- must include evidence
- must include causal explanation
- must include mechanism
- must include implication
- uncertainty must be {low, medium, high}

## Current Behavior

- LLM generates claims
- validator filters invalid outputs
- accepted claims stored in knowledge base

## Limitations

- LLM does not yet operate on multi-observation input by default
- no grounding with profiler metrics
- no consistency checking across claims

## Next Step

- improve prompt structure
- add multi-observation reasoning
- integrate with planner
