# claim_c676d8a7c885

Question: explore memory hierarchy effects with strided global memory access
Hypothesis: For a fixed single-GPU launch configuration, a 2048 KB working set with 128-byte strided global-memory accesses will produce lower effective bandwidth than a cache-friendly regime, indicating sensitivity to memory-hierarchy locality under otherwise identical controls.

Status: accepted
Confidence: medium

## Statement
For the tested single-GPU configuration, a 2048 KB working set with 128-byte stride produced an estimated 147.73436 GB/s in the CUDA memory probe over 3 timed launches.

## Support Summary
Raw probe output reports `avg_elapsed_ms=5.545088`, `estimated_bandwidth_gb_s=147.73436`, `working_set_kb=2048`, `stride_bytes=128`, `blocks=80`, `threads_per_block=128`, `iterations=20000`, and a successful checksum (`19050463232`).

## Metrics

- avg_elapsed_ms: 5.545088
- blocks: 80
- estimated_bandwidth_gb_s: 147.73436
- repeat_count: 3
- stride_bytes: 128
- threads_per_block: 128
- working_set_kb: 2048

## Verification
accepted

Accepted: the claim is narrowly stated and matches the original probe output exactly (`estimated_bandwidth_gb_s=147.73436`, `working_set_kb=2048`, `stride_bytes=128`, `repeat_count=3`, checksum match). The independent rerun produced 145.81688 GB/s with the same configuration and checksum, a relative delta of 0.012979, which supports the reported signal rather than contradicting it. The caveats listed in counterevidence limit generalization, but they do not undermine this specific factual statement about the tested run.
