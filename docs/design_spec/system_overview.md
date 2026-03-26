# System Overview

## Current Objective

Establish a reliable and reproducible experimental loop and extract first causal insights from GPU behavior.

## Architecture

### Benchmark Layer
- CUDA kernels (`compute.cu`, `memory.cu`)
- Parameterized execution

### Execution Layer
- `runner/run.py`
- Compiles with `nvcc`
- Executes binary

### Parsing Layer
- Extracts key=value outputs

### Model Layer
- Stores latest result
- Not yet predictive

### LLM Layer
- GPT-5.4 used for analysis
- No control authority

### Entry Point
- `main.py`

## Assumptions

- compute kernel approximates arithmetic intensity scaling
- runtime stable with averaging
- LLM used only for interpretation
- experiments assumed single dominant mechanism
