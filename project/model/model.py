from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
RESULTS_FILE = RESULTS_DIR / "latest_result.json"


class PerformanceModel:
    def __init__(self) -> None:
        self.state: dict[str, Any] = {}

    def update(self, observation: dict[str, Any]) -> None:
        self.state.update(observation)

    def save(self, path: Path = RESULTS_FILE) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    def load(self, path: Path = RESULTS_FILE) -> None:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                self.state = json.load(f)
