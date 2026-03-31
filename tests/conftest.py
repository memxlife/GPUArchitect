from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(autouse=True)
def disable_default_codex_auth(monkeypatch, tmp_path):
    from gpu_research_agent import codex_client as module

    monkeypatch.setattr(module, "DEFAULT_CODEX_AUTH_PATH", tmp_path / "missing-auth.json")
    monkeypatch.setenv("GPUARCHITECT_FORCE_SYNTHETIC", "1")
