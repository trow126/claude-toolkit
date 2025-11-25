---
name: progress-tracker
description: Track TodoWrite task completion and automatically update GitHub Issues with progress comments. Monitors TodoWrite changes and posts updates to linked Issues. Integrates with checkpoint-manager for Compact resilience. Use when TodoWrite tasks are completed, Issue progress needs updating, or automatic sync is required. Activates on TodoWrite completion events or explicit sync requests.
allowed-tools: Bash, TodoWrite
---

# Progress Tracker Skill

Monitors TodoWrite task completion and automatically synchronizes progress to GitHub Issues.

## What This Skill Does

### Automatic Progress Tracking
- **Detects TodoWrite completion**: When tasks are marked complete
- **Reads Issue mapping**: From session context
- **Calculates progress**: Completion percentage and counts
- **Updates GitHub**: Posts progress comments automatically
- **Updates checkpoint**: Triggers checkpoint-manager for Serena Memory update
- **Auto-closes Issues**: When all tasks are complete (if enabled)

### Manual Progress Updates
- **On-demand sync**: Update GitHub with current progress
- **Batch updates**: Sync multiple Issues at once
- **Progress reports**: Generate detailed progress summaries

## When to Use

This skill automatically activates when:
- **TodoWrite task completed**: You mark a task as done
- **Explicit sync request**: "sync Issue progress"
- **Status check**: "show Issue #42 status"
- **Batch sync**: "sync all active Issues"

Explicit invocation: **"use progress-tracker skill to sync Issue #42"**

## How It Works

### Activation Trigger

**Scenario 1: TodoWrite Completion**
```
User: (Marks TodoWrite task #3 as completed)
↓
Claude: Detects completion via TodoWrite state change
↓
progress-tracker skill activates automatically
```

**Scenario 2: Explicit Sync**
```
User: "Sync progress for Issue #42"
↓
progress-tracker skill invokes explicitly
```

### Process Flow

#### Step 1: Detect Completion
When a TodoWrite task is marked complete:
1. **Check for Issue linkage**
   - Read active Issue mappings from session context
   - Determine which Issue(s) are affected

2. **Identify completed task**
   - Match TodoWrite index to Issue task
   - Get task details from mapping

#### Step 2: Calculate Progress
```python
# Read mapping from session context
mapping = get_session_mapping(issue_number=42)

# Count current TodoWrite states
total_tasks = len(mapping['task_mapping'])
completed_tasks = count_completed_in_todowrite()

# Calculate percentage
completion_pct = (completed_tasks / total_tasks) * 100
```

#### Step 3: Update GitHub

**Post Progress Comment**
```bash
gh issue comment 42 --body "$(cat <<'EOF'
✅ **Task Completed**: API実装

**Progress**: 3/8 tasks (37.5%)

---
_Updated automatically by progress-tracker skill_
EOF
)"
```

#### Step 3.5: Update Checkpoint (Compact耐性)

**🔴 必須: タスク完了後に checkpoint-manager skill でcheckpoint更新**
```yaml
checkpoint-manager skill を起動:
  1. read_memory("issue_42_checkpoint")
  2. 更新:
     - task_mapping[i].status = "completed"
     - progress.overall_completed++
     - progress.percentage = (completed / total) * 100
     - last_updated = now()
  3. write_memory("issue_42_checkpoint", updated_yaml)
```

**Check for Auto-Close**
```python
if completed_tasks == total_tasks and auto_close_enabled:
    # Post completion comment
    gh issue comment 42 --body "🎉 All tasks completed!"

    # Close issue
    gh issue close 42 --reason "completed"

    # Delete checkpoint (via checkpoint-manager skill)
    delete_memory("issue_42_checkpoint")
```

## Usage Examples

### Example 1: Automatic Tracking (Background)
```
# User working with TodoWrite
User: (Marks task "API実装" as completed)

Claude (internal process):
  1. progress-tracker detects completion
  2. Reads issue_42_mapping from session context
  3. Identifies: Task #1 of Issue #42
  4. Posts to GitHub:
     "✅ Task Completed: API実装
      Progress: 1/5 tasks (20%)"

User sees:
  ✓ GitHub Issue #42 updated automatically
  ✓ Progress comment posted
  ✓ No manual action required
```

### Example 2: Manual Sync
```
User: "Sync progress for Issue #42"

Claude:
  1. Invokes progress-tracker skill explicitly
  2. Reads current TodoWrite state
  3. Reads issue_42_mapping from session context
  4. Calculates progress delta
  5. Posts update if changed

Output:
  "Synced Issue #42: 3/5 tasks complete (60%)
   Posted progress update to GitHub"
```

### Example 3: Auto-Close on Completion
```
User: (Marks final task as complete)

Claude (progress-tracker):
  1. Detects last task completion
  2. Calculates: 5/5 tasks (100%)
  3. Posts completion comment:
     "🎉 All tasks completed!"
  4. Closes Issue #42 with reason: "completed"

Output:
  "✅ All tasks complete!
   Issue #42 automatically closed.
   Great work! 🎉"
```

### Example 4: Batch Sync
```
User: "Sync all active Issues"

Claude (progress-tracker):
  1. Lists all Issues in session context
  2. For each Issue:
     - Read TodoWrite state
     - Calculate progress
     - Post update if changed
  3. Summary report

Output:
  "Synced 3 Issues in current session:
   - Issue #42: 3/5 tasks (60%) ✅
   - Issue #43: 2/4 tasks (50%) ✅
   - Issue #44: 5/5 tasks (100%) - Auto-closed ✅"
```

## Configuration

### Auto-Close Behavior

**Enabled by default**. When all tasks complete:
- Posts completion comment
- Closes Issue with reason "completed"

**To disable**:
During Issue work start:
```
/gh:issue work 42 --no-auto-close
```

### Sync Frequency

**Real-time (default)**: Updates immediately on task completion within current session

**Manual**: Use explicit sync commands on-demand
```
User: "Sync progress for Issue #42"
Claude: Manually triggers progress update to GitHub
```

### Progress Comment Format

Standard format:
```markdown
✅ **Task Completed**: <task_text>

**Progress**: <completed>/<total> tasks (<percentage>%)

---
_Updated automatically by progress-tracker skill_
```

## Error Handling

### GitHub API Errors
- **Rate limit**: Wait and retry after delay
- **Network error**: Retry once, then queue for later
- **Permission denied**: Log error, notify user
- **Issue not found**: Clean up mapping, notify user

### TodoWrite Conflicts
- **Unexpected state**: Reconcile with GitHub
- **Missing task**: Log warning, continue
- **Index mismatch**: Re-sync mapping

### Session Errors
- **Missing session data**: Warn user to use `/gh:issue work` to start tracking
- **Session expired**: Re-run `/gh:issue work` to restore tracking

## Integration Points

### With issue-todowrite-sync
```
issue-todowrite-sync: Creates mapping + TodoWrite tasks
         ↓
progress-tracker: Monitors TodoWrite completion
         ↓
issue-todowrite-sync: Syncs progress to GitHub
         ↓
checkpoint-manager: Updates Serena Memory checkpoint
```

### With checkpoint-manager (Compact耐性)
```
タスク完了検出
  → GitHub更新
  → checkpoint-manager skill 起動
    → read_memory("issue_{number}_checkpoint")
    → task_mapping[i].status = "completed"
    → progress 再計算
    → write_memory("issue_{number}_checkpoint", updated_yaml)

全タスク完了時
  → Issue自動クローズ
  → checkpoint-manager skill 起動
    → delete_memory("issue_{number}_checkpoint")
```

### With /gh:issue Command
```
/gh:issue work 42
  → Creates session mapping
  → Creates checkpoint via checkpoint-manager
  → Activates progress-tracker monitoring

TodoWrite completion
  → progress-tracker detects
  → Calls issue-todowrite-sync for GitHub update
  → Calls checkpoint-manager for Serena Memory update

/gh:issue status 42
  → progress-tracker provides current state from session
  → Falls back to checkpoint if session data missing
```

## Implementation Notes

### Detection Mechanism

Since TodoWrite doesn't emit events, detection happens through:

1. **Periodic checks** (when Claude is active)
2. **Explicit triggers** (user commands)
3. **TodoWrite state comparison** (read current vs. stored)

### Performance Considerations

- **Lazy evaluation**: Only check when TodoWrite is accessed
- **Batch updates**: Group multiple completions
- **Rate limiting**: Respect GitHub API limits
- **Session caching**: Minimize redundant GitHub API calls

## Files

- `SKILL.md`: This documentation

## Dependencies

- `gh` CLI (GitHub CLI)
- TodoWrite tool
- issue-todowrite-sync skill (for sync logic)
- checkpoint-manager skill (for Compact resilience)

## Testing

### Manual Test
```bash
# Simulate completion event
User: "Simulate TodoWrite task #2 completion for Issue #42"

Claude:
  1. Reads issue_42_mapping from session
  2. Marks task #2 as completed
  3. Calls progress-tracker
  4. Posts update to GitHub
```

### Integration Test
```bash
# Full workflow test
/gh:issue work 42
→ Creates session mapping with 5 tasks

(Mark tasks 1, 2, 3 as complete)
→ progress-tracker posts 3 updates

(Mark tasks 4, 5 as complete)
→ progress-tracker posts 2 updates
→ Auto-closes Issue #42
```

## Monitoring and Debugging

### Check Tracking Status
```
User: "What Issues am I tracking?"
Claude: Lists all Issues in current session context
```

### View Sync History
```
User: "Show sync history for Issue #42"
Claude: Reads mapping from session, displays:
  - Created: 2025-10-30 10:00
  - Current completion: 80%
  - Tasks completed: 4/5
```

### Debug Mode
```
User: "Debug progress tracking for Issue #42"
Claude:
  1. Reads mapping from session
  2. Reads TodoWrite state
  3. Compares states
  4. Shows diff and sync plan
```

## Best Practices

✅ **Do**:
- Let progress-tracker work automatically
- Use `/gh:issue status` to check progress
- Keep auto-close enabled for most Issues
- Complete work within single session when possible

❌ **Don't**:
- Manually edit Issue task checkboxes (breaks sync)
- Mix manual and automatic updates
- Disable tracking without reason

## Limitations

- **Detection delay**: Not real-time, depends on Claude activity
- **No reverse sync**: GitHub changes don't auto-update TodoWrite
- **Single-direction**: TodoWrite → GitHub only (by design)
- **GitHub dependency**: Requires network access
- **Checkpoint updates**: Requires Serena Memory availability

---

**Note**: This skill works best when TodoWrite tasks are the "source of truth" for progress. GitHub Issues reflect TodoWrite state, not the other way around. With checkpoint-manager integration, work can now be resumed across sessions after Compact events.

---

**Last Updated**: 2025-11-25
**Version**: 1.1.0 (Checkpoint Integration)
