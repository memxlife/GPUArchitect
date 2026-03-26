from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT / "build"
BENCH_DIR = ROOT / "benchmarks"


def run_cmd(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=False,
    )


def compile_benchmark(source: Path, output: Path) -> None:
    nvcc = shutil.which("nvcc")
    if nvcc is None:
        raise RuntimeError("nvcc not found in PATH. Please install CUDA toolkit or add nvcc to PATH.")

    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        nvcc,
        str(source),
        "-O3",
        "-std=c++17",
        "-o",
        str(output),
    ]
    result = run_cmd(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")


def run_binary(binary: Path, program_args: list[str]) -> str:
    cmd = [str(binary), *program_args]
    result = run_cmd(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"Program failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    return result.stdout


def profile_with_ncu(binary: Path, program_args: list[str], output_base: Path) -> str:
    ncu = shutil.which("ncu")
    if ncu is None:
        raise RuntimeError("ncu not found in PATH. Please install Nsight Compute or add it to PATH.")

    cmd = [
        ncu,
        "--target-processes",
        "all",
        "--set",
        "basic",
        "--csv",
        "-o",
        str(output_base),
        str(binary),
        *program_args,
    ]
    result = run_cmd(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"NCU profiling failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    return result.stdout + "\n" + result.stderr


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", choices=["memory", "compute"], default="memory")
    parser.add_argument("--profile", action="store_true")
    parser.add_argument("program_args", nargs="*")
    args = parser.parse_args()

    source = BENCH_DIR / f"{args.benchmark}.cu"
    binary = BUILD_DIR / args.benchmark

    compile_benchmark(source, binary)
    stdout = run_binary(binary, args.program_args)

    print("=== PROGRAM OUTPUT ===")
    print(stdout.strip())

    if args.profile:
        profile_dir = BUILD_DIR / "profiles"
        profile_dir.mkdir(parents=True, exist_ok=True)
        output_base = profile_dir / args.benchmark
        profile_output = profile_with_ncu(binary, args.program_args, output_base)

        print("\n=== NCU OUTPUT ===")
        print(profile_output.strip())


if __name__ == "__main__":
    main()
