# Progress Tracker - Automatic GitHub Issue Sync

Automatically posts progress updates to GitHub Issues when TodoWrite tasks are completed.

## Features

✅ **Progress comments** - Posts updates when tasks complete  
✅ **Auto-close** - Closes Issues when all tasks are done  
✅ **Retry logic** - Handles network failures gracefully  
✅ **Session persistence** - Tracks synced state between runs  

## Installation

Scripts are already installed in:
```
~/.claude/skills/progress-tracker/scripts/sync_progress.py
```

## Usage

### Environment Variables

```bash
export CURRENT_ISSUE_NUMBER=42  # Required: Issue number to sync
```

### Automatic Invocation

The script is designed to be called automatically by Claude after TodoWrite completions:

```bash
# Claude internally runs:
echo "$TODOWRITE_JSON" | python3 ~/.claude/skills/progress-tracker/scripts/sync_progress.py
```

### Manual Testing

```bash
cd ~/.claude/skills/progress-tracker/scripts
bash test_sync_progress.sh
```

## How It Works

1. **Progress Calculation**: Compares TodoWrite state with Issue mapping
2. **New Completion Detection**: Identifies newly completed tasks
3. **GitHub Update**: Posts progress comment via gh CLI
4. **Auto-Close Check**: Closes Issue if all tasks complete
5. **State Update**: Saves sync status to session storage

## Comment Format

**Progress Update**:
```markdown
✅ **Task Completed**: Task 1.1: API implementation

**Progress**: 1/3 tasks (33.3%)

---
_Updated automatically by progress-tracker skill_
```

**Completion**:
```markdown
🎉 **All tasks completed!**

This Issue has been automatically closed because all tasks are done.

---
_Closed automatically by progress-tracker skill_
```

## Session Mapping Format

```json
{
  "issue_number": 42,
  "task_mapping": [
    {"todowrite_index": 0, "task_text": "Task 1.1: API implementation"},
    {"todowrite_index": 1, "task_text": "Task 1.2: Add tests"}
  ],
  "auto_close": true,
  "last_synced_completed": 0,
  "completed_indices": []
}
```

## Files

- `sync_progress.py` - Main script
- `test_sync_progress.sh` - Integration tests
- `SKILL.md` - Skill documentation

## Requirements

- Python 3.x (standard library only)
- gh CLI (GitHub CLI)
- TodoWrite state as JSON via stdin
- `CURRENT_ISSUE_NUMBER` environment variable
- Session mapping file at `~/.claude/.session/issue_mapping.json`

## Error Handling

- Missing Issue number: Warning, skips sync
- gh CLI unavailable: Error exit
- Network timeout: Retry once, then error log
- Missing mapping: Warning, skips sync
- Invalid JSON: Error exit
