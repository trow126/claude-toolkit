---
name: issue-work-logger
description: Automatically log work progress for GitHub Issues to claudedocs/work/ (project, gitignored)
category: skill
scope: project
---

# Issue Work Logger Skill

**Purpose**: Automatic work progress logging for GitHub Issue-driven development workflow.

## Overview

This skill automatically monitors TodoWrite state changes and logs task progress to
`claudedocs/work/issue_N_notes.md` files. It enables seamless tracking of work sessions,
task starts, and task completions without manual intervention.

## Features

- **Automatic Session Detection**: Logs session start when first in_progress task appears
- **Task Start Logging**: Records when tasks transition from pending → in_progress
- **Task Completion Logging**: Records when tasks transition from in_progress → completed
- **State Persistence**: Maintains TodoWrite state between sessions in `~/.claude/.session/`
- **Robust Error Handling**: Gracefully handles missing files and invalid input

## Usage

### Automatic Mode (Recommended)

The skill is designed to be called automatically by Claude after TodoWrite operations:

```bash
# Called automatically by Claude Code
echo "$TODOWRITE_JSON" | python3 $HOME/.claude/skills/issue-work-logger/scripts/auto_logger.py
```

### Manual Mode

You can manually trigger logging for testing:

```bash
export CURRENT_ISSUE_NUMBER=42
export WORK_DIR=~/claudedocs/work  # Optional, defaults to ~/claudedocs/work

# Pipe TodoWrite JSON state to the logger
echo '{"todos": [...]}' | python3 auto_logger.py
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CURRENT_ISSUE_NUMBER` | Yes | - | Active GitHub Issue number |
| `WORK_DIR` | No | `~/claudedocs/work` | Base directory for work logs |

## Log Format

### Session Start
```markdown
## [2025-11-01 14:30] Session started
**Starting task**: Implement authentication system
```

### Task Start
```markdown
## [2025-11-01 14:35] Task started
**Task**: Design database schema
```

### Task Completion
```markdown
## [2025-11-01 15:20] Task completed
**Task**: Design database schema
```

## State Management

### Session Storage Location
- **State File**: `~/.claude/.session/todowrite_state.json`
- **Purpose**: Track previous TodoWrite state for change detection
- **Format**: JSON with complete TodoWrite structure

### Change Detection Logic

The logger compares current TodoWrite state with previous state to detect:

1. **Task Started**: `pending` → `in_progress`
2. **Task Completed**: `in_progress` → `completed`
3. **Session Started**: Empty state → state with `in_progress` tasks

Tasks are matched by their `content` field for comparison.

## Integration with Issue Workflow

This skill integrates with the complete GitHub Issue-driven development workflow:

1. **Issue Creation**: `/gh:issue` or `/gh:brainstorm`
2. **Task Conversion**: `issue-todowrite-sync` skill converts Issue tasks to TodoWrite
3. **Work Logging**: `issue-work-logger` (this skill) automatically logs progress
4. **Progress Tracking**: `progress-tracker` skill updates GitHub Issue with completed tasks

## File Structure

```
~/.claude/skills/issue-work-logger/
├── skill.md                    # This documentation
├── README.md                   # User guide
└── scripts/
    ├── auto_logger.py          # Main automatic logger
    └── test_auto_logger.sh     # Test suite

~/.claude/.session/
└── todowrite_state.json        # TodoWrite state persistence

~/claudedocs/work/
└── issue_N_notes.md            # Work logs per Issue
```

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Missing `CURRENT_ISSUE_NUMBER` | Error message, exit code 1 |
| Invalid JSON input | Error message, exit code 1 |
| Missing log file | Warning, creates new file |
| No state changes | Info message, exit code 0 |
| Previous state parse error | Warning, treats as empty state |

## Testing

Run the test suite:

```bash
cd $HOME/.claude/skills/issue-work-logger/scripts
bash test_auto_logger.sh
```

Tests cover:
- Empty input handling
- Invalid JSON handling
- Session start detection
- Task start logging
- Task completion logging
- No-change scenarios

## Dependencies

- Python 3.x (standard library only)
- No external packages required

## Best Practices

1. **Set Issue Context**: Always set `CURRENT_ISSUE_NUMBER` when starting work on an Issue
2. **Session Management**: Let Claude automatically call the logger after TodoWrite operations
3. **Review Logs**: Periodically review `issue_N_notes.md` for accurate progress tracking
4. **Clean State**: Clear session state (`~/.claude/.session/`) when switching projects

## Troubleshooting

### No logs being written

```bash
# Check if CURRENT_ISSUE_NUMBER is set
echo $CURRENT_ISSUE_NUMBER

# Check if work directory exists
ls -la ~/claudedocs/work/

# Verify script is executable
ls -l $HOME/.claude/skills/issue-work-logger/scripts/auto_logger.py
```

### State file corruption

```bash
# Reset state file
rm ~/.claude/.session/todowrite_state.json
```

### Permission errors

```bash
# Ensure directories are writable
chmod +w ~/claudedocs/work/
chmod +w ~/.claude/.session/
```

## Future Enhancements

Potential improvements for future versions:

- **Session End Detection**: Time-based or explicit session close logging
- **Multi-Issue Support**: Track multiple concurrent Issues
- **Rich Markdown**: Add task duration, session summaries
- **Conflict Resolution**: Handle concurrent TodoWrite updates
- **Web Dashboard**: Visualize work progress across Issues

## Related Skills

- **issue-todowrite-sync**: Convert GitHub Issues to TodoWrite tasks
- **progress-tracker**: Update GitHub Issues with TodoWrite completion
- **issue-parser**: Parse GitHub Issue markdown structure
