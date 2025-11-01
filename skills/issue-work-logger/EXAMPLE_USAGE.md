# Usage Examples

## Example 1: Starting Work on Issue #42

```bash
# Terminal setup
export CURRENT_ISSUE_NUMBER=42
cd ~/my-project

# Start Claude Code session
# Claude creates TodoWrite tasks from GitHub Issue

# TodoWrite state (automatically captured):
{
  "todos": [
    {
      "content": "Analyze security requirements",
      "activeForm": "Analyzing security requirements",
      "status": "in_progress"
    }
  ]
}

# Auto-logger runs automatically and writes to:
# ~/claudedocs/work/issue_42_notes.md
```

**Result in `issue_42_notes.md`**:
```markdown
## [2025-11-01 14:30] Session started
**Starting task**: Analyze security requirements

## [2025-11-01 14:30] Task started
**Task**: Analyze security requirements
```

## Example 2: Completing Task and Starting Next

```bash
# TodoWrite state changes (automatically captured):
{
  "todos": [
    {
      "content": "Analyze security requirements",
      "activeForm": "Analyzing security requirements",
      "status": "completed"
    },
    {
      "content": "Design authentication flow",
      "activeForm": "Designing authentication flow",
      "status": "in_progress"
    }
  ]
}

# Auto-logger detects changes and logs
```

**Result appended to `issue_42_notes.md`**:
```markdown
## [2025-11-01 15:15] Task completed
**Task**: Analyze security requirements

## [2025-11-01 15:15] Task started
**Task**: Design authentication flow
```

## Example 3: Manual Testing

```bash
# Create test directory
mkdir -p /tmp/test_work

# Test session start
cat <<'EOF' | CURRENT_ISSUE_NUMBER=123 WORK_DIR=/tmp/test_work \
  python3 $HOME/.claude/skills/issue-work-logger/scripts/auto_logger.py
{
  "todos": [
    {
      "content": "Write unit tests",
      "activeForm": "Writing unit tests",
      "status": "in_progress"
    }
  ]
}
EOF

# Test task completion
cat <<'EOF' | CURRENT_ISSUE_NUMBER=123 WORK_DIR=/tmp/test_work \
  python3 $HOME/.claude/skills/issue-work-logger/scripts/auto_logger.py
{
  "todos": [
    {
      "content": "Write unit tests",
      "activeForm": "Writing unit tests",
      "status": "completed"
    },
    {
      "content": "Run integration tests",
      "activeForm": "Running integration tests",
      "status": "in_progress"
    }
  ]
}
EOF

# View generated log
cat /tmp/test_work/issue_123_notes.md
```

**Output**:
```
✓ Logged session start to /tmp/test_work/issue_123_notes.md
✓ Logged task start: Write unit tests...
✓ Successfully logged 1 event(s) to /tmp/test_work/issue_123_notes.md

✓ Logged task completion: Write unit tests...
✓ Logged task start: Run integration tests...
✓ Successfully logged 2 event(s) to /tmp/test_work/issue_123_notes.md
```

## Example 4: Complete Workflow Integration

```bash
# 1. Create Issue from brainstorming
/gh:brainstorm "Need to add user authentication"
# Creates GitHub Issue #42

# 2. Convert Issue to TodoWrite
# issue-todowrite-sync skill converts Issue tasks

# 3. Start working (this triggers auto-logger)
# Claude marks first task as in_progress
# -> Auto-logs session start and task start

# 4. Complete tasks
# As you complete tasks, auto-logger records:
# -> Task completions
# -> Task starts for next items

# 5. Sync progress to GitHub
# progress-tracker skill posts updates to Issue #42

# 6. Review work log
cat ~/claudedocs/work/issue_42_notes.md
```

## Example 5: Multi-Session Workflow

### Session 1 (Monday 14:00)
```bash
export CURRENT_ISSUE_NUMBER=42

# Claude starts work, TodoWrite created
# Auto-logged:
## [2025-11-01 14:00] Session started
## [2025-11-01 14:00] Task started: Design schema
## [2025-11-01 15:30] Task completed: Design schema
```

### Session 2 (Monday 16:00)
```bash
export CURRENT_ISSUE_NUMBER=42

# Resume work, next task started
# Auto-logged:
## [2025-11-01 16:00] Session started
## [2025-11-01 16:00] Task started: Implement API endpoints
## [2025-11-01 17:45] Task completed: Implement API endpoints
```

### Session 3 (Tuesday 09:00)
```bash
export CURRENT_ISSUE_NUMBER=42

# Continue work
# Auto-logged:
## [2025-11-02 09:00] Session started
## [2025-11-02 09:00] Task started: Write integration tests
## [2025-11-02 10:30] Task completed: Write integration tests
```

## Example 6: Error Scenarios

### Missing Issue Number
```bash
# Error: CURRENT_ISSUE_NUMBER not set
echo '{"todos": []}' | python3 auto_logger.py

# Output:
# Error: CURRENT_ISSUE_NUMBER environment variable not set
```

### Invalid JSON
```bash
# Error: Malformed JSON
echo 'not valid json' | CURRENT_ISSUE_NUMBER=42 python3 auto_logger.py

# Output:
# Error: Failed to parse input JSON: Expecting value: line 1 column 1 (char 0)
```

### No Changes Detected
```bash
# Running with identical state twice
cat state.json | CURRENT_ISSUE_NUMBER=42 python3 auto_logger.py
cat state.json | CURRENT_ISSUE_NUMBER=42 python3 auto_logger.py

# Second run output:
# No TodoWrite state changes detected
```

## Example 7: Debugging State

```bash
# View current session state
cat ~/.claude/.session/todowrite_state.json

# Example output:
{
  "todos": [
    {
      "content": "Design authentication flow",
      "activeForm": "Designing authentication flow",
      "status": "in_progress"
    }
  ]
}

# Clear state to reset
rm ~/.claude/.session/todowrite_state.json
```

## Example 8: Custom Work Directory

```bash
# Use custom location for logs
export WORK_DIR=/home/user/projects/myapp/work
export CURRENT_ISSUE_NUMBER=42

# Logs will be written to:
# /home/user/projects/myapp/work/issue_42_notes.md
```

## Integration with Claude Commands

The auto-logger is designed to be called automatically by Claude Code after TodoWrite operations. No manual invocation needed!

```python
# Pseudo-code for Claude integration
def on_todowrite_update(todowrite_json):
    if os.getenv('CURRENT_ISSUE_NUMBER'):
        result = subprocess.run(
            ['python3', '$HOME/.claude/skills/issue-work-logger/scripts/auto_logger.py'],
            input=todowrite_json.encode(),
            capture_output=True
        )
        if result.returncode == 0:
            print("✓ Work log updated")
```
