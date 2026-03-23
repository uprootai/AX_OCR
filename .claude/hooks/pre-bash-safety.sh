#!/bin/bash
# PreToolUse Hook: Bash safety rail
# - Uses JSON parsing instead of grep to avoid quoted command bypasses
# - Asks before destructive commands and denies catastrophic ones

set -euo pipefail

INPUT=$(cat)
[ -z "$INPUT" ] && exit 0

HOOK_INPUT="$INPUT" python3 - <<'PY'
import json
import os
import re
import shlex
import sys
from pathlib import Path

SAFE_CLEANUP_TARGETS = {
    "node_modules",
    ".next",
    "dist",
    "build",
    "__pycache__",
    ".cache",
    ".turbo",
    "coverage",
}
SHELL_NAMES = {"bash", "sh", "zsh"}
SEGMENT_SEPARATORS = {"&&", "||", ";", "|", "&"}


def emit(decision: str, message: str) -> None:
    payload = {
        "hookSpecificOutput": {"permissionDecision": decision},
        "systemMessage": message,
    }
    print(json.dumps(payload, ensure_ascii=True), file=sys.stderr)
    raise SystemExit(2)


def parse_command(raw: str) -> list[str]:
    try:
        return shlex.split(raw, posix=True)
    except ValueError:
        return []


def iter_command_variants(command: str) -> list[str]:
    variants: list[str] = []
    stack = [command]
    seen: set[str] = set()

    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        variants.append(current)

        tokens = parse_command(current)
        if not tokens:
            continue

        head = Path(tokens[0]).name
        if head not in SHELL_NAMES:
            continue

        for idx, token in enumerate(tokens[1:], start=1):
            if token in {"-c", "-lc", "-ic", "-cl"} and idx + 1 < len(tokens):
                stack.append(tokens[idx + 1])
                break

    return variants


def is_safe_cleanup_target(target: str) -> bool:
    cleaned = target.rstrip("/")
    if not cleaned:
        return False
    return Path(cleaned).name in SAFE_CLEANUP_TARGETS


def recursive_rm_targets(tokens: list[str]) -> list[str]:
    targets: list[str] = []

    for idx, token in enumerate(tokens):
        if token != "rm":
            continue

        recursive = False
        current_targets: list[str] = []
        for inner in tokens[idx + 1 :]:
            if inner in SEGMENT_SEPARATORS:
                break
            if inner == "--recursive":
                recursive = True
                continue
            if inner.startswith("-"):
                if "r" in inner[1:]:
                    recursive = True
                continue
            current_targets.append(inner)

        if recursive:
            targets.extend(current_targets)

    return targets


def is_rootlike_target(target: str) -> bool:
    cleaned = target.rstrip("/")
    return cleaned in {"/", "~"}


def detect_destructive_command(command: str) -> tuple[str, str] | None:
    for variant in iter_command_variants(command):
        lowered = variant.lower()
        tokens = parse_command(variant)

        if any(tok == "mkfs" or tok.startswith("mkfs.") for tok in tokens):
            return ("deny", f"Dangerous filesystem format blocked: {variant}")

        if "dd if=" in lowered and re.search(r"\bof=/dev/", lowered):
            return ("deny", f"Dangerous disk write blocked: {variant}")

        rm_targets = recursive_rm_targets(tokens)
        if rm_targets:
            if any(is_rootlike_target(target) for target in rm_targets):
                return ("deny", f"Recursive delete of root-like target blocked: {variant}")
            if not all(is_safe_cleanup_target(target) for target in rm_targets):
                return ("ask", f"Destructive recursive delete requires confirmation: {variant}")

        if tokens[:2] == ["git", "reset"] and "--hard" in tokens:
            return ("ask", f"History-destructive git reset requires confirmation: {variant}")

        if len(tokens) >= 3 and tokens[:2] == ["git", "checkout"] and "--" in tokens[2:]:
            return ("ask", f"Checkout discard requires confirmation: {variant}")

        if tokens[:2] == ["git", "clean"] and any(
            flag in token for token in tokens[2:] for flag in ("-f", "-d", "-x")
        ):
            return ("ask", f"git clean requires confirmation: {variant}")

        if tokens[:2] == ["git", "push"] and any(
            token in {"-f", "--force", "--force-with-lease"} for token in tokens[2:]
        ):
            return ("ask", f"Force push requires confirmation: {variant}")

        if tokens[:2] == ["docker", "system"] and "prune" in tokens[2:]:
            return ("ask", f"Docker system prune requires confirmation: {variant}")

        if tokens[:2] == ["docker", "volume"] and "prune" in tokens[2:]:
            return ("ask", f"Docker volume prune requires confirmation: {variant}")

        if re.search(r"\bdrop\s+(table|database)\b", lowered):
            return ("ask", f"Destructive SQL command requires confirmation: {variant}")

        if re.search(r"\btruncate(\s+table)?\b", lowered):
            return ("ask", f"Table truncation requires confirmation: {variant}")

    return None


data = json.loads(os.environ["HOOK_INPUT"])
command = data.get("tool_input", {}).get("command", "")
if not command:
    raise SystemExit(0)

decision = detect_destructive_command(command)
if decision is None:
    raise SystemExit(0)

emit(*decision)
PY
