from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile and run the CUDA memory hierarchy probe")
    parser.add_argument("--working-set-kb", type=int, required=True)
    parser.add_argument("--stride-bytes", type=int, required=True)
    parser.add_argument("--iterations", type=int, required=True)
    parser.add_argument("--threads-per-block", type=int, required=True)
    parser.add_argument("--blocks", type=int, required=True)
    parser.add_argument("--repeat-count", type=int, required=True)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--build-dir", required=True)
    parser.add_argument("--compile-log", required=True)
    return parser.parse_args()


def ensure_compiled(build_dir: Path, compile_log: Path) -> Path:
    source_path = Path(__file__).with_suffix(".cu")
    binary_path = build_dir / "cuda_memory_hierarchy_probe"
    build_dir.mkdir(parents=True, exist_ok=True)

    if binary_path.exists() and binary_path.stat().st_mtime >= source_path.stat().st_mtime:
        compile_log.write_text("cache_hit=true\n", encoding="utf-8")
        return binary_path

    cmd = [
        "/usr/local/cuda/bin/nvcc",
        "-O3",
        "-std=c++17",
        str(source_path),
        "-o",
        str(binary_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    compile_log.write_text(
        f"command={' '.join(cmd)}\nreturncode={result.returncode}\nstdout=\n{result.stdout}\nstderr=\n{result.stderr}\n",
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    return binary_path


def main() -> None:
    args = parse_args()
    build_dir = Path(args.build_dir)
    compile_log = Path(args.compile_log)
    binary_path = ensure_compiled(build_dir, compile_log)
    cmd = [
        str(binary_path),
        "--working-set-kb",
        str(args.working_set_kb),
        "--stride-bytes",
        str(args.stride_bytes),
        "--iterations",
        str(args.iterations),
        "--threads-per-block",
        str(args.threads_per_block),
        "--blocks",
        str(args.blocks),
        "--repeat-count",
        str(args.repeat_count),
        "--seed",
        str(args.seed),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
