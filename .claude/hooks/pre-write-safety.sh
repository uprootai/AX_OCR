#!/bin/bash
# PreToolUse Hook: Edit/Write scope and sensitive path safety rail
# - Enforces repo-local freeze boundary when active
# - Uses resolve(strict=False) to avoid prefix/path-space bypasses

set -euo pipefail

INPUT=$(cat)
[ -z "$INPUT" ] && exit 0

PROJECT_ROOT="${AX_HOOK_PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
STATE_DIR="${AX_HOOK_STATE_DIR:-${PROJECT_ROOT}/.gstack/state}"

HOOK_INPUT="$INPUT" AX_HOOK_PROJECT_ROOT="$PROJECT_ROOT" AX_HOOK_STATE_DIR="$STATE_DIR" python3 - <<'PY'
import json
import os
import sys
from pathlib import Path


def emit(decision: str, message: str) -> None:
    payload = {
        "hookSpecificOutput": {"permissionDecision": decision},
        "systemMessage": message,
    }
    print(json.dumps(payload, ensure_ascii=True), file=sys.stderr)
    raise SystemExit(2)


def resolve_from_root(root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = root / path
    return path.resolve(strict=False)


def is_sensitive_path(path: Path) -> bool:
    name = path.name.lower()
    path_str = str(path).lower()
    return (
        name in {".env", ".env.local", ".env.production", ".env.development"}
        or name.endswith(".pem")
        or name.endswith(".key")
        or "credentials" in path_str
        or "secrets" in path_str
    )


project_root = Path(os.environ["AX_HOOK_PROJECT_ROOT"]).resolve(strict=False)
state_dir = Path(os.environ["AX_HOOK_STATE_DIR"]).resolve(strict=False)
freeze_file = state_dir / "freeze-dir.txt"

data = json.loads(os.environ["HOOK_INPUT"])
raw_file_path = data.get("tool_input", {}).get("file_path", "")
if not raw_file_path:
    raise SystemExit(0)

candidate = resolve_from_root(project_root, raw_file_path)

if is_sensitive_path(candidate):
    emit("ask", f"Sensitive file edit requires confirmation: {candidate}")

if freeze_file.exists():
    freeze_raw = freeze_file.read_text(encoding="utf-8").strip()
    if freeze_raw:
        freeze_root = resolve_from_root(project_root, freeze_raw)
        try:
            inside = os.path.commonpath([str(candidate), str(freeze_root)]) == str(freeze_root)
        except ValueError:
            inside = False

        if not inside:
            emit(
                "deny",
                f"[freeze] Blocked: {candidate} is outside the active edit scope ({freeze_root}).",
            )

raise SystemExit(0)
PY
