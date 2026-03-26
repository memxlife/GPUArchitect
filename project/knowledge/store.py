from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KB_DIR = ROOT / "knowledge"

OBS_FILE = KB_DIR / "observations.jsonl"
CLAIM_FILE = KB_DIR / "claims.jsonl"

KB_DIR.mkdir(exist_ok=True)


def append_jsonl(path: Path, data: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")


def add_observation(obs: dict) -> None:
    append_jsonl(OBS_FILE, obs)


def add_claim(claim: dict) -> None:
    append_jsonl(CLAIM_FILE, claim)
