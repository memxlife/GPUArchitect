from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict

from knowledge.dedup import is_duplicate_claim


ROOT = Path(__file__).resolve().parents[1]
KB_DIR = ROOT / "knowledge"

OBS_FILE = KB_DIR / "observations.jsonl"
CLAIM_FILE = KB_DIR / "claims.jsonl"

KB_DIR.mkdir(exist_ok=True)


def append_jsonl(path: Path, data: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")

def load_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows

def add_observation(obs: dict) -> None:
    append_jsonl(OBS_FILE, obs)


def add_claim(claim: dict) -> None:
    existing_claims = load_jsonl(CLAIM_FILE)

    if is_duplicate_claim(claim, existing_claims):
        print("Duplicate claim skipped.")
        return

    append_jsonl(CLAIM_FILE, claim)
    print("Claim stored.")
