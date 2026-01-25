---
name: rules-quick-reference
description: Quick reference for Claude Code behavioral rules. Activates on 'rules reference', 'decision tree', 'priority actions', or when quick rule lookup is needed.
allowed-tools: Read
---

# Rules Quick Reference

Use this skill for quick lookup of Claude Code behavioral rules and decision trees.

## Critical Decision Flows

**🔴 Before Any File Operations**
```
File operation needed?
├─ Writing/Editing? → Read existing first → Understand patterns → Edit
├─ Creating new? → Check existing structure → Place appropriately
└─ Safety check → Absolute paths only → No auto-commit
```

**🟡 Starting New Feature**
```
New feature request?
├─ Scope clear? → No → Brainstorm mode first
├─ >3 steps? → Yes → TodoWrite required
├─ Patterns exist? → Yes → Follow exactly
├─ Tests available? → Yes → Run before starting
└─ Framework deps? → Check package.json first
```

**🟢 Tool Selection Matrix**
```
Task type → Best tool:
├─ Multi-file edits → MultiEdit > individual Edits
├─ Complex analysis → Task agent > native reasoning
├─ Code search → Grep > bash grep
├─ UI components → Magic MCP > manual coding
├─ Documentation → Context7 MCP > web search
└─ Browser testing → Playwright MCP > unit tests
```

## Priority-Based Quick Actions

### 🔴 CRITICAL (Never Compromise)
- `git status && git branch` before starting
- Read before Write/Edit operations
- Feature branches only, never main/master
- Root cause analysis, never skip validation
- Absolute paths, no auto-commit

### 🟡 IMPORTANT (Strong Preference)
- TodoWrite for >3 step tasks
- Complete all started implementations
- Build only what's asked (MVP first)
- Professional language (no marketing superlatives)
- Clean workspace (remove temp files)

### 🟢 RECOMMENDED (Apply When Practical)
- Parallel operations over sequential
- Descriptive naming conventions
- MCP tools over basic alternatives
- Batch operations when possible

For full rules, read ~/.claude/RULES.md
