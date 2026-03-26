from __future__ import annotations

from knowledge.pattern_pipeline import process_pattern_claim_from_sweep


def main() -> None:
    process_pattern_claim_from_sweep("compute_inner_iters_sweep.json")


if __name__ == "__main__":
    main()
