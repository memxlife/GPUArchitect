from __future__ import annotations

import argparse
import json
import math
import random
import time


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deterministic synthetic memory probe")
    parser.add_argument("--working-set-kb", type=int, required=True)
    parser.add_argument("--stride-bytes", type=int, required=True)
    parser.add_argument("--iterations", type=int, required=True)
    parser.add_argument("--sleep-ms", type=int, default=10)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--repeat-count", type=int, default=3)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    start = time.perf_counter()

    penalty = math.log2(max(args.working_set_kb, 2))
    stride_penalty = max(args.stride_bytes / 64.0, 1.0)
    throughput = round((args.iterations / penalty) / stride_penalty, 6)
    latency = round((penalty * stride_penalty) / max(args.repeat_count, 1), 6)

    time.sleep(max(args.sleep_ms, 0) / 1000.0)
    elapsed = round(time.perf_counter() - start, 6)

    payload = {
        "benchmark": "synthetic_memory_probe",
        "working_set_kb": args.working_set_kb,
        "stride_bytes": args.stride_bytes,
        "iterations": args.iterations,
        "repeat_count": args.repeat_count,
        "throughput_score": throughput,
        "mean_latency_ms": latency,
        "elapsed_seconds": elapsed,
        "seed": args.seed,
    }
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
