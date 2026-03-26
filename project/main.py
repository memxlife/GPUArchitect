from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from model.model import PerformanceModel
from parser.parse_ncu import parse_key_value_output

try:
    from llm.interpret import interpret_result
except ImportError:
    interpret_result = None  # type: ignore


ROOT = Path(__file__).resolve().parent


def run_runner(benchmark: str, profile: bool, program_args: list[str]) -> str:
    cmd = [
        sys.executable,
        str(ROOT / "runner" / "run.py"),
        "--benchmark",
        benchmark,
    ]

    if profile:
        cmd.append("--profile")

    cmd.extend(program_args)

    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Runner failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    return result.stdout


def extract_program_output(full_output: str) -> str:
    lines = full_output.splitlines()
    in_program_section = False
    collected: list[str] = []

    for line in lines:
        if line.strip() == "=== PROGRAM OUTPUT ===":
            in_program_section = True
            continue
        if line.strip().startswith("=== NCU OUTPUT ==="):
            break
        if in_program_section:
            collected.append(line)

    return "\n".join(collected).strip()


def maybe_run_llm_analysis(program_output: str, enable_llm: bool) -> str | None:
    if not enable_llm:
        return None

    if interpret_result is None:
        return "LLM analysis requested, but llm.interpret could not be imported."

    try:
        return interpret_result(program_output)
    except Exception as exc:
        return f"LLM analysis failed: {exc}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", choices=["memory", "compute"], default="memory")
    parser.add_argument("--profile", action="store_true")
    parser.add_argument("--llm-analysis", action="store_true")
    parser.add_argument("--generate-claim", action="store_true")  # ← ADD THIS LINE
    parser.add_argument("program_args", nargs="*")

    args = parser.parse_args()

    full_output = run_runner(args.benchmark, args.profile, args.program_args)
    print(full_output)

    program_output = extract_program_output(full_output)
    parsed = parse_key_value_output(program_output)
    # -------------------------------
    # store observation
    # -------------------------------
    from knowledge.store import add_observation

    obs = {
        "benchmark": parsed.get("benchmark"),
        "parameters": {
            "n": parsed.get("n"),
            "threads_per_block": parsed.get("threads_per_block"),
            "inner_iters": parsed.get("inner_iters"),
        },
        "metrics": {
            "avg_time_ms": parsed.get("avg_time_ms"),
        }
    }

    add_observation(obs)

    # -------------------------------
    # Existing model logic
    # -------------------------------

    model = PerformanceModel()
    model.load()
    model.update(parsed)
    model.save()

    print("=== PARSED RESULT ===")
    print(parsed)
    print("Saved to results/latest_result.json")

    llm_analysis = maybe_run_llm_analysis(program_output, args.llm_analysis)
    if llm_analysis is not None:
        print("\n=== LLM ANALYSIS ===")
        print(llm_analysis)

    # -------------------------------
    # NEW: claim pipeline
    # -------------------------------
    if args.generate_claim:
        from knowledge.pipeline import process_claim_from_observations
        process_claim_from_observations(program_output)



if __name__ == "__main__":
    main()
