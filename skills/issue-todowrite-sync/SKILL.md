---
name: issue-todowrite-sync
description: Synchronize GitHub Issues with TodoWrite tasks bidirectionally. Converts Issue tasks to TodoWrite format and updates GitHub Issues when TodoWrite tasks complete. Integrates with checkpoint-manager for Compact resilience. Use when starting work on Issues, managing task progress, converting Issues to todos, or syncing Issue status. Activates on "work on Issue", "convert to TodoWrite", "sync progress", or explicit "use issue-todowrite-sync skill".
allowed-tools: TodoWrite, Bash, Read
---

# Issue-TodoWrite Sync Skill

Provides bidirectional synchronization between GitHub Issues and TodoWrite tasks.

## What This Skill Does

### Issue → TodoWrite Conversion
- Converts parsed Issue tasks to TodoWrite format
- Generates proper `activeForm` for each task (e.g., "実装" → "実装中", "Implement" → "Implementing")
- Maintains task-to-Issue mapping in session memory
- Preserves completion status from GitHub
- **Generates checkpoint data for checkpoint-manager skill**

### TodoWrite → Issue Synchronization
- Posts progress comments to GitHub when tasks complete
- Updates completion percentage automatically
- Auto-closes Issues when all tasks are done (optional)
- Tracks sync state within current session
- **Triggers checkpoint updates on task completion**

### Checkpoint Integration (Compact耐性)
- Generates `task_mapping` for checkpoint-manager skill
- Provides data for checkpoint creation after conversion
- Supports recovery mode: rebuilds TodoWrite from checkpoint

## When to Use

This skill automatically activates when you:
- Say "work on Issue #42"
- Request "convert Issue to TodoWrite"
- Mention "sync Issue progress"
- Complete TodoWrite tasks linked to an Issue

Explicit invocation: **"use issue-todowrite-sync skill for Issue #42"**

## How It Works

### Part 1: Issue → TodoWrite

#### Input
Requires parsed Issue data (from `issue-parser` skill):
```json
{
  "issue_number": 42,
  "title": "Feature: Authentication",
  "tasks": [
    {"id": 1, "text": "API実装", "completed": false, "phase": "Backend"},
    {"id": 2, "text": "テスト作成", "completed": false, "phase": "Testing"}
  ]
}
```

#### Process
1. **Convert to TodoWrite format**
   ```bash
   cat parsed_issue.json | \
     python3 ~/.claude/skills/issue-todowrite-sync/scripts/convert_to_todowrite.py
   ```

2. **Apply to TodoWrite**
   Use TodoWrite tool with converted tasks

3. **Store mapping in session**
   Task-to-Issue mapping maintained in current session context

#### Output
```json
{
  "issue_number": 42,
  "issue_title": "Feature: Authentication",
  "todowrite_tasks": [
    {
      "content": "API実装",
      "status": "pending",
      "activeForm": "API実装中"
    },
    {
      "content": "テスト作成",
      "status": "pending",
      "activeForm": "テスト作成中"
    }
  ],
  "task_mapping": [
    {
      "todowrite_index": 0,
      "github_task_id": 1,
      "text": "API実装",
      "phase": "Backend",
      "status": "pending"
    },
    {
      "todowrite_index": 1,
      "github_task_id": 2,
      "text": "テスト作成",
      "phase": "Testing",
      "status": "pending"
    }
  ],
  "checkpoint_data": {
    "issue_number": 42,
    "issue_title": "Feature: Authentication",
    "phases": ["Backend", "Testing"],
    "task_mapping": "..."
  }
}
```

**⚠️ checkpoint_dataは checkpoint-manager skillに渡してcheckpoint作成に使用**

### Part 2: TodoWrite → Issue Sync

#### Trigger
When TodoWrite task is marked complete

#### Process
1. **Read mapping from session**
   Retrieve task-to-Issue mapping from current session context

2. **Calculate progress**
   - Count completed vs total tasks
   - Calculate completion percentage

3. **Sync to GitHub**
   ```bash
   echo '{
     "issue_number": 42,
     "completed_task": {"content": "API実装"},
     "completed_count": 1,
     "total_count": 2,
     "auto_close": true
   }' | python3 ~/.claude/skills/issue-todowrite-sync/scripts/sync_progress.py
   ```

#### Result
- Posts comment to Issue #42: "✅ Task Completed: API実装\n\nProgress: 1/2 tasks (50%)"
- Auto-closes Issue if all tasks complete (when `auto_close: true`)

## Usage Examples

### Example 1: Convert Issue to TodoWrite
```
User: "Work on Issue #42"
Claude:
  1. Uses issue-parser skill to extract tasks
  2. Uses issue-todowrite-sync skill to convert
  3. Creates TodoWrite tasks:
     ✓ 1. API実装
     ⏳ 2. テスト作成
  4. Stores mapping in session context
```

### Example 2: Sync Progress
```
User: (Marks "API実装" as complete in TodoWrite)
Claude:
  1. Detects completion via issue-todowrite-sync skill
  2. Reads mapping from session context
  3. Posts to GitHub Issue #42:
     "✅ Task Completed: API実装
      Progress: 1/2 tasks (50%)"
```

### Example 3: Auto-Close on Completion
```
User: (Marks final task complete)
Claude:
  1. Detects all tasks completed
  2. Posts completion comment to Issue #42
  3. Closes Issue with reason: "completed"
```

### Example 4: Explicit Sync Request
```
User: "Sync progress for Issue #42"
Claude:
  1. Reads current TodoWrite state
  2. Reads mapping from session context
  3. Calculates progress difference
  4. Posts update to GitHub if changed
```

## Configuration Options

### Auto-Close Behavior
By default, Issues auto-close when all tasks complete. To disable:
```
User: "Sync Issue #42 but don't auto-close"
Claude: (Sets auto_close: false in sync_data)
```

### Active Form Generation
Automatically converts task text to active form:
- Japanese: "実装" → "実装中", "作成" → "作成中"
- English: "Implement" → "Implementing", "Create" → "Creating"
- Fallback: Appends "中" (Japanese) or "(in progress)" (English)

## Error Handling

- **Missing session data**: Warns user that Issue not tracked in current session (use `/gh:issue work` to start)
- **GitHub API error**: Retries once, then logs error
- **TodoWrite conflict**: Preserves local state, warns about sync issue
- **Network failure**: Retry on next sync attempt

## Files

- `SKILL.md`: This documentation
- `scripts/convert_to_todowrite.py`: Issue → TodoWrite converter
- `scripts/sync_progress.py`: TodoWrite → GitHub syncer

## Dependencies

- `gh` CLI (GitHub CLI)
- Python 3.6+
- TodoWrite tool

## Testing

### Test Conversion
```bash
# Sample parsed Issue
echo '{
  "issue_number": 1,
  "title": "Test",
  "tasks": [
    {"id": 1, "text": "API実装", "completed": false, "phase": "Backend"}
  ]
}' | python3 ~/.claude/skills/issue-todowrite-sync/scripts/convert_to_todowrite.py
```

### Test Sync
```bash
# Sample sync data
echo '{
  "issue_number": 1,
  "completed_task": {"content": "API実装"},
  "completed_count": 1,
  "total_count": 2,
  "auto_close": false
}' | python3 ~/.claude/skills/issue-todowrite-sync/scripts/sync_progress.py
```

## Integration Points

Works with:
- **issue-parser**: Receives parsed Issue data
- **progress-tracker**: Triggers on TodoWrite completion events
- **checkpoint-manager**: Provides data for checkpoint creation and recovery
- **/gh:issue command**: Primary workflow integration
- **/gh:start command**: Checkpoint recovery mode integration

### Checkpoint Manager Integration

#### After Conversion (Part 1)
```yaml
Output includes checkpoint_data:
  - issue_number, issue_title
  - phases (extracted from tasks)
  - task_mapping (TodoWrite ↔ GitHub mapping)

→ checkpoint-manager skill uses this to:
  write_memory("issue_{number}_checkpoint", checkpoint_yaml)
```

#### Recovery Mode (Compact後)
```yaml
Input: Checkpoint data from Serena Memory
Process:
  1. Read task_mapping from checkpoint
  2. Filter: status != "completed"
  3. Filter: phase == current_phase
  4. Rebuild TodoWrite tasks
Output: Restored TodoWrite state
```

---

## 実行指示

**あなたは今、`issue-todowrite-sync` skillを実行しています。**

### Part 1: Issue → TodoWrite変換

1. **Pythonスクリプトで変換を実行**
   ```bash
   cat parsed_issue.json | python3 ~/.claude/skills/issue-todowrite-sync/scripts/convert_to_todowrite.py
   ```

2. **出力されたJSONを解析**
   スクリプトの出力から `todowrite_tasks` 配列を取得

3. **TodoWriteツールを呼び出す（重要！）**
   ```
   TodoWrite tool with todos parameter:
   - Each todo from todowrite_tasks array
   - Include: content, status, activeForm
   ```

   **例**:
   ```json
   [
     {
       "content": "API実装",
       "status": "pending",
       "activeForm": "API実装中"
     },
     {
       "content": "テスト作成",
       "status": "pending",
       "activeForm": "テスト作成中"
     }
   ]
   ```

4. **結果をユーザーに報告**
   - 作成されたTodoWriteタスクの数
   - 各タスクの内容
   - GitHubとの同期が有効化されたことを通知

### Part 2: TodoWrite → GitHub同期

1. **現在のTodoWrite状態を確認**
   完了したタスクを特定

2. **Pythonスクリプトでコメント投稿**
   ```bash
   echo '{"issue_number": 42, ...}' | python3 ~/.claude/skills/issue-todowrite-sync/scripts/sync_progress.py
   ```

3. **結果をユーザーに報告**
   - GitHubへの同期完了
   - 進捗率の更新
   - Issue自動クローズ（該当する場合）

---

**必須ステップ**:
- Part 1で **必ず TodoWrite ツールを呼び出す**こと（スクリプトの出力だけでは不十分）
- スクリプトはJSON生成のみ、TodoWrite作成は Claude が実行
- **checkpoint_data を checkpoint-manager skill に渡す**（Compact耐性）

### Part 3: Recovery Mode（Compact後復旧）

checkpoint-manager skillからの復旧リクエスト時:

1. **チェックポイントデータを受け取る**
   ```yaml
   task_mapping:
     - todowrite_index: 0
       text: "API実装"
       status: pending
     - todowrite_index: 1
       text: "テスト作成"
       status: completed
   current_phase: "Backend"
   ```

2. **未完了タスクをフィルタ**
   - status != "completed"
   - phase == current_phase（Phase単位制限適用時）

3. **TodoWriteを再構築**
   フィルタされたタスクのみTodoWrite作成

4. **結果を報告**
   - 復旧されたタスク数
   - 現在のPhase
   - 進捗状況

---

**Last Updated**: 2025-11-25
**Version**: 1.1.0 (Checkpoint Integration)
