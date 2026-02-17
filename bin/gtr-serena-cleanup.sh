#!/bin/bash
# gtr-serena-cleanup.sh - Unregister worktree from Serena MCP
# Usage: gtr-serena-cleanup.sh <worktree_path>
#
# This script:
# 1. Removes worktree path from global serena_config.yml
# 2. Optionally removes .serena directory (if worktree is being deleted)
#
# Called by gtr-finish before worktree removal

set -e

WORKTREE_PATH="$1"
ISSUE_NUMBER="$2"

# Validation
if [ -z "$WORKTREE_PATH" ]; then
    echo "Usage: gtr-serena-cleanup.sh <worktree_path> [issue_number]"
    exit 1
fi

# --- Sync memories to master before cleanup (diff merge) ---
MASTER_REPO=$(git worktree list --porcelain | grep '^worktree ' | head -1 | sed 's/^worktree //')

if [ -d "${WORKTREE_PATH}/.serena/memories" ] && [ -d "${MASTER_REPO}/.serena/memories" ]; then
    echo "   🔄 Syncing memories to master (diff merge)..."

    for mem in code_style project_overview suggested_commands task_completion_checklist; do
        src="${WORKTREE_PATH}/.serena/memories/${mem}.md"
        dst="${MASTER_REPO}/.serena/memories/${mem}.md"

        if [ -f "$src" ]; then
            if [ -f "$dst" ]; then
                # 差分マージ: ワークツリーにあってmasterにない行を追記
                # 重複行は追加しない
                diff_lines=$(diff "$dst" "$src" 2>/dev/null | grep '^>' | sed 's/^> //' || true)
                if [ -n "$diff_lines" ]; then
                    echo "" >> "$dst"
                    if [ -n "$ISSUE_NUMBER" ]; then
                        echo "# --- Merged from issue-${ISSUE_NUMBER} ($(date +%Y-%m-%d)) ---" >> "$dst"
                    else
                        echo "# --- Merged from worktree ($(date +%Y-%m-%d)) ---" >> "$dst"
                    fi
                    echo "$diff_lines" >> "$dst"
                    echo "   📝 Merged: ${mem}.md"
                else
                    echo "   ℹ️  No changes: ${mem}.md"
                fi
            else
                # masterにない場合はコピー
                cp "$src" "$dst"
                echo "   📝 Created: ${mem}.md"
            fi
        fi
    done
    echo "   ✅ Memories merged to master"
else
    if [ ! -d "${WORKTREE_PATH}/.serena/memories" ]; then
        echo "   ℹ️  No worktree memories to sync"
    elif [ ! -d "${MASTER_REPO}/.serena/memories" ]; then
        echo "   ⚠️  Master memories directory not found: ${MASTER_REPO}/.serena/memories"
    fi
fi

GLOBAL_CONFIG="$HOME/.serena/serena_config.yml"

# Remove from global serena_config.yml
if [ -f "$GLOBAL_CONFIG" ]; then
    if grep -q "^- ${WORKTREE_PATH}$" "$GLOBAL_CONFIG"; then
        # Use | as delimiter since path contains /
        sed -i "\|^- ${WORKTREE_PATH}$|d" "$GLOBAL_CONFIG"
        echo "   ✅ Serena unregistered: ${WORKTREE_PATH}"
    else
        echo "   ℹ️  Not in Serena config: ${WORKTREE_PATH}"
    fi
else
    echo "   ⚠️  Global config not found: $GLOBAL_CONFIG"
fi
