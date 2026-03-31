from __future__ import annotations

from gpu_research_agent.codex_client import CodexClient
from gpu_research_agent.config import WorkspaceLayout


def test_codex_client_falls_back_without_runtime_or_credentials(tmp_path, monkeypatch) -> None:
    from gpu_research_agent import codex_client as module

    monkeypatch.setattr(module, "DEFAULT_CODEX_AUTH_PATH", tmp_path / "missing-auth.json")
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    layout = WorkspaceLayout(root=tmp_path)
    client = CodexClient(layout=layout)

    result = client.invoke_json(
        role="planner",
        instructions="test",
        payload={"question": "q"},
        output_schema={"type": "object", "properties": {}, "additionalProperties": False},
        fallback_output={"ok": True},
    )

    assert result.backend == "fallback"
    assert result.output == {"ok": True}


def test_codex_client_reads_default_auth_file(monkeypatch, tmp_path) -> None:
    from gpu_research_agent import codex_client as module

    auth_path = tmp_path / "auth.json"
    auth_path.write_text('{"OPENAI_API_KEY":"test-key"}', encoding="utf-8")
    monkeypatch.setattr(module, "DEFAULT_CODEX_AUTH_PATH", auth_path)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    auth_env = module._resolve_auth_env()

    assert auth_env["OPENAI_API_KEY"] == "test-key"
