---
name: checkpoint-manager
description: Manage GitHub Issue work checkpoints for Compact resilience. Creates, updates, and recovers checkpoint data from Serena Memory. Use when starting Issue work, completing tasks, or recovering from session reset. Activates on checkpoint operations or Compact recovery needs.
allowed-tools: Bash, TodoWrite
---

# Checkpoint Manager Skill

Provides Compact-resilient checkpoint management for GitHub Issue workflows using Serena Memory.

## What This Skill Does

### Checkpoint Lifecycle
- **Create**: Initialize checkpoint when `/gh:issue work` starts
- **Update**: Save progress on task completion, Phase transitions
- **Recover**: Rebuild TodoWrite state after Compact
- **Delete**: Clean up checkpoint when Issue closes

### Data Persistence
- **Storage**: Serena Memory (`write_memory` / `read_memory`)
- **Key format**: `issue_{number}_checkpoint`
- **Source of Truth**: GitHub Issue (checkpoints are supplementary)

## Checkpoint Schema

```yaml
# Serena Memory: issue_{number}_checkpoint

issue_number: 42
issue_title: "Feature: Authentication"
issue_url: "https://github.com/owner/repo/issues/42"
repo: "owner/repo"

# Phase Tracking
current_phase: "Phase 2: API Implementation"
phases_completed:
  - "Phase 1: Database Schema"
phases_remaining:
  - "Phase 3: Frontend Components"
  - "Phase 4: E2E Tests"

# Task Mapping (TodoWrite ↔ GitHub)
task_mapping:
  - todowrite_index: 0
    github_task_id: 4
    text: "Implement login endpoint"
    phase: "Phase 2: API Implementation"
    status: pending    # pending | in_progress | completed
  - todowrite_index: 1
    github_task_id: 5
    text: "Implement logout endpoint"
    phase: "Phase 2: API Implementation"
    status: completed

# Phase 1.5 Results (Parallel Groups)
parallel_groups:
  - group_id: 1
    mode: sequential
    tasks: [4]
    reason: "Auth middleware dependency"
  - group_id: 2
    mode: parallel
    tasks: [5, 6]
    reason: "Independent endpoints"

# Progress Statistics
progress:
  current_phase_completed: 1
  current_phase_total: 3
  overall_completed: 4
  overall_total: 12
  percentage: 33.3

# Timestamps
created_at: "2025-11-25T10:00:00"
last_updated: "2025-11-25T14:30:00"
last_github_sync: "2025-11-25T14:30:00"

# Configuration
auto_close_enabled: true
recovery_hint: "Continue with login endpoint implementation"

# Schema Version (for backward compatibility)
schema_version: "1.1.0"

# TodoWrite Snapshot（Compact復旧用・v1.1追加）
todowrite_snapshot:
  - index: 0
    content: "Implement login endpoint"
    status: pending
    activeForm: "Implementing login endpoint"
  - index: 1
    content: "Implement logout endpoint"
    status: completed
    activeForm: "Implementing logout endpoint"

# Recovery Command（v1.1追加）
recovery_command: "/gh:start  # Auto-recovers from checkpoint"

# Phase 2 Explore Results（再実行回避・v1.1追加）
explore_results:
  backend:
    patterns: ["REST API", "Express middleware"]
    files: ["src/api/routes.ts", "src/middleware/auth.ts"]
    recommendations: "Use existing auth middleware pattern"
  database:
    patterns: ["Prisma ORM", "PostgreSQL"]
    files: ["prisma/schema.prisma"]
    recommendations: "Extend User model with fields"
  frontend:
    patterns: ["React", "TailwindCSS"]
    files: ["src/components/Auth/"]
    recommendations: "Follow existing form component pattern"

# Execution Stats（v1.1追加）
execution_stats:
  phase_1_5_duration_ms: 1500
  parallel_groups_count: 3
  estimated_speedup_percent: 45
```

## When to Use

This skill activates when:
- **Issue work starts**: `/gh:issue work 42` → create checkpoint
- **Task completes**: TodoWrite task marked done → update checkpoint
- **Phase transitions**: Current phase complete → update checkpoint
- **Parallel analysis done**: Phase 1.5 complete → save parallel_groups
- **Session recovery**: TodoWrite empty + checkpoint exists → recover
- **Issue closes**: `/gh:issue close 42` → delete checkpoint

Explicit invocation: **"use checkpoint-manager skill to recover Issue #42"**

## Operations

### 1. Create Checkpoint

**Trigger**: `/gh:issue work 42` completion

**Process**:
```yaml
1. Receive parsed Issue data from issue-parser
2. Receive TodoWrite mapping from issue-todowrite-sync
3. Build checkpoint structure:
   - issue_number, issue_title, issue_url
   - current_phase (first Phase or "Phase 1")
   - phases_completed: []
   - phases_remaining: [Phase 2, Phase 3, ...]
   - task_mapping: [...]
   - progress: {current: 0, total: N}
4. Save to Serena Memory:
   write_memory("issue_{number}_checkpoint", checkpoint_yaml)
5. Log: "Checkpoint created for Issue #N"
```

**Input** (from issue-todowrite-sync):
```json
{
  "issue_number": 42,
  "issue_title": "Feature: Authentication",
  "tasks": [...],
  "phases": ["Phase 1", "Phase 2", ...],
  "todowrite_mapping": [...]
}
```

### 2. Update Checkpoint

**Trigger**: Task completion, Phase transition, Parallel analysis

**Process**:
```yaml
1. Read current checkpoint:
   read_memory("issue_{number}_checkpoint")

2. Apply update based on trigger:

   Task Completion:
     - Update task_mapping[i].status = "completed"
     - Increment progress.current_phase_completed
     - Increment progress.overall_completed
     - Recalculate progress.percentage

   Phase Transition:
     - Move current_phase to phases_completed
     - Set current_phase = next phase
     - Reset progress.current_phase_completed = 0
     - Update progress.current_phase_total

   Parallel Analysis:
     - Save parallel_groups array

3. Update timestamps:
   last_updated = now()

4. Save updated checkpoint:
   write_memory("issue_{number}_checkpoint", updated_yaml)
```

### 3. Recover from Checkpoint

**Trigger**: `/gh:start` with empty TodoWrite + checkpoint exists

**Process**:
```yaml
1. Detect recovery condition:
   - TodoWrite is empty (no pending tasks)
   - Serena Memory contains issue_*_checkpoint

2. Find checkpoint:
   list_memories() → filter "issue_*_checkpoint"

3. If single checkpoint:
   read_memory("issue_{number}_checkpoint")

4. If multiple checkpoints:
   List all with progress, ask user to choose

5. Fetch GitHub Issue (SSOT):
   gh issue view {number} --json body,comments

6. Reconcile checkpoint vs GitHub:
   - Parse GitHub checkboxes for completion status
   - GitHub status wins all conflicts
   - Update checkpoint.task_mapping accordingly

7. Rebuild TodoWrite:
   - Filter: status != "completed"
   - Filter: phase == current_phase
   - Create TodoWrite tasks for pending items

8. Restore parallel_groups if available

9. Save reconciled checkpoint:
   write_memory("issue_{number}_checkpoint", reconciled_yaml)

10. Log: "Recovered from checkpoint for Issue #N (X/Y complete)"
```

### 4. Delete Checkpoint

**Trigger**: `/gh:issue close 42`

**Process**:
```yaml
1. Verify Issue is being closed
2. Delete checkpoint:
   delete_memory("issue_{number}_checkpoint")
3. Log: "Checkpoint deleted for Issue #N"
```

## Recovery Scenarios

### Scenario 1: Compact During Execution

```
Before Compact:
  - TodoWrite: 5 tasks (2 completed, 3 pending)
  - Checkpoint: issue_42_checkpoint (2/5 complete)
  - Session: Active

[COMPACT]

After Compact:
  - TodoWrite: Empty
  - Checkpoint: issue_42_checkpoint (preserved in Serena)
  - Session: Reset

Recovery:
  /gh:start
  → Phase 0.5: Empty TodoWrite detected
  → read_memory("issue_42_checkpoint")
  → GitHub fetch: Confirms 2/5 complete
  → TodoWrite rebuild: Tasks 3,4,5
  → Continue execution
```

### Scenario 2: Multiple Active Issues

```
/gh:start (TodoWrite empty)
→ list_memories() finds:
  - issue_42_checkpoint (3/8 complete, Phase 2)
  - issue_45_checkpoint (1/5 complete, Phase 1)

→ Display to user:
  "Multiple active Issues detected:
   - Issue #42: 3/8 (37.5%) - Phase 2: API Implementation
   - Issue #45: 1/5 (20%) - Phase 1: Database

   Which Issue to continue?"

→ User selects #42
→ Recover from issue_42_checkpoint
```

### Scenario 3: Stale Checkpoint

```
Checkpoint says: Task 5 pending
GitHub shows: Task 5 checked (completed externally)

Reconciliation:
  - GitHub is SSOT
  - Update checkpoint: Task 5 = completed
  - Don't add Task 5 to TodoWrite
  - Log: "Task 5 completed externally, skipping"
```

## Integration Points

### With /gh:issue work

```
/gh:issue work 42
  ├─ issue-parser: Extract tasks, phases
  ├─ issue-todowrite-sync: Create TodoWrite tasks
  └─ checkpoint-manager: create_checkpoint()
       └─ write_memory("issue_42_checkpoint", ...)
```

### With /gh:start

```
/gh:start
  ├─ Phase 0.5: Check for recovery need
  │    └─ checkpoint-manager: recover_if_needed()
  ├─ Phase 1.5: Parallel analysis complete
  │    └─ checkpoint-manager: update_checkpoint(parallel_groups)
  └─ Phase 3: Task completion
       └─ checkpoint-manager: update_checkpoint(task_status)
```

### With progress-tracker

```
TodoWrite task completed
  ├─ progress-tracker: Post GitHub comment
  └─ checkpoint-manager: update_checkpoint()
```

### With /gh:issue close

```
/gh:issue close 42
  ├─ (other operations)
  └─ checkpoint-manager: delete_checkpoint()
```

## Error Handling

### Serena Memory Errors
- **Memory unavailable**: Fall back to session-only mode
- **Write failure**: Retry once, warn user
- **Read failure**: Attempt GitHub-only recovery

### Reconciliation Errors
- **GitHub unreachable**: Use checkpoint data, warn user
- **Schema mismatch**: Rebuild from GitHub
- **Corrupted checkpoint**: Delete and start fresh

### Multiple Checkpoint Conflicts
- **Same Issue, different checkpoints**: Use most recent
- **Orphaned checkpoints**: Offer cleanup option

## Best Practices

✅ **Do**:
- Let checkpoints be created/updated automatically
- Trust GitHub as the source of truth
- Use `/gh:issue status` to verify state
- Clean up stale checkpoints periodically

❌ **Don't**:
- Manually edit checkpoint memory
- Rely solely on checkpoints (GitHub is SSOT)
- Delete checkpoints while Issue is active
- Skip GitHub reconciliation during recovery

## Files

- `SKILL.md`: This documentation
- `scripts/checkpoint_utils.py`: Checkpoint YAML generation utilities

## Dependencies

- Serena Memory (`write_memory`, `read_memory`, `list_memories`, `delete_memory`)
- `gh` CLI (for GitHub reconciliation)
- issue-parser skill (provides parsed Issue data)
- issue-todowrite-sync skill (provides task mapping)

## Limitations

- **Not real-time**: Updates happen on explicit triggers
- **Serena dependency**: Requires Serena Memory availability
- **GitHub latency**: Reconciliation requires API calls
- **Session-agnostic**: Checkpoints don't track which session created them

---

## 実行指示

**あなたは今、`checkpoint-manager` skillを実行しています。**

### create_checkpoint

1. **入力データを受け取る**
   - issue-parserからのIssueデータ
   - issue-todowrite-syncからのマッピング

2. **チェックポイント構造を構築**
   - YAMLフォーマットで構築
   - 全フィールドを初期化

3. **Serena Memoryに保存**
   ```
   write_memory("issue_{number}_checkpoint", checkpoint_yaml)
   ```

4. **結果を報告**
   - 作成完了メッセージ
   - 保存されたデータのサマリー

### update_checkpoint

1. **現在のチェックポイントを読み取り**
   ```
   read_memory("issue_{number}_checkpoint")
   ```

2. **更新内容を適用**
   - タスク完了: status更新、progress更新
   - Phase遷移: current_phase更新
   - 並列分析: parallel_groups保存

3. **タイムスタンプを更新**

4. **保存**
   ```
   write_memory("issue_{number}_checkpoint", updated_yaml)
   ```

### recover_from_checkpoint

1. **復旧条件を確認**
   - TodoWriteが空
   - checkpointが存在

2. **チェックポイントを取得**
   ```
   list_memories() → filter "issue_*_checkpoint"
   read_memory("issue_{number}_checkpoint")
   ```

3. **GitHubと照合（SSOT）**
   ```bash
   gh issue view {number} --json body,comments
   ```
   - チェックボックス状態を解析
   - GitHubが勝つ

4. **TodoWriteを再構築**
   - 未完了タスクのみ
   - 現在Phaseのタスクのみ

5. **結果を報告**

### delete_checkpoint

1. **チェックポイントを削除**
   ```
   delete_memory("issue_{number}_checkpoint")
   ```

2. **結果を報告**

---

**Last Updated**: 2025-11-25
**Version**: 1.0.0
