# Workflow Rules

## Task Pattern
Understand > Plan > TaskCreate (3+ tasks) > Execute > Track > Validate

## Planning
- Identify parallelizable operations during planning
- Map dependencies: separate sequential from parallel tasks
- Plan optimal MCP server combinations and batch operations
- Architectural tasks: use Claude Code Plan mode before executing

## Execution
- ALWAYS parallel tool calls by default, sequential ONLY for dependencies
- Validate before execution, verify after completion
- Run lint/typecheck before marking tasks complete
- Proof of operation before marking complete: show actual execution output or file final state

## Self-Improvement
- When the user corrects your work: append to the project's `claudedocs/learnings.md` under a `## Corrections` section
- Review project learnings at session start

## Serena Memory
- Auto-execute memory operations without confirmation
- Session pattern: list_memories > Work > write_memory (checkpoint) > write_memory (save)
- Checkpoint on: task completion, 30-min intervals, risky operations

## Tool Selection
- Best tool for each task: MCP > Native > Basic
- Use Task agents for complex multi-step operations (>3 steps)
- Batch operations: MultiEdit over multiple Edits, batch Read calls
