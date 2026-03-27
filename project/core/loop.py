from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )


def build_state() -> None:
    cmd = [sys.executable, "-m", "core.state_builder"]
    result = run_cmd(cmd)
    print(result.stdout, end="")
    if result.returncode != 0:
        raise RuntimeError(f"state_builder failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")


def load_plan() -> dict[str, Any]:
    from core.planner import select_next_experiment
    return select_next_experiment()


def save_plan(plan: dict[str, Any], cycle_idx: int) -> Path:
    out_dir = ROOT / "data" / "planning" / "runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"cycle_{cycle_idx:02d}_plan.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)
    return out_file


def run_plan_file(plan_file: Path) -> None:
    cmd = [sys.executable, "-m", "runner.run_next", str(plan_file)]
    result = run_cmd(cmd)
    print(result.stdout, end="")
    if result.returncode != 0:
        raise RuntimeError(f"run_next failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")


def maybe_generate_pattern_claim(plan: dict[str, Any]) -> None:
    question_id = plan.get("question_id")
    benchmark_name = plan.get("benchmark_name", "")

    if benchmark_name != "compute_fma_like":
        return

    if question_id == "q_compute_transition_refine":
        cmd = [sys.executable, "-m", "knowledge.run_pattern_claim"]
    elif question_id == "q_compute_block_sensitivity":
        cmd = [sys.executable, "-m", "knowledge.run_block_pattern_claim"]
    else:
        return

    result = run_cmd(cmd)
    print(result.stdout, end="")
    if result.returncode != 0:
        raise RuntimeError(
            f"pattern claim generation failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def main() -> None:
    max_cycles = 3
    last_question_id: str | None = None

    for cycle_idx in range(1, max_cycles + 1):
        print(f"\n===== PLANNING CYCLE {cycle_idx} =====")

        build_state()
        plan = load_plan()

        print("=== SELECTED PLAN ===")
        print(json.dumps(plan, indent=2))

        question_id = plan.get("question_id")
        if question_id is None:
            print("Stopping: no active question available.")
            break

        if last_question_id is not None and question_id == last_question_id:
            print(f"Stopping: repeated question_id '{question_id}' with no agenda change.")
            break

        plan_file = save_plan(plan, cycle_idx)
        run_plan_file(plan_file)
        maybe_generate_pattern_claim(plan)
        build_state()

        last_question_id = question_id

    print("\n===== LOOP FINISHED =====")


if __name__ == "__main__":
    main()
