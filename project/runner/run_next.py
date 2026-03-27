from __future__ import annotations

import argparse
import itertools
import json
import subprocess
import sys
from pathlib import Path

from core.planner import select_next_experiment

ROOT = Path(__file__).resolve().parents[1]


def load_plan_from_file(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_list(value, default):
    if value is None:
        return [default]
    if isinstance(value, list):
        return value
    return [value]


def parse_metrics_from_stdout(stdout: str) -> dict:
    metrics: dict = {}
    for line in stdout.splitlines():
        line = line.strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)

        if key in {"n", "threads_per_block", "inner_iters", "iterations"}:
            try:
                metrics[key] = int(value)
            except ValueError:
                metrics[key] = value
        elif key in {"avg_time_ms", "effective_bandwidth_gb_s", "checksum_1024"}:
            try:
                metrics[key] = float(value) if value != "inf" else float("inf")
            except ValueError:
                metrics[key] = value
        else:
            metrics[key] = value

    return metrics


def save_sweep_results(plan: dict, rows: list[dict]) -> None:
    results_dir = ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    question_id = plan.get("question_id")
    if question_id == "q_compute_block_sensitivity":
        filename = results_dir / "compute_block_sensitivity_sweep.json"
    elif question_id == "q_compute_transition_refine":
        filename = results_dir / "compute_inner_iters_refined_sweep.json"
    elif question_id == "q_compute_iterations_stability":
        filename = results_dir / "compute_iterations_stability_sweep.json"
    else:
        filename = results_dir / "latest_sweep.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    print(f"Saved sweep results to {filename}")


def run_plan(plan: dict) -> None:
    print("=== NEXT EXPERIMENT PLAN ===")
    print(plan)

    benchmark = plan["benchmark"]
    parameter_space = plan.get("parameter_space", {})

    default_n = plan.get("n", 1 << 24)
    default_iterations = plan.get("iterations", 20)
    default_threads_per_block = 256
    default_inner_iters = 1024

    n_list = ensure_list(parameter_space.get("n"), default_n)
    threads_per_block_list = ensure_list(
        parameter_space.get("threads_per_block"), default_threads_per_block
    )
    inner_iters_list = ensure_list(
        parameter_space.get("inner_iters"), default_inner_iters
    )
    iterations_list = ensure_list(
        parameter_space.get("iterations"), default_iterations
    )

    rows: list[dict] = []

    for n, threads_per_block, inner_iters, iterations in itertools.product(
        n_list,
        threads_per_block_list,
        inner_iters_list,
        iterations_list,
    ):
        cmd = [
            sys.executable,
            str(ROOT / "main.py"),
            "--benchmark",
            benchmark,
            str(n),
            str(threads_per_block),
            str(inner_iters),
            str(iterations),
        ]

        print("Running:", " ".join(cmd))
        result = subprocess.run(cmd, text=True, capture_output=True, check=False)
        print(result.stdout, end="")

        row = {
            "benchmark": plan.get("benchmark_name", benchmark),
            "question_id": plan.get("question_id"),
            "n": n,
            "threads_per_block": threads_per_block,
            "inner_iters": inner_iters,
            "iterations": iterations,
            "stdout": result.stdout,
            "returncode": result.returncode,
        }

        row.update(parse_metrics_from_stdout(result.stdout))
        rows.append(row)

    save_sweep_results(plan, rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "plan_file",
        nargs="?",
        help="Optional path to a saved plan JSON file.",
    )
    args = parser.parse_args()

    if args.plan_file:
        plan = load_plan_from_file(Path(args.plan_file))
    else:
        plan = select_next_experiment()

    run_plan(plan)


if __name__ == "__main__":
    main()
