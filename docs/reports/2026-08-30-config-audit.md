# 設定全体監査レポート

| 項目 | 値 |
|---|---|
| 対象 repository / branch | `trow126/agents-toolkit` / `issue-1` |
| 対象 commit | `60204e4`（`git rev-parse --short HEAD`） |
| 監査日 | 2026-08-30（Asia/Tokyo） |
| 実行環境 | Claude Code `2.1.251`、Codex CLI `0.151.0` |
| 依頼 | [GitHub Issue #1](https://github.com/trow126/agents-toolkit/issues/1) |
| 公式資料取得日時 | 2026-08-30 |

Issue の Related context にある Obsidian vault の clippings 3 件は、この環境から到達できず未読である。本監査では Issue 本文に記載された要約、すなわち「モデル更新は本体 system prompt の更新」「同じ話題に 2 指示が並ぶと一般形が負ける」「過剰制約の矛盾蓄積が最大の劣化要因」「機械判定可能ルールの hook 降格」を方法論として使用した。clippings 原文を読んだ、または原文から直接引用したとは扱わない。

Issue 本文は監査開始時に `gh issue view 1 --json body -q .body` で取得した。

## 軸 1: ハーネス仕様との整合

### 方法

次を実行し、local file、実 CLI、現行 schema、公式 documentation、公式 changelog を突き合わせた。

```bash
git rev-parse --short HEAD
claude --version
claude --help
claude doctor </dev/null
codex --version
codex doctor
codex features list
scripts/check-runtime.sh
jq -S . claude/managed-settings.json
jq -S . claude/settings.json
jq -S . codex/hooks.json
nl -ba claude/hooks/*.sh
nl -ba "$HOME/.codex/config.toml"
```

参照した一次情報は次のとおり。引用は取得時表示の原文である。

- [Claude Code settings](https://code.claude.com/docs/en/settings): 「The settings reference lists every key you can set」。同 page は schema が newest CLI release より遅れる場合があるとも明記する。
- [Claude Code settings schema](https://json.schemastore.org/claude-code-settings.json) と [SchemaStore source](https://raw.githubusercontent.com/SchemaStore/schemastore/master/src/schemas/json/claude-code-settings.json)。
- [Claude Code hooks reference](https://code.claude.com/docs/en/hooks): 「When an event fires and a matcher matches, Claude Code passes JSON context about the event to your hook handler. For command hooks, input arrives on stdin.」
- [Claude Code permissions](https://code.claude.com/docs/en/permissions) と [sandboxing](https://code.claude.com/docs/en/sandboxing)。
- [Claude Code CHANGELOG](https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md)。
- [Codex config schema](https://developers.openai.com/codex/config-schema.json)、[config reference](https://developers.openai.com/codex/config-reference)、[hooks reference](https://developers.openai.com/codex/hooks)。Codex hooks reference は現在「During a turn」に `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `UserPromptSubmit`, `SubagentStop`, `Stop` を列挙する。

#### Claude settings 全キー照合

schema と docs に対し、object の leaf まで再帰的に確認した。`claude doctor` に invalid/rejected setting の指摘はなかった。

| file | 確認した key 群 | schema/docs 結果 |
|---|---|---|
| `claude/managed-settings.json:2-6` | `$schema`, `allowManagedHooksOnly`, `allowManagedPermissionRulesOnly`, `disableAutoMode`, `skipDangerousModePermissionPrompt` | 現行 key、型も一致 |
| `claude/managed-settings.json:7-10` | `statusLine.type`, `.command`, `.padding` | 現行 key、型も一致 |
| `claude/managed-settings.json:12-109` | `permissions.allow`, `.deny`, `.ask`, `.defaultMode` | 現行 key。permission rule は current function-call syntax |
| `claude/managed-settings.json:111-213` | `sandbox.enabled`, `.failIfUnavailable`, `.allowUnsandboxedCommands`, `.filesystem.denyRead`, `.allowRead`, `.allowManagedReadPathsOnly`, `.credentials.files[].path`, `.mode`, `.credentials.envVars[].name`, `.mode`, `.excludedCommands`, `.network.allowManagedDomainsOnly`, `.network.autoAllow` | 現行 key、型も一致 |
| `claude/managed-settings.json:215-314` | `hooks.ConfigChange`, `Notification`, `PostCompact`, `PostToolUse`, `PreToolUse`, `SessionStart`, `Stop` と各 `matcher`, `hooks[].type`, `.command`, `.timeout` | 登録 event/handler は現行。unknown/deprecated event なし |
| `claude/managed-settings.json:316` | `requiredMinimumVersion` | 現行 key。値と運用契約に A1-01 |
| `claude/settings.json:2-15` | `$schema`, `attribution.commit`, `.pr`, `model`, `enabledPlugins.*`, `extraKnownMarketplaces.*.source.source`, `.source.repo` | 現行 key、型も一致 |
| `claude/settings.json:26-33` | `language`, `effortLevel`, `autoUpdatesChannel`, `tui`, `autoMemoryEnabled`, `theme`, `editorMode`, `autoCompactEnabled` | 現行 key、型も一致 |

未知 key と deprecated key は 0 件だった。repo が登録していない current event は、少なくとも `UserPromptSubmit`, `InstructionsLoaded`, `UserPromptExpansion`, `PermissionRequest`, `PermissionDenied`, `PostToolUseFailure`, `PostToolBatch`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `StopFailure`, `TeammateIdle`, `CwdChanged`, `DirectoryAdded`, `FileChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PreModelSwitch`, `PostModelSwitch`, `SessionEnd`, `Elicitation`, `ElicitationResult`, `MessageDisplay` である。未登録は直ちに欠陥ではなく、明示された用途がない event は追加しない。`UserPromptSubmit` は Issue #3 の injection layer 候補、`PostToolUse(Edit|Write)` は Issue #2 の lint 候補としてのみ扱う。

外部 SchemaStore は `2.1.251` 追加の `PreModelSwitch` / `PostModelSwitch` をまだ列挙しない。一方、公式 hooks docs と CHANGELOG は両 event を current とする。settings docs 自身が「The schema can lag behind the newest CLI releases」と記載するため、これは repo の unknown key ではなく upstream schema lag である。

#### Claude hooks stdin JSON 照合

共通 field は公式 hooks reference の `session_id`, `prompt_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name` を基準に、各 event 固有 field を照合した。

| hook | 登録 event / local 参照 field | 現行仕様との差 |
|---|---|---|
| `claude/hooks/session-init-hook.sh` | `SessionStart`; stdin を読まず process cwd / Git state を使用 | event JSON を必要としないため追加 field に非依存。差なし |
| `claude/hooks/post-compact-hook.sh` | `PostCompact`; stdin を読まず process cwd / Git state を使用 | event JSON を必要としないため追加 field に非依存。差なし |
| `claude/hooks/pre-bash-validate-hook.sh:34-87` | `PreToolUse`; `.tool_name`, `.tool_input.command`, `.tool_input.subagent_type`, `.tool_input.run_in_background`, `.cwd`; legacy `.tool_input.cwd` fallback | documented tool/common field に整合。`.tool_input.cwd` だけは undocumented fallback だが、公式 `.cwd` を優先し判定を緩和しない |
| `claude/hooks/pr-review-hook.sh` | `PostToolUse`; `.tool_name`, `.tool_input`, `.tool_response` | `PostToolUse` common/tool field と整合 |
| `claude/hooks/config-change-hook.sh:18-27` | `.file_path`, `.cwd` に加え `.tool_input.file_path`, `.path`, `.tool_input.cwd`; home 直下 `settings.local.json` | 公式 event-specific field は `source` と optional `file_path`。legacy fallback と scope 表現に A1-03 |
| `claude/hooks/herdr-agent-state.sh` | `SessionStart`; `.hook_event_name`, `.agent_id`, `.session_id` | common/subagent context field を defensive parse。差なし |
| `claude/hooks/slack-notify-hook.sh` | `Notification` の `.message`; `Stop` input は未使用 | Notification message と整合。Stop 固有 field に非依存 |

公式 `ConfigChange input` は「receive `source` and optionally `file_path`」と明記する。`claude/hooks/config-change-hook.sh:18-20` の fallback は current input では不要で、`source` を検証していない。

#### Codex config / hooks 照合

`codex/hooks.json:1-16` の `$schema`, `hooks.SessionStart[].matcher`, `hooks[].type`, `.command`, `.timeout` は current schema と docs に一致した。`~/.codex/config.toml` は repo 外の監査対象として読み取りだけを行い、編集していない。

| 対象 | 確認した key 群 | 結果 |
|---|---|---|
| `~/.codex/config.toml:1-15` | `model`, `model_reasoning_effort`, `approval_policy`, `sandbox_mode`, `web_search`, `personality`, `hide_agent_reasoning`, `show_raw_agent_reasoning`, `tool_output_token_limit`, `project_doc_max_bytes`, `model_auto_compact_token_limit`, `default_subagent_model`, `default_subagent_reasoning_effort` | schema 受理、`codex doctor` load 成功 |
| `~/.codex/config.toml:17-114` | `projects.*.trust_level`, `mcp_servers.*`, `apps.*`, `agents.*`, `tui.*` | schema 受理、参照 path/command の runtime load 成功 |
| `~/.codex/config.toml:116-118` | `features.hooks=true`, `features.memories=false` | `codex features list` で hooks stable/enabled、memories stable/disabled |
| `~/.codex/config.toml:120-125` | `hooks.state.version`, `hooks.state.notices_shown`, `hooks.state.events.session_start.trusted_hashes` | current schema に存在。repo `codex/hooks.json` の実測 hash と一致 |
| `codex/hooks.json:1-16` | `SessionStart` command hook | current hooks syntax と一致 |

`codex doctor` は config を読み込み、`gpt-5.6-sol`、approval `Never`、unrestricted sandbox を表示した。network reachability はこの実行環境の制約により失敗したが、config parse / hook trust error はなかった。公式 docs は hash 変更時に「new or changed hooks are marked for review and skipped until trusted」とする。現在の `trusted_hash` と `sha256sum codex/hooks.json` は一致した。

Codex の公式現行 hooks 仕様には `PostToolUse` と `UserPromptSubmit` が存在する。Issue #1 の Non-goal にある「Codex 側 PostToolUse 相当 event が存在しない」という前提は現行仕様とは異なる。ただし明示的 Non-goal と action safety を優先し、Codex 側 lint hook の実装・Issue 草案化はしていない。

#### `claude doctor` と version 差分

`claude doctor </dev/null` は非対話で終了した。invalid setting の指摘はなく、npm global folder が writable でないため auto-update できないという warning だけを報告した。よって `claude --help` 代替には切り替えず、`claude doctor` と `scripts/check-runtime.sh` の両結果を採用した。

`2.1.218` から `2.1.251` の間で repo に関係する CHANGELOG 項目は次のとおり。

| version / URL 行 | 原文引用 | repo との関係 |
|---|---|---|
| [2.1.219, lines 770-775](https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md) | “Added Claude Opus 5 (`claude-opus-5`), now the default Opus model” | current `opus` routing に必須。repo 下限は 1 version 古い |
| 同上 | “Added `sandbox.network.strictAllowlist` setting” | repo は `allowManagedDomainsOnly` を使い、新 key に依存しない |
| 同上 | “Added `DirectoryAdded` hook” | repo は未使用。用途なしのため追加不要 |
| 同上 | “Added the `workflowSizeGuideline` settings key” | repo は未使用。unknown key なし |
| [2.1.251, lines 1-6](https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md) | “Added `PreModelSwitch` and `PostModelSwitch` hook events” | model-specific guidance を hook 化できるが、現状は未使用 |
| 同上 | “`SessionStart` resume hooks now receive session staleness and the estimated re-cache cost” | local SessionStart hook は追加 field を無視するため互換 |
| 同上 | “Added `attach`, `logs`, `stop`, `respawn`, and `rm` to `claude --help`” | repo command contract に依存なし |

追加された関連 key/event/flag に対し、repo が使う既存 key の非推奨化は確認できなかった。

### 結果: 乖離 3 件

| ID | 対象 file:line | 事実（現状） | 期待（最新仕様・方針） | 重要度 | 対応方針 | 対応 Issue 草案 ID |
|---|---|---|---|---|---|---|
| A1-01 | `claude/managed-settings.json:316`; `scripts/check-runtime.sh:9-13,23`; `claude/CLAUDE.md:21` | 最低 version は `2.1.218` だが、routing は current `opus` alias を前提にする | Opus 5 を追加した `2.1.219` 以上を許容下限にする | medium | 下限と境界 test を同時更新 | D-01 (#4) |
| A1-02 | `claude doctor` 実測 | npm global folder が writable でなく auto-update warning | owner が選んだ install/update 経路で doctor warning なし | low | native installer または sudo 不要 npm prefix を選び再検証 | D-02 (#5) |
| A1-03 | `claude/hooks/config-change-hook.sh:18-27`; [ConfigChange input](https://code.claude.com/docs/en/hooks) | undocumented fallback field と home 直下 `settings.local.json` を受理 | `source`, optional `file_path`, common `cwd` と正しい scope を fail-closed で検査 | low | official field へ限定し fixture 更新 | D-03 (#6) |

重要度内訳は high 0、medium 1、low 2。外部 schema lag と Codex PostToolUse の Non-goal 前提差は repo 修正の乖離数に含めていない。

## 軸 2: モデル環境との整合

### 方法

```bash
rg -n '^model:' claude/agents/*.md
rg -n '^(model|model_reasoning_effort)' codex/agents/*.toml
rg -n 'model|Fable|Opus|Sonnet|Haiku' claude/CLAUDE.md shared/skills/*/model-routing/SKILL.md codex/AGENTS.md
rg -n 'keep-coding-instructions|model|effort' claude/output-styles/*.md
```

main system prompt は repo 外の空 directory で指定の headless command を RUN 1〜4 と owner 直接再実行 RUN 5 の計 5 回実行した。RUN 1〜4 は Codex 実行環境で無出力または timeout、RUN 5 は同一 command に 19 秒で応答し、逐語引用を拒否して本体 prompt の構成一覧を返した。詳細は [system prompt overlap 実測記録](2026-08-30-system-prompt-overlap.md)、生出力は [raw 記録](2026-08-30-system-prompt-fable5-raw.txt) にある。公式 settings docs は「Claude Code’s system prompt isn’t published」と明記している。

逐語原文の代替として、RUN 5 から得た節構成 S1〜S16 と、同一 harness prompt を受けている Fable 5 main session の in-session 判定を用いて 138 条文を比較した。in-session 判定は headless では再現できない観察である。前回の network/provider reachability という原因推定は撤回し、RUN 1〜4 の失敗は Codex 実行環境の非 PTY exec wrapper 起因と推定するが、確定はしていない。

現行 Claude lineup は user が提示した harness の事実を一次情報として使用し、web 情報で上書きしていない。

#### Claude routing の一致

| 対象 | 指定 | 現行 model への解決 | routing 方針 | 判定 |
|---|---|---|---|---|
| `claude/settings.json:7` | `claude-fable-5[1m]` | Fable 5 | main lead/advisor | 一致。`[1m]` は current CLI が受理 |
| `claude/agents/ai-engineer.md:5` | `sonnet` | `claude-sonnet-5` | domain implementation | 一致 |
| `claude/agents/blockchain-security-auditor.md:5` | `opus` | `claude-opus-5` | high-risk independent audit | 一致 |
| `claude/agents/code-reviewer.md:5` | `sonnet` | `claude-sonnet-5` | independent review | 一致 |
| `claude/agents/data-engineer.md:5` | `sonnet` | `claude-sonnet-5` | domain implementation | 一致 |
| `claude/agents/deep-reasoner.md:5` | `opus` | `claude-opus-5` | high-risk reasoning | 一致 |
| `claude/agents/explore.md:5` | `haiku` | `claude-haiku-4-5-20251001` | read-only exploration | 一致 |
| `claude/agents/model-qa-specialist.md:5` | `sonnet` | `claude-sonnet-5` | domain review | 一致 |
| `claude/agents/plan-reviewer.md:5` | `sonnet` | `claude-sonnet-5` | plan review | 一致 |
| `claude/agents/solidity-engineer.md:5` | `sonnet` | `claude-sonnet-5` | domain implementation | 一致 |
| `claude/agents/sre.md:5` | `sonnet` | `claude-sonnet-5` | domain implementation | 一致 |

`claude/CLAUDE.md:21-23` と `shared/skills/claude-code/model-routing/SKILL.md:13-19` は Fable main、Opus teammate/anonymous worker、高 risk Opus、Explore Haiku、named agent frontmatter 尊重を一貫して定義する。`~/.claude.json` の `teammateDefaultModel` は `opus`、`CLAUDE_CODE_SUBAGENT_MODEL` は未設定で、effective routing とも一致した。

#### Codex routing の一致

| 対象 | model / effort | `~/.codex/config.toml` との関係 | 判定 |
|---|---|---|---|
| `codex/agents/deep_reasoner.toml:3-4` | `gpt-5.6-sol` / `xhigh` | parent/default は Sol、role は high-risk escalation | 一致 |
| `codex/agents/explorer.toml:3-4` | `gpt-5.6-terra` / `medium` | read-only exploration の明示 override | 一致 |
| `codex/agents/plan_reviewer.toml:3-4` | `gpt-5.6-sol` / `high` | parent/default と同系統、review effort 固定 | 一致 |
| `codex/agents/reviewer.toml:3-4` | `gpt-5.6-sol` / `high` | parent/default と同系統、review effort 固定 | 一致 |
| `~/.codex/config.toml:3-4,13-14` | main/default subagent `gpt-5.6-sol`; main `high`; default subagent `high` | `codex/AGENTS.md:30-33` と `shared/skills/codex/model-routing/SKILL.md:18` に一致 | 一致 |

#### output style の静的確認

| file | opt-in / coding instruction | Fable 5 との判定 |
|---|---|---|
| `claude/output-styles/darasan.md:1-4` | named style、`keep-coding-instructions: true` | persona は opt-in。model/routing/security を上書きしない |
| `claude/output-styles/hiyos.md:1-4,61` | 同上、技術的正確さを style より優先 | 静的矛盾なし |
| `claude/output-styles/kuroko.md:1-4` | named style、`keep-coding-instructions: true` | 静的矛盾なし |
| `claude/output-styles/ojosama.md:1-4,30-32` | 同上、技術的正確さを優先 | 静的矛盾なし |

output style は `claude/settings.json` で常時指定されておらず opt-in である。本体 Fable 5 の逐語原文は取得できなかったため、既定挙動との逐語比較はしていない。

### 結果: 改善候補 2 件

model ID、alias、frontmatter、Codex custom agents、main/default routing の範囲では乖離なし。system prompt overlap は代替法で判定し、重複 4 件、部分重複/補完 6 件、矛盾 1 件、部分矛盾 2 件を確認した。

| ID | 対象 file:line | 事実（現状） | 期待（最新仕様・方針） | 重要度 | 対応方針 | 対応 Issue 草案 ID |
|---|---|---|---|---|---|---|
| A2-01 | `shared/rules/core-contract.md:5,8`; `claude/CLAUDE.md:39`; `shared/rules/git-workflow.md:4-5` | 本体 harness prompt と重複する | 常時注入は本体にない意味だけを短く保持する | low | 短縮候補 | D-09 (#12) |
| A2-02 | `claude/CLAUDE.md:40`; plugin 由来 agent 説明; `claude/hooks/pre-bash-validate-hook.sh:47-48,105-108` | 本体は `codex:codex-rescue` の積極利用を促すが user 条文は禁止する | hook 強制を維持し、prompt は理由説明に限定する | low | hook 強制済みのため条文短縮のみ | D-09 (#12) |

重要度内訳は high 0、medium 0、low 2。逐語原文の非公開と in-session 判定の headless 再現不能は、repo 原因の乖離には含めていない。

## 軸 3: 運用知見との整合

### 方法

対象文書の bullet を file:line 単位で抽出し、hook input と file/state だけで決定論的に判定できるか、user intent/semantic judgment が必要か、既存 hook が対応済みかを分類した。

```bash
nl -ba claude/CLAUDE.md
nl -ba shared/rules/*.md
nl -ba claude/rules/*.md
nl -ba codex/AGENTS.md
find claude/skills shared/skills -name SKILL.md -type f -print | sort
nl -ba claude/hooks/*.sh
jq -S . codex/hooks.json
```

全 45 候補と検査式は [hook 降格候補の分類表](2026-08-30-hook-downgrade-candidates.md) に記録した。Issue 本文に要約された運用知見に従い、判断を要する rule は prompt 層に残し、file-local で fail condition が一意なものだけ hook 候補とした。

#### Issue #2 の初期実装候補

| 候補 ID | check | 偽陽性を抑える境界 |
|---|---|---|
| H-001 | 変更後 `.md` の見出し・table・code block 前後の空行 | Markdown file だけを対象にし、構文違反の line を advisory 表示 |
| H-002 | 変更後 `.py` を `ast.parse` | style/typing を判定せず syntax error だけを報告し、`__pycache__` を作らない |
| H-003 | `settings*.json` を JSON parse し `Tool:*` と no-space wildcard を検出 | 既知の invalid literal pattern だけを対象にする |

初期実装では H-001〜H-003 の 3 check を推す。H-004 以降の silent fallback、test skip、workspace placement、issue completeness は文脈依存または偽陽性が高く、後続 warning か prompt 層に残す。

#### Issue #3 の短文 injection 候補

長い rule 群を再注入せず、H-015〜H-018 を次の 2 文へ圧縮する。

> 変更前に成功条件と surrounding code を確認し、単一 owner で進める。変更後は最小の決定論的検証を実行し、未検証を明記する。

> 事実と推論を分け、重要判断は実ファイル・公式仕様・diff・test 結果で自己監査する。

`UserPromptSubmit` は prompt の model 処理を待たせるため、公式 docs が示す timeout behavior を考慮し、短い deterministic command と bounded output にする。既存 PreToolUse/ConfigChange hook が扱う destructive command、`.env`、history rewrite、project settings drift、Codex rescue routing は重複実装しない。

### 結果: 改善候補 3 件

H-001〜H-003 は「現在 prompt に残っているが機械判定へ降格できる」low の運用 drift とした。修正先は既存 Issue #2 であり、新しい重複草案は作成しない。Issue #3 の短文は enforcement ではなく進め方の optional injection 候補で、乖離数に含めない。

| ID | 対象 file:line | 事実（現状） | 期待（最新仕様・方針） | 重要度 | 対応方針 | 対応 Issue 草案 ID |
|---|---|---|---|---|---|---|
| A3-01 | `claude/rules/markdown.md:10`; `shared/rules/markdown-rules.md:3` | Markdown 空行規則が prompt/rule のみ | file-local lint へ降格し prompt 重量を減らす | low | H-001 を #2 初期実装へ | 既存 #2（草案化対象外） |
| A3-02 | `claude/rules/python.md:18`; `shared/rules/python-guidelines.md:11` | Python syntax correctness が広い品質規則に含まれる | syntax error だけ `ast.parse` で判定 | low | H-002 を #2 初期実装へ | 既存 #2（草案化対象外） |
| A3-03 | `claude/rules/settings-syntax.md:11-14` | invalid permission literal が prompt/rule のみ | JSON parse 後の exact pattern lint へ降格 | low | H-003 を #2 初期実装へ | 既存 #2（草案化対象外） |

重要度内訳は high 0、medium 0、low 3。

## 軸 4: 契約と実体の整合

### 方法

```bash
nl -ba docs/contracts/context-consumers.tsv
nl -ba docs/contracts/skill-authority.tsv
nl -ba docs/contracts/skill-dependencies.tsv
nl -ba docs/reports/inventory-elements.tsv
find claude/skills shared/skills codex/skills -name SKILL.md -type f -print | sort
rg -n 'core-contract|failure-investigation|git-workflow|issue-completeness|learnings|markdown-rules|python-guidelines|self-improvement|test-policy|workspace-hygiene' claude codex shared
sha256sum claude/managed-settings.json claude/settings.json
scripts/validate-layout.sh
tests/test-measure-metrics.sh
tests/test-report-consistency.sh
```

`scripts/validate-layout.sh` が既に検出する path/symlink/frontmatter/schema の形式不正は除外し、consumer trigger、authority mode、inventory meaning、decision record binding の意味的 drift だけを確認した。

#### context consumer 全行

| contract 行 | consumer の実参照 | 判定 |
|---|---|---|
| `docs/contracts/context-consumers.tsv:2` core-contract / Claude | `claude/CLAUDE.md:5` が `@~/.agents/rules/core-contract.md` | 一致 |
| `docs/contracts/context-consumers.tsv:3` core-contract / Codex | `codex/AGENTS.md:8-19` に同期 block | 一致 |
| `docs/contracts/context-consumers.tsv:4` failure-investigation | `shared/skills/implementation-quality/SKILL.md:14` | 一致 |
| `docs/contracts/context-consumers.tsv:5` git-workflow / git-operations | `shared/skills/git-operations/SKILL.md:8` | 参照はあるが trigger scope に A4-03 |
| `docs/contracts/context-consumers.tsv:6` git-workflow / gh skills | `shared/skills/{claude-code,codex}/gh-{start,pr,review}/SKILL.md:9` | 一致 |
| `docs/contracts/context-consumers.tsv:7` issue-completeness | `codex/skills/issue-writing/SKILL.md:8` | 一致 |
| `docs/contracts/context-consumers.tsv:8` learnings | `shared/skills/implementation-quality/SKILL.md:17` | 一致 |
| `docs/contracts/context-consumers.tsv:9` markdown-rules | `claude/rules/markdown.md:6-11`; `shared/skills/implementation-quality/SKILL.md:16` | 一致 |
| `docs/contracts/context-consumers.tsv:10` python-guidelines | `claude/rules/python.md:6-37`; `codex/references/python-quality.md:6-37` | 一致 |
| `docs/contracts/context-consumers.tsv:11` self-improvement | `shared/skills/knowledge-audit/SKILL.md:9` | 一致 |
| `docs/contracts/context-consumers.tsv:12` test-policy | `shared/skills/implementation-quality/SKILL.md:12` | 一致 |
| `docs/contracts/context-consumers.tsv:13` workspace-hygiene | `shared/skills/implementation-quality/SKILL.md:13` | 一致 |

#### active skill 全列挙と authority

同名の Claude/Codex wrapper は 1 logical skill として authority 名を照合しつつ、active `SKILL.md` path はすべて列挙した。

| active SKILL.md | authority table |
|---|---|
| `claude/skills/gh-codex-drive/SKILL.md` | 未登録: `gh-codex-drive` |
| `claude/skills/gh-finish/SKILL.md` | 未登録: `gh-finish` |
| `claude/skills/gh-roadmap-drive/SKILL.md` | 未登録: `gh-roadmap-drive` |
| `codex/skills/claude-second-opinion/SKILL.md` | 未登録: `claude-second-opinion` |
| `codex/skills/doctor/SKILL.md` | 未登録: `doctor` |
| `codex/skills/issue-writing/SKILL.md` | 未登録: `issue-writing` |
| `codex/skills/kaggle/SKILL.md` | 未登録: `kaggle` |
| `shared/skills/agmsg/SKILL.md` | 登録済み |
| `shared/skills/article-style/SKILL.md` | 登録済み |
| `shared/skills/branch-cleanup/SKILL.md` | 未登録: `branch-cleanup` |
| `shared/skills/claude-code/break-consensus/SKILL.md` | 未登録: `break-consensus` |
| `shared/skills/claude-code/config-audit/SKILL.md` | 登録済み |
| `shared/skills/claude-code/gh-issue/SKILL.md` | 登録済み |
| `shared/skills/claude-code/gh-pr/SKILL.md` | 登録済み |
| `shared/skills/claude-code/gh-review/SKILL.md` | 登録済み |
| `shared/skills/claude-code/gh-start/SKILL.md` | 登録済み |
| `shared/skills/claude-code/model-routing/SKILL.md` | 未登録: `model-routing` |
| `shared/skills/claude-code/plan-review/SKILL.md` | 未登録: `plan-review` |
| `shared/skills/claude-code/pr-review/SKILL.md` | 未登録: `pr-review` |
| `shared/skills/codex/break-consensus/SKILL.md` | 未登録: `break-consensus` |
| `shared/skills/codex/config-audit/SKILL.md` | 登録済み |
| `shared/skills/codex/gh-issue/SKILL.md` | 登録済み |
| `shared/skills/codex/gh-pr/SKILL.md` | 登録済み |
| `shared/skills/codex/gh-review/SKILL.md` | 登録済み |
| `shared/skills/codex/gh-start/SKILL.md` | 登録済み |
| `shared/skills/codex/model-routing/SKILL.md` | 未登録: `model-routing` |
| `shared/skills/codex/plan-review/SKILL.md` | 未登録: `plan-review` |
| `shared/skills/codex/pr-review/SKILL.md` | 未登録: `pr-review` |
| `shared/skills/gh-index/SKILL.md` | 登録済み。ただし `--force` mode は未登録 |
| `shared/skills/git-operations/SKILL.md` | 登録済み |
| `shared/skills/implementation-quality/SKILL.md` | 登録済み |
| `shared/skills/knowledge-audit/SKILL.md` | 登録済み |
| `shared/skills/python-refactor-analysis/SKILL.md` | 未登録: `python-refactor-analysis` |

logical skill 13 種と `gh-index --force` mode が未登録である。特に GitHub write、branch deletion、external process、repair action を持ち得る skill を authority table だけでは監査できない。

#### dependency、inventory、accepted exception

`docs/contracts/skill-dependencies.tsv:2-3` の `gh-issue -> issue-writing` は、Claude/Codex とも install manifest および `SKILL.md` の read 条件に一致し、drift はない。

`docs/reports/inventory-elements.tsv` の current `after_path` / `disposition` を tree と照合した結果、`docs/reports/inventory-elements.tsv:33` だけが `branch-cleanup` の canonical source を `claude/skills/branch-cleanup/SKILL.md` とするが、実体は `shared/skills/branch-cleanup/SKILL.md` であった。runtime install path と source after_path の混同である。

accepted exception は次の実測となった。

| record | 台帳の artifact SHA-256 | current `sha256sum` | 判定 |
|---|---|---|---|
| `docs/reports/accepted-exceptions.md:13` EX-003 | `7e1a7aabf093d4d85f39845245795aa5c5246a424846cf4c7de4d5b128ce8a8b` | `db505068ec4de279f7951588d64477f2f4de0628b229bd73ba760b743d5f72b7` (`claude/managed-settings.json`) | mismatch |
| `docs/reports/accepted-exceptions.md:14` EX-004 | `76f03e41022402ba46320d433a645937daf9b87bd05bbecdd92ba1769dbe136a` | `b192677f0450318faec59f0c4573f380d197818bf6775e1046187ca893e2b8f6` (`claude/settings.json`) | mismatch |

hash mismatch は例外 decision が current artifact を承認したことを証明できないという意味であり、policy 自体が誤りと推定したものではない。owner 再確認なしの hash 更新も行わない。

### 結果: 乖離 5 件

| ID | 対象 file:line | 事実（現状） | 期待（最新仕様・方針） | 重要度 | 対応方針 | 対応 Issue 草案 ID |
|---|---|---|---|---|---|---|
| A4-01 | `docs/reports/accepted-exceptions.md:13-14` | EX-003/004 の artifact hash が current file と不一致 | active exception は exact current artifact と owner decision を結ぶ | high | owner が diff と policy 継続を確認後に更新または close | D-04 (#7) |
| A4-02 | `docs/contracts/skill-authority.tsv:1-34` と上記 active 一覧 | 13 logical skill と `gh-index --force` の authority 行がない | active skill/mode の side effect authority を全件定義 | high | table と validator を拡張 | D-05 (#8) |
| A4-03 | `docs/contracts/context-consumers.tsv:5`; `shared/skills/git-operations/SKILL.md:8` | contract は generic Git、consumer は mutating Git の前だけ読む | trigger と実読込条件を同一 scope にする | low | どちらを正とするか決めて同期 | D-06 (#9) |
| A4-04 | `docs/reports/inventory-elements.tsv:33`; `shared/skills/branch-cleanup/SKILL.md:1` | after_path が非実体の Claude path | canonical shared source と install mapping を区別 | low | inventory と semantic test を更新 | D-07 (#10) |
| A4-05 | `tests/test-measure-metrics.sh`; `tests/test-report-consistency.sh`; `docs/plans/2026-07-23-agents-toolkit-modernization.md` の `metrics:after` block | test は `claude_skills=18`、report は 18 / 31 / 72766 のままだが、実測は `claude_skills=21`、`active_skill_entrypoints=34`、`active_skill_entrypoint_bytes=80740`。clean `master` (`60204e4`) でもこの 2 tests だけが変更前から FAIL し、他 15 件は PASS | test 期待値と `metrics:after` block を実測へ同期し、skill 追加時に両者を更新する | medium | commit `2749265` と `eee8652` で増えた 3 skill の同期漏れを修正し、更新手順または生成を検討 | D-08 (#11) |

重要度内訳は high 2、medium 1、low 2。

## Issue #1 完了条件

| 完了条件 | 状況 | 根拠 |
|---|---|---|
| 4 軸の監査結果が記録され、乖離に根拠・重要度・対応方針がある | 充足 | 本ファイルの軸 1〜4 と A1/A2/A3/A4 表。乖離ごとの修正 Issue は #4〜#12 として作成済み（草案 D-01〜D-09 に対応） |
| 本体 system prompt と常時/遅延 instruction の重複・矛盾を実測する | 充足 (代替法) | [system prompt overlap](2026-08-30-system-prompt-overlap.md) と [raw](2026-08-30-system-prompt-fable5-raw.txt)。RUN 5 の節構成と Fable 5 main session の in-session 判定で 138 条文を比較し、重複 4、部分重複/補完 6、矛盾 1、部分矛盾 2 |
| 機械判定可能 rule の hook 降格候補を分類する | 充足 | [hook 降格候補](2026-08-30-hook-downgrade-candidates.md) の 45 行、#2/#3 要約 |
| 常時注入量 baseline と修正 Issue 草案を残す | 充足 | [baseline](baseline-2026-08-30.txt) と [Issue 草案](2026-08-30-config-audit-issues.md) |

## 未実施・未確認

- Obsidian clippings 3 件は環境から到達不能のため未読。Issue 本文の要約だけを方法論に使用した。
- system prompt の逐語原文は公式に非公開で、RUN 5 でも model が引用を拒否したため未取得。in-session 判定の headless 再現も未確認である。
- 個別 project settings の監査、判断を要する rule の機械化、Codex 側 PostToolUse lint 実装は Issue #1 の Non-goals により未実施。
- 修正実装、existing file の変更、GitHub Issue 作成は action safety により未実施。owner は D-04 で例外 policy の継続可否を判断する必要がある。

## Verification loop

2026-08-30 に最終成果物を対象として実行した。

| 検証 | 結果 |
|---|---|
| `scripts/validate-layout.sh` | PASS。`claude/settings.json:7` の runtime-managed model warning 1 件だけで violation なし |
| `shared/bin/sync-shared-rules.sh --check` | 成功: `OK: all synced blocks match canonical sources` |
| `scripts/package-release.sh --check` | 直接実行は新規 report が untracked のため gate で失敗。6 report path だけを `/tmp` の一時 `core.excludesFile` で隠して同 command を再実行し、`PASS: release archive is clean (452 entries)`。一時 file/directory は削除済み。これは HEAD archive の clean check であり、新規 report の package inclusion は commit 後に owner が再確認する |
| `tests/test-measure-metrics.sh` / `tests/test-report-consistency.sh` | 診断どおり FAIL。前者は `claude_skills` の期待 18 / 実測 21、後者は report の 18 / 31 / 72766 と実測 21 / 34 / 80740 の差だけを検出（A4-05 / D-08） |
| `git status --short --untracked-files=all` | PASS: 上記 6 files が `??` のみ。`M`、staged、tracked file write なし |
| 追加 Markdown の空行規則 | PASS: 4 `.md` に対し見出し・table・fenced code block の前後を line scanner で検査。trailing whitespace なし |
| 監査 report / Issue 草案 ID | PASS: report の `D-01`〜`D-09` と草案の H2 ID の `comm -3` 出力なし |
| RUN 5 raw stdout | PASS: owner raw 24 行との `diff -u` 出力なし |
