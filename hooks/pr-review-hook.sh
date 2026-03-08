#!/bin/bash
# PostToolUse hook: detect gh pr create and trigger auto-review

TOOL_INPUT_JSON="${TOOL_INPUT:-}"

# Check if the Bash command contained gh pr create
if echo "$TOOL_INPUT_JSON" | grep -q "gh pr create"; then
  # Check tool output for success (PR URL present)
  TOOL_OUTPUT_JSON="${TOOL_OUTPUT:-}"
  if echo "$TOOL_OUTPUT_JSON" | grep -qE "https://github\.com/.+/pull/[0-9]+"; then
    echo "PR作成を検出。PRレビュー手順を実行してください："
    echo "1. gh pr view --json number -q '.number' でPR番号を取得"
    echo "2. gh pr diff <PR番号> で差分を取得"
    echo "3. Task subagent でコードレビューを実施（自己レビュー防止のため別コンテキスト）"
    echo "4. レビュー結果を gh pr comment <PR番号> --body でPRコメントに投稿"
  fi
fi
