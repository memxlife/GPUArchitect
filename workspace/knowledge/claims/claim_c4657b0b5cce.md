# claim_c4657b0b5cce

Question: Does the missing matched-control cell at 256 KB working set and 4-byte stride show substantially higher effective bandwidth than the 256 KB, 128-byte hostile-stride case under the same CUDA memory probe launch parameters?
Hypothesis: With launch shape, iterations, and controls held fixed, the missing 256 KB, 4-byte-stride cell will measure higher estimated bandwidth than the accepted 256 KB, 128-byte-stride result; if it does not, the hostile-stride penalty does not persist clearly at the reduced working set under this probe.

Status: accepted
Confidence: medium

## Statement
For working set 256 KB and stride 4 bytes, the CUDA memory probe measured an estimated 357.310682 GB/s with average elapsed time 2.292683 ms over 3 timed launches; this supports the missing control-cell measurement itself, but not by itself a claim about how much higher it is than the 256 KB, 128-byte-stride case.

## Support Summary
Raw output reports a successful `cuda_memory_hierarchy_probe` at 256 KB working set, 4-byte stride, 80 blocks, 128 threads per block, and 20,000 iterations, with checksum 10589503488 and estimated bandwidth 357.310682 GB/s. The evidence is internally consistent for this single cell, but the hostile-stride comparison value is absent from the provided payload.

## Metrics

- avg_elapsed_ms: 2.292683
- blocks: 80
- estimated_bandwidth_gb_s: 357.310682
- repeat_count: 3
- stride_bytes: 4
- threads_per_block: 128
- working_set_kb: 256

## Verification
accepted

Accepted: the payload consistently supports the 256 KB, 4-byte-stride measurement itself (357.310682 GB/s, 2.292683 ms, 3 timed launches), and the rerun closely matches it (356.635366 GB/s; relative_delta=0.001890). The statement is appropriately limited because the 256 KB, 128-byte-stride comparison value is not included here, so only the control-cell measurement is verified.
