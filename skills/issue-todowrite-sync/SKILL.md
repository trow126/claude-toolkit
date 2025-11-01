---
name: issue-todowrite-sync
description: Synchronize GitHub Issues with TodoWrite tasks bidirectionally. Converts Issue tasks to TodoWrite format and updates GitHub Issues when TodoWrite tasks complete. Use when starting work on Issues, managing task progress, converting Issues to todos, or syncing Issue status. Activates on "work on Issue", "convert to TodoWrite", "sync progress", or explicit "use issue-todowrite-sync skill".
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

### TodoWrite → Issue Synchronization
- Posts progress comments to GitHub when tasks complete
- Updates completion percentage automatically
- Auto-closes Issues when all tasks are done (optional)
- Tracks sync state within current session

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
  "task_mapping": [...]
}
```

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
- **/gh:issue command**: Primary workflow integration
