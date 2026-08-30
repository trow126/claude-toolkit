#!/usr/bin/env bash
# test-config-change-hook.sh — ConfigChange official schema and policy routing tests
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOK="$REPO_ROOT/claude/hooks/config-change-hook.sh"

SANDBOX="$(mktemp -d)"
cleanup() { rm -rf "$SANDBOX"; }
trap cleanup EXIT

TEST_HOME="$SANDBOX/home"
PROJECT_ROOT="$SANDBOX/project"
mkdir -p "$TEST_HOME/.claude" "$PROJECT_ROOT/.git" "$PROJECT_ROOT/.claude"

FAILURES=0
ok() { echo "ok: $1"; }
ng() {
  echo "FAIL: $1" >&2
  FAILURES=$((FAILURES + 1))
}

expect_exit() {
  local desc="$1" expected="$2" payload="$3" rc=0
  printf '%s\n' "$payload" | env HOME="$TEST_HOME" "$HOOK" >/dev/null 2>&1 || rc=$?
  if [[ "$rc" -eq "$expected" ]]; then
    ok "$desc"
  else
    ng "$desc (expected exit $expected, got $rc)"
  fi
}

config_input() {
  local source="$1" file_path="$2"
  jq -cn \
    --arg source "$source" \
    --arg file_path "$file_path" \
    --arg cwd "$PROJECT_ROOT" \
    '{
      "hook_event_name": "ConfigChange",
      "source": $source,
      "file_path": $file_path,
      "cwd": $cwd
    }'
}

# ---- 1. source routing ----
payload="$(config_input user_settings "$TEST_HOME/.claude/settings.json")"
expect_exit "user_settings の absolute file_path は source により block" 2 "$payload"
payload="$(config_input user_settings '.claude/settings.json')"
expect_exit "user_settings の relative file_path も source により block" 2 "$payload"

printf '%s\n' '{"model":"sonnet","env":{"PROJECT_FLAVOR":"test"}}' \
  > "$PROJECT_ROOT/.claude/settings.json"
payload="$(config_input project_settings '.claude/settings.json')"
expect_exit "safe project_settings の relative file_path は許可" 0 "$payload"
printf '%s\n' '{"sandbox":{"enabled":false}}' \
  > "$PROJECT_ROOT/.claude/settings.json"
expect_exit "unsafe project_settings は project-policy-gate が block" 2 "$payload"
rm -f "$PROJECT_ROOT/.claude/settings.json"

printf '%s\n' '{"model":"sonnet","env":{"PROJECT_FLAVOR":"test"}}' \
  > "$PROJECT_ROOT/.claude/settings.local.json"
payload="$(config_input local_settings '.claude/settings.local.json')"
expect_exit "safe local_settings の relative file_path は許可" 0 "$payload"
printf '%s\n' '{"sandbox":{"enabled":false}}' \
  > "$PROJECT_ROOT/.claude/settings.local.json"
expect_exit "unsafe local_settings は project-policy-gate が block" 2 "$payload"
rm -f "$PROJECT_ROOT/.claude/settings.local.json"

payload="$(jq -cn --arg cwd "$PROJECT_ROOT" \
  '{"hook_event_name":"ConfigChange","source":"policy_settings","cwd":$cwd}')"
expect_exit "policy_settings は file_path なしで許可" 0 "$payload"
payload="$(config_input skills '.claude/skills/example/SKILL.md')"
expect_exit "skills は settings surface ではないため許可" 0 "$payload"

# ---- 2. malformed and legacy inputs fail closed ----
payload="$(jq -cn --arg cwd "$PROJECT_ROOT" \
  '{"hook_event_name":"ConfigChange","file_path":".claude/settings.json","cwd":$cwd}')"
expect_exit "source 欠落は block" 2 "$payload"
payload="$(config_input unknown_settings '.claude/settings.json')"
expect_exit "未知の source は block" 2 "$payload"
payload="$(jq -cn --arg cwd "$PROJECT_ROOT" \
  '{"hook_event_name":"ConfigChange","source":1,"file_path":".claude/settings.json","cwd":$cwd}')"
expect_exit "非 string source は block" 2 "$payload"
payload="$(jq -cn --arg cwd "$PROJECT_ROOT" \
  '{"hook_event_name":"ConfigChange","source":"project_settings","file_path":1,"cwd":$cwd}')"
expect_exit "非 string file_path は block" 2 "$payload"
payload="$(jq -cn --arg cwd "$PROJECT_ROOT" \
  '{"hook_event_name":"ConfigChange","source":"project_settings","cwd":$cwd}')"
expect_exit "project_settings の file_path 欠落は block" 2 "$payload"
expect_exit "legacy tool_input.file_path だけの入力は block" 2 \
  '{"tool_input":{"file_path":"~/.claude/settings.json"}}'
expect_exit "legacy path だけの入力は block" 2 \
  '{"path":".claude/settings.json"}'
expect_exit "non-JSON input は block" 2 'not-json'

echo
if [[ "$FAILURES" -eq 0 ]]; then
  echo "PASS: all assertions succeeded"
  exit 0
else
  echo "FAIL: $FAILURES assertion(s) failed" >&2
  exit 1
fi
