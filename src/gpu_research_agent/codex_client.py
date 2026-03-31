from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import DEFAULT_CODEX_AUTH_PATH, DEFAULT_CODEX_REASONING, DEFAULT_MODEL, WorkspaceLayout


def _has_agent_runtime(layout: WorkspaceLayout) -> bool:
    return (layout.agent_runtime_dir / "package.json").exists()


def _log(message: str) -> None:
    print(f"[gpuarchitect] {message}", file=sys.stderr)


def _load_default_auth_env() -> dict[str, str]:
    if not DEFAULT_CODEX_AUTH_PATH.exists():
        return {}
    try:
        payload = json.loads(DEFAULT_CODEX_AUTH_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    auth_env: dict[str, str] = {}
    for key in ("CODEX_API_KEY", "OPENAI_API_KEY"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            auth_env[key] = value.strip()
    return auth_env


def _resolve_auth_env() -> dict[str, str]:
    auth_env = _load_default_auth_env()
    for key in ("CODEX_API_KEY", "OPENAI_API_KEY"):
        value = os.getenv(key)
        if value:
            auth_env[key] = value
    return auth_env


@dataclass(slots=True)
class CodexInvocationResult:
    output: dict[str, Any]
    backend: str
    thread_id: str | None
    usage: dict[str, Any] | None
    events: list[dict[str, Any]]
    raw_response: str


@dataclass(slots=True)
class CodexClient:
    layout: WorkspaceLayout
    model: str = DEFAULT_MODEL
    reasoning_effort: str = DEFAULT_CODEX_REASONING

    def invoke_json(
        self,
        *,
        role: str,
        instructions: str,
        payload: dict[str, Any],
        output_schema: dict[str, Any],
        fallback_output: dict[str, Any],
        sandbox_mode: str = "read-only",
        web_search_enabled: bool = False,
    ) -> CodexInvocationResult:
        auth_env = _resolve_auth_env()
        if not _has_agent_runtime(self.layout):
            _log(f"role={role} backend=fallback reason=missing_agent_runtime")
            return CodexInvocationResult(
                output=fallback_output,
                backend="fallback",
                thread_id=None,
                usage=None,
                events=[],
                raw_response=json.dumps(fallback_output, sort_keys=True),
            )

        if not auth_env:
            _log(f"role={role} backend=fallback reason=missing_api_key")
            return CodexInvocationResult(
                output=fallback_output,
                backend="fallback",
                thread_id=None,
                usage=None,
                events=[],
                raw_response=json.dumps(fallback_output, sort_keys=True),
            )

        _log(
            f"role={role} backend=codex_sdk sandbox={sandbox_mode} web_search={str(web_search_enabled).lower()} "
            f"auth_source={'env' if os.getenv('CODEX_API_KEY') or os.getenv('OPENAI_API_KEY') else str(DEFAULT_CODEX_AUTH_PATH)}"
        )
        request = {
            "role": role,
            "instructions": instructions,
            "payload": payload,
            "output_schema": output_schema,
            "working_directory": str(self.layout.root),
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "sandbox_mode": sandbox_mode,
            "web_search_enabled": web_search_enabled,
            "skip_git_repo_check": True,
        }

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
            request_path = Path(handle.name)
            json.dump(request, handle, sort_keys=True)

        try:
            try:
                result = subprocess.run(
                    ["node", str(self.layout.agent_runtime_dir / "codex_runner.mjs"), str(request_path)],
                    cwd=str(self.layout.root),
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=180,
                    env={**os.environ, **auth_env},
                )
            except subprocess.TimeoutExpired:
                _log(f"role={role} backend=fallback reason=runtime_timeout")
                return CodexInvocationResult(
                    output=fallback_output,
                    backend="fallback",
                    thread_id=None,
                    usage=None,
                    events=[],
                    raw_response=json.dumps(fallback_output, sort_keys=True),
                )
        finally:
            request_path.unlink(missing_ok=True)

        if result.returncode != 0:
            stderr = result.stderr.strip()
            _log(f"role={role} backend=fallback reason=runtime_error detail={stderr or result.stdout.strip()}")
            return CodexInvocationResult(
                output=fallback_output,
                backend="fallback",
                thread_id=None,
                usage=None,
                events=[],
                raw_response=json.dumps(fallback_output, sort_keys=True),
            )

        parsed = json.loads(result.stdout)
        invocation = CodexInvocationResult(
            output=dict(parsed.get("output", fallback_output)),
            backend=str(parsed.get("backend", "codex_sdk")),
            thread_id=parsed.get("thread_id"),
            usage=parsed.get("usage"),
            events=list(parsed.get("events", [])),
            raw_response=str(parsed.get("raw_response", "")),
        )
        _log(
            f"role={role} backend={invocation.backend} thread_id={invocation.thread_id} "
            f"events={len(invocation.events)}"
        )
        return invocation
