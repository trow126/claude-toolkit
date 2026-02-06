---
name: task-management
description: Hierarchical task organization with Serena memory persistence. Activate for operations with >3 steps or multiple file/directory scope (>2 dirs OR >3 files).
---

# Task Management

## Hierarchy
Plan > Phase > Task > Todo (TaskCreate + write_memory)

## Session Lifecycle
- **Start**: list_memories > read_memory > resume context
- **During**: write_memory checkpoints every 30min or on task completion
- **End**: write_memory session summary, delete temporary items

## Tool Selection
| Task Type | Primary Tool | Memory Key |
|-----------|-------------|------------|
| Analysis | Sequential MCP | "analysis_results" |
| Implementation | MultiEdit | "code_changes" |
| Testing | Test runner | "test_results" |
