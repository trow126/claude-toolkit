#!/usr/bin/env bash
# UserPromptSubmit reminder delivery, byte bound, and fail-open fixtures.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOK="$REPO_ROOT/claude/hooks/prompt-submit-hook.sh"
SANDBOX="$(mktemp -d)"
trap 'rm -rf "$SANDBOX"' EXIT

STDOUT_FILE="$SANDBOX/stdout"
STDERR_FILE="$SANDBOX/stderr"
EXPECTED_FILE="$SANDBOX/expected"
FAILURES=0
CASE_RC=0

ok() { echo "ok: $1"; }
ng() {
  echo "FAIL: $1" >&2
  FAILURES=$((FAILURES + 1))
}

printf '%s\n' \
  '着手前に成功条件を決め、単一ownerで探索・実装・検証まで完遂する。' \
  '完了判定は一次情報・diff・test結果で自己監査し、未検証項目は明示する。' \
  > "$EXPECTED_FILE"

run_input() {
  local input="$1" hook="${2:-$HOOK}"
  : > "$STDOUT_FILE"
  : > "$STDERR_FILE"
  set +e
  printf '%s' "$input" | "$hook" >"$STDOUT_FILE" 2>"$STDERR_FILE"
  CASE_RC=${PIPESTATUS[1]}
  set -e
}

assert_success_and_exact_output() {
  local desc="$1"
  if [[ "$CASE_RC" -eq 0 ]]; then
    ok "$desc: exit 0"
  else
    ng "$desc: expected exit 0, got $CASE_RC"
  fi
  if cmp -s "$EXPECTED_FILE" "$STDOUT_FILE"; then
    ok "$desc: stdout は指定の2行と完全一致"
  else
    ng "$desc: stdout が指定文と一致しない"
  fi
}

run_input '{"hook_event_name":"UserPromptSubmit","user_prompt":"fixture","cwd":"/tmp"}'
assert_success_and_exact_output "valid UserPromptSubmit JSON"
if [[ ! -s "$STDERR_FILE" ]]; then
  ok "normal case: stderr は空"
else
  ng "normal case: stderr に出力された: $(<"$STDERR_FILE")"
fi

bytes="$(wc -c < "$STDOUT_FILE")"
if [[ "$bytes" -gt 0 && "$bytes" -le 256 ]]; then
  ok "stdout は256 bytes以下 ($bytes)"
else
  ng "stdout byte数が不正 ($bytes)"
fi

run_input 'not-json'
assert_success_and_exact_output "非 JSON stdin"

run_input ''
assert_success_and_exact_output "空 stdin"

OVERSIZED_HOOK="$SANDBOX/prompt-submit-hook.sh"
cp "$HOOK" "$OVERSIZED_HOOK"
python3 - "$OVERSIZED_HOOK" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
replacement = "INJECTION_TEXT='" + ("x" * 400) + "'\n\ncat"
text, count = re.subn(
    r"INJECTION_TEXT='.*?'\n\ncat",
    replacement,
    text,
    count=1,
    flags=re.DOTALL,
)
if count != 1:
    raise SystemExit("failed to replace INJECTION_TEXT fixture")
path.write_text(text, encoding="utf-8")
PY
run_input '{"hook_event_name":"UserPromptSubmit"}' "$OVERSIZED_HOOK"
if [[ "$CASE_RC" -eq 0 ]]; then
  ok "400-byte message: exit 0"
else
  ng "400-byte message: expected exit 0, got $CASE_RC"
fi
if [[ ! -s "$STDOUT_FILE" ]]; then
  ok "400-byte message: stdout は空"
else
  ng "400-byte message: stdout が空ではない"
fi

printf '\n'
if [[ "$FAILURES" -eq 0 ]]; then
  echo "PASS: all assertions succeeded"
  exit 0
fi
echo "FAIL: $FAILURES assertion(s) failed" >&2
exit 1
