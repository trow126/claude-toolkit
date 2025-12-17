---
name: gh:start
description: GitHub Issue駆動開発（簡略版v3）。Issue取得→逐次実行→進捗同期の3フェーズで確実に実行。
category: workflow
complexity: standard
---

# /gh:start - GitHub Issue駆動開発

> **原則**: GitHub Issue = SSOT、TodoWrite = 進捗追跡、逐次実行 = 確実性

## Usage

```bash
/gh:start 42        # Issue #42 で作業開始
/gh:start           # アクティブIssue自動検出
```

---

## Phase 1: Fetch (Issue取得)

1. **Issue取得**: `gh-issue-fetch.sh ${ISSUE_NUMBER}` を実行
2. **出力確認**: JSON形式で tasks, statistics を取得
3. **エラー時**: Issue番号確認を促す

```bash
# 実行コマンド
gh-issue-fetch.sh 42
```

**成功条件**: exit 0 + 有効なJSON + state == "open"

---

## Phase 2: Execute (実装)

1. **TodoWrite構築**:
   - pending タスクのみ抽出
   - 各タスクに content, status, activeForm を設定

2. **逐次実行** (タスクごとに):
   - TodoWrite → `in_progress` に更新
   - Task tool でサブエージェントに委譲して実装
   - 完了後 → TodoWrite → `completed` に更新

3. **エラー時**: エラー内容を表示して停止

**実行ルール**:
- 1タスクずつ確実に完了させる（並列実行なし）
- 各タスク完了時にTodoWrite状態を即座に更新
- 失敗したらユーザーに報告して指示を待つ

---

## Phase 3: Sync (GitHub同期)

1. **進捗更新**: `gh-progress-sync.sh` で GitHub Issue に進捗コメント投稿
2. **チェックボックス更新**: 完了タスクを `[x]` にマーク
3. **全完了時**: PR作成を提案（`Closes #N` 含む）

```bash
# 進捗同期
echo '{"issue": 42, "completed": [1,2], "total": 5, "task_name": "Task name"}' | gh-progress-sync.sh

# タスク個別チェック
gh-progress-sync.sh --check-task 42 "Implement login button"
```

---

## Error Handling

| フェーズ | エラー | 対応 |
|----------|--------|------|
| Fetch | Issue not found | Issue番号を確認してください |
| Fetch | Issue closed | 既にクローズ済みです |
| Execute | 実装失敗 | エラー内容を確認し、手動で対応してください |
| Sync | コメント失敗 | `gh issue comment` で手動投稿してください |

---

## Examples

### 基本的な使い方
```
User: /gh:start 42

Claude:
1. [Fetch] gh-issue-fetch.sh 42 実行
2. [Parse] 5タスク検出 (3 pending)
3. [TodoWrite] 3タスクを登録
4. [Execute] Task 1 開始...
   ... Task 1 完了
   Task 2 開始...
   ... Task 2 完了
   Task 3 開始...
   ... Task 3 完了
5. [Sync] GitHub更新完了
6. [Done] 全タスク完了。PR作成しますか？
```

---

## Related Commands

- `/gh:issue` - Issue管理（作成・クローズ）
- `/gh:review` - CodeRabbitレビュー対応
- `/gh:gtr-start` - Git Worktree統合

---

## Technical Details

**Scripts**:
- `~/.local/bin/gh-issue-fetch.sh` - Issue取得・パース
- `~/.local/bin/gh-progress-sync.sh` - GitHub同期
- `~/.claude/skills/issue-parser/scripts/parse_issue.py` - Markdownパース

**依存**:
- `gh` CLI (GitHub CLI)
- `jq` (JSONパース)
- `python3` (パーサースクリプト)
