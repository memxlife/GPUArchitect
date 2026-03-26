# Experiment Pipeline

## Execution Flow

run → parse → store → analyze → (optional) claim

## Steps

1. Benchmark execution
2. Output parsing
3. Observation storage
4. Model update
5. LLM interpretation
6. Claim generation (optional)

## Current Limitations

- sweep results stored as raw stdout
- no structured experiment registry
- no profiler integration yet

## Next Improvements

- normalized experiment records
- profiler metrics integration
- batch experiment execution
