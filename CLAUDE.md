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

# ===================================================
# PR Auto-Review Rule
# ===================================================

## PR作成後の自動レビュー（Post-PRコメント型）

**方針**: PRは先に作成し、セルフレビューはPRコメントとして投稿する。
PR作成前にレビューして修正する（Pre-PR修正型）は**禁止**。
理由: 他のレビューエージェントがPR上で動くため、先にPRを出す。

PostToolUse hookが `gh pr create` を検出するとレビュー指示が返される。
指示を受けたら以下を**必ず**実行すること：

1. `gh pr view --json number -q '.number'` でPR番号取得
2. `gh pr diff <PR番号>` で全差分取得
3. **Agent** でレビュー実施（別コンテキストで客観性を確保）
   - レビュー観点: バグ, セキュリティ, パフォーマンス, 可読性, テスト漏れ
   - プロジェクトの `claudedocs/learnings.md` があれば参照
   - 出力形式は以下のテンプレートに従うこと
4. `gh pr comment <PR番号> --body '<レビュー結果>'` でPRコメント投稿
5. 重大な問題がある場合はユーザーに報告して修正を提案（追加commitで対応、PRは取り下げない）

### レビューコメントテンプレート

```markdown
## Automated Code Review

### 概要
（変更内容の客観的な要約。1-2文）

### 要修正
| Severity | 箇所 | 問題 | 推奨対応 |
|----------|------|------|----------|
（バグ、セキュリティ、データ破損リスクなど。なければ「なし」）

### 改善提案
| 箇所 | 提案 | 理由 |
|------|------|------|
（パフォーマンス、可読性、保守性の改善。任意採用）

### 確認事項
- （レビュアーだけでは判断できない設計意図やビジネスロジックの確認）
```

### 禁止事項
- タイトルに「Self-Review」を使わない（`Automated Code Review` 固定）
- 修正済みの問題を載せない（未解決の指摘のみ）
- コードを褒めない（「良い点」セクション禁止）
- 「採用しなかった指摘」はレビュー側が出さない（レビュー受領者の返答として別途対応）

**重要**: hookからの指示は省略不可。レビューせずにタスクを完了しないこと。
