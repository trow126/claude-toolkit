# Workspace Rules

## Hygiene
- Clean temporary files, scripts, and directories after operations
- Remove build artifacts, logs, and debugging outputs
- Never leave temporary files that could be accidentally committed
- Delete `claudedocs/brainstorm/*.md` when corresponding Issue is closed

## File Organization
- Claude-specific docs in `claudedocs/` directory
- Tests in `tests/`, `__tests__/`, or `test/` directories
- Scripts in `scripts/`, `tools/`, or `bin/` directories
- Check existing patterns before creating new directories

## Temporal Awareness
- Always verify current date from environment before temporal assessments
- Never assume from knowledge cutoff dates
