from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
BASH_HOOK = HOOKS_DIR / "pre-bash-safety.sh"
WRITE_HOOK = HOOKS_DIR / "pre-write-safety.sh"


def run_hook(
    script: Path,
    payload: dict[str, object],
    *,
    cwd: Path | None = None,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(script)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=str(cwd or REPO_ROOT),
        env=env,
        check=False,
    )


def parse_hook_stderr(result: subprocess.CompletedProcess[str]) -> dict[str, object]:
    assert result.stderr.strip(), "expected hook stderr JSON"
    return json.loads(result.stderr)


def test_bash_hook_allows_safe_readonly_command() -> None:
    payload = {"tool_input": {"command": "ls -la .claude/hooks"}}
    result = run_hook(BASH_HOOK, payload)

    assert result.returncode == 0
    assert result.stderr == ""


def test_bash_hook_blocks_nested_recursive_delete() -> None:
    payload = {"tool_input": {"command": 'bash -lc "rm -rf /tmp/pwn"'}}
    result = run_hook(BASH_HOOK, payload)

    assert result.returncode == 2
    body = parse_hook_stderr(result)
    assert body["hookSpecificOutput"]["permissionDecision"] == "ask"
    assert "rm -rf /tmp/pwn" in body["systemMessage"]


def test_bash_hook_allows_safe_cleanup_targets() -> None:
    payload = {"tool_input": {"command": "rm -rf dist coverage __pycache__"}}
    result = run_hook(BASH_HOOK, payload)

    assert result.returncode == 0
    assert result.stderr == ""


def test_write_hook_denies_prefix_boundary_bypass(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    freeze_root = project_root / "app"
    outside_prefix = project_root / "application"
    state_dir = project_root / ".gstack" / "state"

    freeze_root.mkdir(parents=True)
    outside_prefix.mkdir(parents=True)
    state_dir.mkdir(parents=True)
    (state_dir / "freeze-dir.txt").write_text(str(freeze_root), encoding="utf-8")

    payload = {"tool_input": {"file_path": str(outside_prefix / "notes.txt")}}
    result = run_hook(
        WRITE_HOOK,
        payload,
        cwd=project_root,
        extra_env={"AX_HOOK_PROJECT_ROOT": str(project_root)},
    )

    assert result.returncode == 2
    body = parse_hook_stderr(result)
    assert body["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "outside the active edit scope" in body["systemMessage"]


def test_write_hook_allows_inside_freeze_dir_with_spaces(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    freeze_root = project_root / "app name"
    state_dir = project_root / ".gstack" / "state"

    (freeze_root / "nested").mkdir(parents=True)
    state_dir.mkdir(parents=True)
    (state_dir / "freeze-dir.txt").write_text(str(freeze_root), encoding="utf-8")

    payload = {"tool_input": {"file_path": str(freeze_root / "nested" / "file.txt")}}
    result = run_hook(
        WRITE_HOOK,
        payload,
        cwd=project_root,
        extra_env={"AX_HOOK_PROJECT_ROOT": str(project_root)},
    )

    assert result.returncode == 0
    assert result.stderr == ""


def test_write_hook_asks_for_sensitive_file_even_without_freeze(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir(parents=True)

    payload = {"tool_input": {"file_path": str(project_root / ".env")}}
    result = run_hook(
        WRITE_HOOK,
        payload,
        cwd=project_root,
        extra_env={"AX_HOOK_PROJECT_ROOT": str(project_root)},
    )

    assert result.returncode == 2
    body = parse_hook_stderr(result)
    assert body["hookSpecificOutput"]["permissionDecision"] == "ask"
    assert "Sensitive file edit requires confirmation" in body["systemMessage"]
