# Code Quality Rules

## Implementation Completeness
- No partial features: start it = finish it
- No TODO comments for core functionality
- No mock objects, placeholders, or stub implementations
- All generated code must be production-ready

## Test Implementation
- Every feature/fix includes corresponding tests
- New code must not reduce test coverage

## Scope Discipline
- Build ONLY what's asked, no feature expansion
- MVP first, iterate based on feedback
- No enterprise bloat (auth, deployment, monitoring) unless requested
- YAGNI: no speculative features

## Code Organization
- Follow language/framework naming conventions
- Match existing project organization patterns
- Never mix naming conventions within same project

## Pre-Implementation Quality Gate
- Check LEARNINGS.md before implementation
- CodeRabbit prevention: apply Ruff rules (G004, TRY401, RUF059, RUF022)
- Type safety: zero-division, empty arrays, None handling, index bounds
- Logging: `%s` formatting, `logger.exception()` without `{e}`
- Markdown: blank lines around headings/tables/code blocks
