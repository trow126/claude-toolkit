---
name: coderabbit-prevention
description: CodeRabbit prevention patterns and Ruff rule reference. Activates on 'CodeRabbit', 'Ruff rules', 'linting patterns', or when implementing Python code.
allowed-tools: Read
---

# CodeRabbit Prevention Patterns

Use this skill for detailed CodeRabbit/Ruff rule reference during Python development.

## Markdown (markdownlint)

| Rule | Issue | Solution |
|------|-------|----------|
| MD022 | No blank before heading | Add `\n## Heading` |
| MD031 | No blank around code | Add blank lines |
| MD034 | Bare URL | Use `[title](url)` |
| MD040 | No lang in code block | Add ` ```python ` |
| MD058 | No blank around table | Add blank lines |

## Python Variables (Ruff)

| Rule | Issue | Solution |
|------|-------|----------|
| RUF059 | Unused unpack var | Add `_` prefix |
| RUF022 | `__all__` not sorted | Sort alphabetically |

## Logging (Ruff G/TRY)

| Rule | Issue | Solution |
|------|-------|----------|
| G004 | f-string in log | Use `%s` format |
| TRY401 | `exception(f"{e}")` | Just `exception("msg")` |
| TRY003 | Long error msg | Custom exception class |

## Other Rules

| Rule | Issue | Solution |
|------|-------|----------|
| ASYNC110 | while/sleep loop | Use `await event.wait()` |
| DTZ005 | `datetime.now()` | Add `timezone.utc` |
| NPY002 | Legacy random | Use `default_rng()` |

## Type Safety Patterns

```python
# Zero-division
rate = wins / total if total > 0 else 0.0

# Index access
first = items[0] if items else None

# Empty DataFrame
if df.empty or df["col"].isna().all():
    return None

# Exception logging
except Exception:
    logger.exception("Error occurred")  # No {e}!
```

## Ruff Commands

```bash
uv run ruff check src/ --fix && uv run ruff format src/ && uv run mypy src/
```

For full patterns, read ~/.claude/LEARNINGS.md
