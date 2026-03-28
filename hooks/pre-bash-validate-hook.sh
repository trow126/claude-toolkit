#!/bin/bash
# PreToolUse hook: validate Bash commands before execution
# Blocks dangerous patterns by exiting with code 2 + stderr message
# Only checks tool_input.command from Claude's Bash tool calls

set -euo pipefail

INPUT=$(cat)

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

if [ -z "$COMMAND" ]; then
    exit 0
fi

# Block writes to block devices
if echo "$COMMAND" | grep -qE '(>|of=)\s*/dev/sd'; then
    echo "Blocked: write to block device detected in command" >&2
    exit 2
fi

# Block mkfs on block devices
if echo "$COMMAND" | grep -qE 'mkfs\S*\s+/dev/sd'; then
    echo "Blocked: mkfs on block device detected" >&2
    exit 2
fi

exit 0
