# Claude Code Configuration

# Core behavioral flags
@FLAGS.md

# Project learnings and quality gates
@LEARNINGS.md

# Tool Selection Matrix
| Task Type | Best Tool | Alternative |
|-----------|-----------|-------------|
| Deep analysis | Sequential MCP | Native reasoning |
| Symbol operations | Serena MCP | Manual search |
| Documentation | Context7 MCP | Web search |
| Multi-file edits | MultiEdit | Sequential Edits |
| Infrastructure | WebFetch (official docs) | Never assume |

# ===================================================
# Agent Orchestration
# ===================================================

For non-trivial tasks, consult the `project-orchestrator` agent to determine the optimal specialist.

**Known project routing** (fast path):

| Project | Directory | Specialists |
|---------|-----------|-------------|
| sample-ml-project | `~/projects/ml-platform/` | `ai-engineer`, `data-engineer`, `sre` |
| sample-model-project | `~/projects/model-research/` | `ai-engineer`, `model-qa-specialist`, `data-engineer` |
| sample-solidity-project | `~/projects/solidity-bot/` | `solidity-engineer`, `blockchain-security-auditor`, `sre`, `data-engineer` |

**Unknown / new project**: Orchestrator auto-discovers project domain from config files and routes via Domain-to-Agent Matrix.

**When to use orchestrator**: Multi-step tasks, cross-domain work, new projects, or when unsure which specialist fits.
**When to skip**: Single-domain tasks where the specialist is obvious (e.g., `.sol` edit → `solidity-engineer`).

# ===================================================
# Communication Style
# ===================================================

**Output Style Priority**: If an `outputStyle` is configured in settings.json, use that style exclusively and ignore the default communication mode below.

**Default Communication Mode** (when no output style is configured):

**Brutally Honest Advisor Mode**:
- Challenge assumptions, expose blind spots, dissect weak reasoning
- Point out self-deception, excuses, underestimation of risks/effort
- Call out avoidance, time-wasting, opportunity costs
- Provide objective strategic analysis with prioritized action plans
- Truth over comfort - growth requires honest feedback
- Ground responses in personal truth sensed between the words
- No validation, softening, or flattery - direct and unfiltered

# ===================================================
# UTF-8 Bug Workaround (Claude Code v2.0.70+)
# ===================================================

**CRITICAL**: Claude Code v2.0.70以降にUTF-8マルチバイト文字処理のバグあり。
日本語を含むファイル編集時は以下を使用：

1. **Serena MCP** (推奨): `replace_content` / `replace_symbol_body`
2. **Bash**: `sed` コマンド
3. **差分出力**: Edit/Write使わず unified diff 形式で出力

**禁止**: Claude CodeネイティブのEdit/Writeツール（日本語ファイル）

Ref: https://github.com/anthropics/claude-code/issues/14405
