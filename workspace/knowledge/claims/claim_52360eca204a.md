# claim_52360eca204a

Question: Explore memory hierarchy effects with strided global memory access
Hypothesis: With a 1024 KB working set and 128-byte stride, effective bandwidth will be measurably lower than the probe's smaller, more contiguous default access pattern, consistent with weaker cache locality and coalescing.

Status: accepted
Confidence: medium

## Statement
For a 1024 KB working set and 128-byte stride, the CUDA memory probe reported 164.220883 GB/s estimated bandwidth with an average elapsed time of 2.494202 ms across 5 timed launches.

## Support Summary
Raw evidence shows a completed `cuda_memory_hierarchy_probe` run with fixed geometry (`80` blocks, `128` threads per block), `10000` iterations, checksum `5637636096`, and matching observation/raw-output metrics. This supports a cautious claim about the measured result for this specific configuration, but not a stronger claim about hierarchy effects relative to other access patterns without baseline data.

## Metrics

- avg_elapsed_ms: 2.494202
- blocks: 80
- estimated_bandwidth_gb_s: 164.220883
- repeat_count: 5
- stride_bytes: 128
- threads_per_block: 128
- working_set_kb: 1024

## Verification
accepted

Accepted for the narrow measured-result claim: baseline and rerun use the same configuration, match checksums, and the rerun bandwidth differs by only 0.17%, supporting the reported 164.220883 GB/s and 2.494202 ms for this specific setup. This does not verify the broader hypothesis about reduced bandwidth versus a smaller or more contiguous baseline.
