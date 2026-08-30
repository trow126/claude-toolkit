#!/bin/bash
# ConfigChange hook: block unsafe user/project settings changes fail-closed.
# The definitive runtime gate also runs before every Bash tool call because
# SessionStart hooks cannot prevent session startup.
set -euo pipefail

block() {
    echo "Blocked: $*" >&2
    exit 2
}

command -v jq >/dev/null 2>&1 || block "config-change-hook requires jq (fail-closed)"
INPUT=$(cat) || block "failed to read ConfigChange input"
if ! printf '%s\n' "$INPUT" | jq -e 'type == "object"' >/dev/null 2>&1; then
    block "ConfigChange input is not valid JSON"
fi

# Parse only the official ConfigChange fields documented at
# https://code.claude.com/docs/en/hooks.
if ! printf '%s\n' "$INPUT" | jq -e '(.source | type) == "string"' >/dev/null 2>&1; then
    block "ConfigChange source must be a string"
fi
SOURCE=$(printf '%s\n' "$INPUT" | jq -r '.source' 2>/dev/null) || \
    block "ConfigChange source cannot be parsed"
case "$SOURCE" in
    user_settings|project_settings|local_settings|policy_settings|skills) ;;
    *) block "unknown ConfigChange source: $SOURCE" ;;
esac

FILE_PRESENT=false
FILE_PATH=""
if printf '%s\n' "$INPUT" | jq -e 'has("file_path")' >/dev/null 2>&1; then
    FILE_PRESENT=true
    if ! printf '%s\n' "$INPUT" | jq -e '(.file_path | type) == "string"' >/dev/null 2>&1; then
        block "ConfigChange file_path must be a string"
    fi
    FILE_PATH=$(printf '%s\n' "$INPUT" | jq -r '.file_path' 2>/dev/null) || \
        block "ConfigChange file_path cannot be parsed"
elif [[ "$SOURCE" != "policy_settings" ]]; then
    block "ConfigChange file_path is required for source: $SOURCE"
fi

HOOK_CWD=$(printf '%s\n' "$INPUT" | jq -r \
    'if (.cwd | type) == "string" and .cwd != "" then .cwd else "" end' 2>/dev/null) || \
    block "ConfigChange cwd cannot be parsed"
[[ -n "$HOOK_CWD" ]] || HOOK_CWD="$PWD"
if [[ "$FILE_PRESENT" == true && "$FILE_PATH" != /* ]]; then
    FILE_PATH="$HOOK_CWD/$FILE_PATH"
fi

case "$SOURCE" in
    user_settings)
        # User settings are linked toolkit preferences; edit them outside the
        # running session and restart so composition is revalidated.
        block "~/.claude/settings.json must be edited via shell, then Claude restarted (CLAUDE.md)"
        ;;
    policy_settings)
        # Managed policy changes cannot be blocked by ConfigChange.
        exit 0
        ;;
    skills)
        # Skills are not a settings surface, so the project policy gate is irrelevant.
        exit 0
        ;;
esac

HOOK_DIR="$(cd "${BASH_SOURCE[0]%/*}" && pwd -P)" || block "cannot resolve hook directory"
PROJECT_POLICY_GATE="$HOOK_DIR/../bin/project-policy-gate"
[[ -x "$PROJECT_POLICY_GATE" ]] || block "project-policy-gate is missing or not executable"
if ! GATE_OUTPUT=$("$PROJECT_POLICY_GATE" --cwd "$HOOK_CWD" --quiet 2>&1); then
    block "unsafe project/local Claude settings: $GATE_OUTPUT"
fi

exit 0
