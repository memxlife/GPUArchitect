from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def run_one(inner_iters: int) -> dict:
    cmd = [
        sys.executable,
        str(ROOT / "main.py"),
        "--benchmark",
        "compute",
        str(1 << 24),   # n
        "256",          # threads_per_block
        str(inner_iters),
        "20",           # iterations
    ]

    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Experiment failed for inner_iters={inner_iters}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    return {
        "inner_iters": inner_iters,
        "stdout": result.stdout,
    }


def main() -> None:
    sweep_values = [1, 4, 16, 64, 256, 1024, 4096, 16384]
    all_results = []

    for v in sweep_values:
        print(f"Running inner_iters={v}")
        out = run_one(v)
        all_results.append(out)

    output_file = RESULTS_DIR / "compute_inner_iters_sweep.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print(f"Saved sweep results to {output_file}")


if __name__ == "__main__":
    main()
