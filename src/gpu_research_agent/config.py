from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CODEX_AUTH_PATH = Path.home() / ".codex" / "auth.json"


@dataclass(frozen=True)
class WorkspaceLayout:
    root: Path

    @property
    def agent_runtime_dir(self) -> Path:
        return PACKAGE_ROOT / "agent_runtime"

    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    @property
    def plans_dir(self) -> Path:
        return self.data_dir / "plans"

    @property
    def runs_dir(self) -> Path:
        return self.data_dir / "runs"

    @property
    def records_dir(self) -> Path:
        return self.data_dir / "records"

    @property
    def control_dir(self) -> Path:
        return self.data_dir / "control"

    @property
    def knowledge_dir(self) -> Path:
        return self.root / "knowledge"

    @property
    def exports_dir(self) -> Path:
        return self.root / "exports"

    @property
    def site_dir(self) -> Path:
        return self.root / "site"

    @property
    def config_path(self) -> Path:
        return self.root / "gpu_research.yaml"


DEFAULT_MODEL = "gpt-5.4"
DEFAULT_ROUND_BUDGET_SECONDS = 120
DEFAULT_CODEX_REASONING = "medium"
