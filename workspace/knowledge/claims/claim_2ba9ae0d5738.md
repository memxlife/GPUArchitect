# claim_2ba9ae0d5738

Question: Run a matched cache-friendly control for the latest 2048 KB strided CUDA memory probe to test whether the observed bandwidth is due to memory-hierarchy locality rather than fixed launch configuration.
Hypothesis: Under the same single-GPU launch configuration and working-set size as spec_3626106571cf, reducing the access stride from 128 bytes to 4 bytes will produce higher effective bandwidth, falsifying the locality explanation if the paired control does not improve over the prior strided result.

Status: accepted
Confidence: medium

## Statement
For a 2048 KB working set and 4-byte stride under the specified CUDA probe configuration, the measurement yielded an estimated 334.954323 GB/s averaged over 3 timed launches.

## Support Summary
Raw evidence: the bounded `cuda_memory_hierarchy_probe` completed successfully with working_set_kb=2048, stride_bytes=4, blocks=80, threads_per_block=128, iterations=20000, avg_elapsed_ms=2.445707, checksum=10589503488, and estimated_bandwidth_gb_s=334.954323. Interpretation: this provides a cache-friendly control-point measurement under matched launch parameters, but by itself it only supports the observed bandwidth for this configuration, not a causal locality conclusion.

## Metrics

- avg_elapsed_ms: 2.445707
- blocks: 80
- estimated_bandwidth_gb_s: 334.954323
- repeat_count: 3
- stride_bytes: 4
- threads_per_block: 128
- working_set_kb: 2048

## Verification
accepted

The claim is limited to the observed result for the specified 2048 KB, 4-byte-stride configuration, and both the original run and rerun report the same benchmark/setup, identical checksum, and closely matching estimated bandwidth (334.954323 vs 337.20297 GB/s; relative delta 0.006713), which supports the stated measurement over 3 timed launches.
