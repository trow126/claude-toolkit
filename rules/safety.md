# Safety Rules

## Failure Investigation
- Always investigate WHY failures occur (root cause analysis)
- Never skip, disable, or comment out tests
- Never bypass quality checks or validation
- Debug systematically: Understand > Diagnose > Fix > Verify
- Bug reports: present a concrete fix hypothesis before implementing. For financial/trading logic, always clarify root cause before modifying

## Framework Respect
- Check package.json/deps before using libraries
- Follow existing project conventions and import styles
- Prefer batch operations with rollback capability

## Compound Commands
- Avoid `&&`, `||`, `;`, `|` in Bash commands
  - Reason: Permission check applies to first command only; subsequent commands bypass allowlist
  - Ref: https://github.com/anthropics/claude-code/issues/16180 (Open)
- Use parallel tool calls for independent operations
- Use native tools: Grep over `grep`, Glob over `find`, Read over `cat`
