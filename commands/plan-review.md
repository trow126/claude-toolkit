# Multi-Perspective Plan Review

Review an implementation plan from 3 independent perspectives using specialized subagents.

## Arguments

$ARGUMENTS

## Instructions

You are orchestrating a multi-perspective review of an implementation plan.

### Step 1: Locate the Plan

**If arguments contain a file path:**
- This is "different session" mode
- Read the specified file as the plan
- You have NO prior context about the codebase
- Reviewers will need to explore the codebase themselves

**If arguments are empty:**
- This is "same session" mode
- Find the most recently created or discussed plan file in this conversation
- If you cannot find one, ask the user which plan file to review
- You already have codebase context from the planning session

### Step 2: Read the Plan and Project Context

1. Read the plan file content
2. Read these files if they exist (pass relevant parts to reviewers):
   - CLAUDE.md (project root and .claude/)
   - LEARNINGS.md or claudedocs/learnings.md
   - Any other project convention files referenced in CLAUDE.md

### Step 3: Determine Review Mode

**Same session mode** (no arguments):
- Include in each reviewer's prompt: the plan content, list of relevant files you know about, and key decisions from the planning session
- Reviewers can focus on analysis rather than exploration

**Different session mode** (file path provided):
- Include in each reviewer's prompt: the plan content and instruction to explore the codebase first
- The feasibility reviewer especially needs to verify codebase structure

### Step 4: Spawn 3 Reviewers in Parallel

Launch these subagents simultaneously using the Agent tool:

1. **plan-reviewer-feasibility**
   Prompt: "Review this implementation plan for feasibility. [plan content] [mode-specific context]"

2. **plan-reviewer-completeness**
   Prompt: "Audit this implementation plan for completeness. [plan content] [CLAUDE.md / LEARNINGS.md content if found]"

3. **plan-reviewer-critic**
   Prompt: "Critique this implementation plan's scope and risks. [plan content] [project description if available]"

Each prompt MUST include the full plan text. Do not summarize or truncate the plan.

### Step 5: Synthesize Results

After all 3 reviewers return, create a unified review document with this structure:

```
# Plan Review: [plan title or description]

**Date**: [current date]
**Plan file**: [path]
**Mode**: [same-session / different-session]

## Executive Summary

[2-3 sentence overall assessment]

**Verdict**: [APPROVE / APPROVE_WITH_CHANGES / REQUEST_REVISION / REJECT]
- BLOCKERs: [count]
- WARNINGs: [count]
- INFOs: [count]

## BLOCKERs (must fix before implementation)

[All BLOCKER findings from all reviewers, with source attribution]

## WARNINGs (should address)

[All WARNING findings from all reviewers, with source attribution]

## INFOs (consider)

[All INFO findings from all reviewers, with source attribution]

## Reviewer Reports

### Feasibility Analysis
[Full report from feasibility reviewer]

### Completeness Audit
[Full report from completeness reviewer]

### Scope & Risk Critique
[Full report from critic reviewer]

## Recommended Plan Modifications

[Prioritized list of specific changes to make to the plan]

1. [BLOCKER fixes first]
2. [WARNING fixes second]
3. [INFO suggestions last]
```

### Step 6: Save and Report

1. Create `claudedocs/reviews/` directory if it doesn't exist
2. Save the review to `claudedocs/reviews/plan-review-[YYYYMMDD-HHMM].md`
3. Display a summary to the user:
   - Overall verdict
   - Number of BLOCKERs / WARNINGs / INFOs
   - Top 3 most important findings
   - Path to the full review file

### Verdict Criteria

- **APPROVE**: No BLOCKERs, 0-2 WARNINGs, plan is solid
- **APPROVE_WITH_CHANGES**: No BLOCKERs, some WARNINGs that should be addressed
- **REQUEST_REVISION**: 1+ BLOCKERs or many WARNINGs, plan needs significant changes
- **REJECT**: Multiple BLOCKERs, fundamental issues with the approach
