#!/usr/bin/env python3
"""Measure deterministic hook systemMessage output for a controlled fixture."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path


def run(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str],
    check: bool = True,
    input_data: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        check=check,
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def run_hook(
    path: Path,
    cwd: Path,
    env: dict[str, str],
    strict_json: bool,
    input_data: bytes | None = None,
) -> int:
    if not path.is_file():
        return 0
    proc = run([str(path)], cwd, env, input_data=input_data)
    if strict_json:
        try:
            data = json.loads(proc.stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SystemExit(f"ERROR: hook emitted invalid JSON: {path}: {exc}; stderr={proc.stderr.decode(errors='replace')}")
        if not isinstance(data, dict) or not isinstance(data.get("systemMessage"), str):
            raise SystemExit(f"ERROR: hook output lacks string systemMessage: {path}")
    return len(proc.stdout)


def max_bytes(root: Path) -> str:
    hooks = [root / "claude/hooks/session-init-hook.sh", root / "claude/hooks/post-compact-hook.sh"]
    if not any(path.is_file() for path in hooks):
        return "0"
    helper = root / "claude/hooks/lib/emit_system_message.py"
    if not helper.is_file():
        return "unbounded"
    text = helper.read_text(encoding="utf-8")
    match = re.search(r"^MAX_OUTPUT_BYTES\s*=\s*([0-9]+)\s*$", text, re.M)
    if not match:
        raise SystemExit("ERROR: bounded hook emitter is missing MAX_OUTPUT_BYTES")
    return match.group(1)


def prompt_submit_max_bytes(path: Path) -> str:
    if not path.is_file():
        return "0"
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^MAX_INJECTION_BYTES=([0-9]+)$", text, re.M)
    if not match:
        raise SystemExit(
            "ERROR: prompt submit hook is missing MAX_INJECTION_BYTES"
        )
    return match.group(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()

    with tempfile.TemporaryDirectory(prefix="agents-toolkit-hook-metrics-") as tmp_s:
        tmp = Path(tmp_s)
        repo = tmp / "repo"
        home = tmp / "home"
        repo.mkdir()
        home.mkdir()
        env = os.environ.copy()
        env.update({
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "XDG_STATE_HOME": str(home / ".local/state"),
            "XDG_DATA_HOME": str(home / ".local/share"),
            "XDG_CACHE_HOME": str(home / ".cache"),
            "LC_ALL": "C.UTF-8",
        })
        run(["git", "init", "-q", "-b", "main"], repo, env)
        run(["git", "config", "user.email", "fixture@example.invalid"], repo, env)
        run(["git", "config", "user.name", "Fixture"], repo, env)
        run(["git", "config", "commit.gpgsign", "false"], repo, env)
        (repo / "README.md").write_text("baseline\n", encoding="utf-8")
        run(["git", "add", "README.md"], repo, env)
        run(["git", "commit", "-q", "-m", "fixture baseline"], repo, env)
        (repo / "README.md").write_text("baseline\nchanged\n", encoding="utf-8")

        strict_json = (root / "claude/hooks/lib/emit_system_message.py").is_file()
        session = run_hook(root / "claude/hooks/session-init-hook.sh", repo, env, strict_json)
        run(["git", "add", "README.md"], repo, env)
        compact = run_hook(root / "claude/hooks/post-compact-hook.sh", repo, env, strict_json)
        bound = max_bytes(root)
        prompt_hook = root / "claude/hooks/prompt-submit-hook.sh"
        prompt_input = json.dumps(
            {
                "hook_event_name": "UserPromptSubmit",
                "user_prompt": "fixture",
                "cwd": str(repo),
            }
        ).encode("utf-8")
        prompt_submit = run_hook(
            prompt_hook,
            repo,
            env,
            strict_json=False,
            input_data=prompt_input,
        )
        prompt_bound = prompt_submit_max_bytes(prompt_hook)

    print(f"session_start_system_message_typical_bytes: {session}")
    print(f"session_start_system_message_max_bytes: {bound}")
    print(f"post_compact_system_message_typical_bytes: {compact}")
    print(f"post_compact_system_message_max_bytes: {bound}")
    print(f"user_prompt_submit_injection_typical_bytes: {prompt_submit}")
    print(f"user_prompt_submit_injection_max_bytes: {prompt_bound}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
