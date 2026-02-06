# Safety Rules

## Failure Investigation
- Always investigate WHY failures occur (root cause analysis)
- Never skip, disable, or comment out tests
- Never bypass quality checks or validation
- Debug systematically: Understand > Diagnose > Fix > Verify

## Framework Respect
- Check package.json/deps before using libraries
- Follow existing project conventions and import styles
- Prefer batch operations with rollback capability

## Compound Commands
- Avoid `&&`, `||`, `;`, `|` in Bash commands (causes permission pollution)
- Use parallel tool calls for independent operations
- Use native tools: Grep over `grep`, Glob over `find`, Read over `cat`
