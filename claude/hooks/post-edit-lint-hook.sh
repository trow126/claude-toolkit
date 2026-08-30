#!/bin/bash
# PostToolUse lint feedback for Edit/Write.
#
# This hook is deliberately fail-open: missing dependencies, malformed input,
# unreadable/deleted files, a missing helper, and unexpected internal errors
# exit 0 silently. Only confirmed lint violations exit 2, because a linter bug
# must never break an editing session.

command -v jq >/dev/null 2>&1 || exit 0

INPUT=$(cat 2>/dev/null) || exit 0
if ! TOOL_NAME=$(printf '%s\n' "$INPUT" | jq -er \
    '.tool_name | select(type == "string")' 2>/dev/null); then
    exit 0
fi
case "$TOOL_NAME" in
    Edit|Write) ;;
    *) exit 0 ;;
esac

if ! FILE_PATH=$(printf '%s\n' "$INPUT" | jq -er \
    '.tool_input.file_path | select(type == "string")' 2>/dev/null); then
    exit 0
fi

command -v python3 >/dev/null 2>&1 || exit 0
HOOK_DIR=$( { cd "${BASH_SOURCE[0]%/*}" && pwd -P; } 2>/dev/null) || exit 0
LINTER="$HOOK_DIR/lib/post_edit_lint.py"
[[ -f "$LINTER" ]] || exit 0

LINT_OUTPUT=$(python3 "$LINTER" "$FILE_PATH" 2>&1 >/dev/null)
LINT_STATUS=$?
if [[ "$LINT_STATUS" -eq 2 ]]; then
    printf '%s\n' "$LINT_OUTPUT" >&2
    exit 2
fi

exit 0
