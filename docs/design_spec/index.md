# Design Specification (Current)

## Version
v0.4

## Overview

The system is a GPU experiment-driven learning system that:

- runs controlled CUDA benchmarks
- extracts structured observations
- builds causal knowledge (what / why / how / so what)
- plans next experiments to maximize understanding

## Modules

- System Overview → system_overview.md
- Experiment Pipeline → experiment_pipeline.md
- Knowledge Base → knowledge_base.md
- Planner → planner.md
- LLM Integration → llm_integration.md

## Current State Summary

The system has achieved:

- working experiment loop
- structured observation storage
- first causal claims
- first pattern-level claim (regime transition)

The next phase is:

> transition from passive knowledge accumulation to **active experiment planning**
