# claim_838cc3215edd

Question: At fixed 128-byte stride, does an intermediate 1024 KB working set produce bandwidth between the verified 256 KB and 2048 KB hostile-stride endpoints under the same CUDA memory probe parameters?
Hypothesis: With launch shape and iterations held fixed, the 1024 KB, 128-byte-stride probe will measure estimated bandwidth between the accepted 256 KB, 128-byte-stride result and the accepted 2048 KB, 128-byte-stride result; if it falls outside that interval, the apparent working-set effect on the hostile-stride path is not a simple monotone trend under this probe.

Status: accepted
Confidence: medium

## Statement
For working set 1024 KB and stride 128 bytes, the CUDA memory probe measured an estimated 161.603575 GB/s over 3 timed launches, with average elapsed time 5.069195 ms under the specified fixed launch configuration.

## Support Summary
Raw evidence shows a successful `cuda_memory_hierarchy_probe` run at 1024 KB working set, 128-byte stride, 80 blocks, 128 threads per block, and 20000 iterations, yielding consistent aggregated timing output for `repeat_count=3` and checksum 130719612928.

## Metrics

- avg_elapsed_ms: 5.069195
- blocks: 80
- estimated_bandwidth_gb_s: 161.603575
- repeat_count: 3
- stride_bytes: 128
- threads_per_block: 128
- working_set_kb: 1024

## Verification
accepted

Accepted for the narrow measurement claim. The baseline metrics directly match the stated 1024 KB, 128-byte stride run configuration and report 161.603575 GB/s, 5.069195 ms, repeat_count=3, and checksum 130719612928; the rerun preserved the configuration and checksum and matched within 3.7135% relative delta, supporting reproducibility for this specific observation. The broader interval hypothesis against 256 KB and 2048 KB endpoints remains unverified from this payload, but that does not undermine the stated measurement claim.
