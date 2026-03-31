# Knowledge Base

This directory contains curated claim documents and derived summaries.
It is not the append-only run history.

Questions: 5
Experiment Specs: 5
Claims: 5

- [claim_c676d8a7c885](claims/claim_c676d8a7c885.md): For the tested single-GPU configuration, a 2048 KB working set with 128-byte stride produced an estimated 147.73436 GB/s in the CUDA memory probe over 3 timed launches.
- [claim_2ba9ae0d5738](claims/claim_2ba9ae0d5738.md): For a 2048 KB working set and 4-byte stride under the specified CUDA probe configuration, the measurement yielded an estimated 334.954323 GB/s averaged over 3 timed launches.
- [claim_a670c2343b42](claims/claim_a670c2343b42.md): For working set 256 KB and stride 128 bytes, the CUDA memory probe measured 187.236694 GB/s over 3 timed launches.
- [claim_c4657b0b5cce](claims/claim_c4657b0b5cce.md): For working set 256 KB and stride 4 bytes, the CUDA memory probe measured an estimated 357.310682 GB/s with average elapsed time 2.292683 ms over 3 timed launches; this supports the missing control-cell measurement itself, but not by itself a claim about how much higher it is than the 256 KB, 128-byte-stride case.
- [claim_838cc3215edd](claims/claim_838cc3215edd.md): For working set 1024 KB and stride 128 bytes, the CUDA memory probe measured an estimated 161.603575 GB/s over 3 timed launches, with average elapsed time 5.069195 ms under the specified fixed launch configuration.
