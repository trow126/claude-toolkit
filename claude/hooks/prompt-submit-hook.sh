#!/usr/bin/env bash
# UserPromptSubmit delivery hook: https://code.claude.com/docs/en/hooks
# This reminder is deliberately fail-open and never acts as a gate. Every
# delivery failure exits 0 silently so a prompt cannot be blocked by the hook.

MAX_INJECTION_BYTES=256
INJECTION_TEXT='着手前に成功条件を決め、単一ownerで探索・実装・検証まで完遂する。
完了判定は一次情報・diff・test結果で自己監査し、未検証項目は明示する。'

cat >/dev/null 2>/dev/null || true

LC_ALL=C
injection_bytes=$((${#INJECTION_TEXT} + 1))
if ((injection_bytes > MAX_INJECTION_BYTES)); then
    exit 0
fi

printf '%s\n' "$INJECTION_TEXT" 2>/dev/null || true
exit 0
