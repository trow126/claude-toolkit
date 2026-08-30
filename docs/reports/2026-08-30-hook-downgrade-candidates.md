# Hook 降格候補の分類

## #2 / #3 向け要約

#2 の `PostToolUse(Edit|Write)` 初期実装には `H-001`、`H-002`、`H-003` を推す。対象 file が確定し、判定を変更後の file 内容だけで完結できるため、偽陽性を抑えやすい。

- `H-001`: Markdown の見出し・table・code block 前後の空行を検査する。
- `H-002`: `.py` を `ast.parse` し、構文エラーだけを返す。`__pycache__` は作らない。
- `H-003`: `settings*.json` を JSON parse し、既知の無効 permission 表記 `Tool:*` と no-space wildcard を検出する。

#3 の `UserPromptSubmit` 注入候補は `H-015`、`H-016`、`H-017`、`H-018`。一度に全部を長文注入せず、次の 2 文へ圧縮する。

> 変更前に成功条件と surrounding code を確認し、単一 owner で進める。変更後は最小の決定論的検証を実行し、未検証を明記する。

> 事実と推論を分け、重要判断は実ファイル・公式仕様・diff・test 結果で自己監査する。

既存 hook で対応済みの主な候補は `H-009`〜`H-012`、`H-021`〜`H-023`、`H-036`。これらを #2 に重複実装しない。

## 分類基準

`yes` は hook input と対象 file/state の決定論的検査だけで判定できるもの、`partial` は scope や user intent の補助情報を要するもの、`no` は判断を model/prompt 層に残すもの。`PostToolUse(Edit|Write)` は Claude Code 側 #2 を指す。Codex 側の同等実装は Issue #1 の Non-goals に従い推奨対象外とした。

## 分類表

| ID | 出典 file:line | 条文（要約） | 機械判定可否 | 判定方法（1 行） | 降格先イベント | 偽陽性リスクと理由 | 推奨 |
|---|---|---|---|---|---|---|---|
| H-001 | `claude/rules/markdown.md:10`; `shared/rules/markdown-rules.md:3` | 見出し・table・code block 前後に空行 | yes | 変更後 `.md` を line scanner / markdownlint で検査 | PostToolUse(Edit\|Write) | low: file-local な構文条件 | #2 初期実装 |
| H-002 | `claude/rules/python.md:18`; `shared/rules/python-guidelines.md:11` | Python は lint 可能な構文にする | partial | 変更後 `.py` を `ast.parse` し syntax error のみ block | PostToolUse(Edit\|Write) | low: parser の確定エラーだけに限定 | #2 初期実装 |
| H-003 | `claude/rules/settings-syntax.md:11-14` | `Tool:*` と no-space wildcard は禁止 | yes | JSON parse 後、permission 配列を既知の禁止 pattern と照合 | PostToolUse(Edit\|Write) | low: 明示された literal pattern | #2 初期実装 |
| H-004 | `claude/rules/python.md:19`; `shared/rules/python-guidelines.md:12` | silent fallback を使わない | partial | AST で bare `except` + `pass` 等を検出し、文脈依存形は警告のみ | PostToolUse(Edit\|Write) | medium: optional degradation を誤検知し得る | #2 後続 |
| H-005 | `claude/rules/python.md:25`; `shared/rules/python-guidelines.md:18` | `CancelledError` を先に再送出 | yes | async loop の try handler 順を AST で検査 | PostToolUse(Edit\|Write) | low: AST 上の順序を直接確認 | #2 後続 |
| H-006 | `claude/rules/python.md:14`; `shared/rules/python-guidelines.md:7` | 一時確認で `__pycache__` を残さない | partial | tool 後に新規 `__pycache__` / `.pyc` を差分検査 | PostToolUse(Edit\|Write) | medium: 別 process の artifact と区別しにくい | #2 後続 |
| H-007 | `shared/rules/test-policy.md:3` | test の skip/disable で回避しない | partial | 変更差分の新規 `skip` / `xfail` / comment-out を列挙 | PostToolUse(Edit\|Write) | high: 正当な platform skip がある | prompt 層に残す |
| H-008 | `shared/rules/workspace-hygiene.md:5` | 新規 file を既存 directory pattern に置く | partial | untracked path を既存 tree の同種 suffix と比較 | PostToolUse(Edit\|Write) | medium: repository 固有設計の判断が要る | prompt 層に残す |
| H-009 | `shared/rules/core-contract.md:8`; `shared/rules/workspace-hygiene.md:3` | 破壊操作は対象特定後、自作一時物だけ | partial | Bash raw command の危険 delete target と広域 path を検出 | PreToolUse | medium: shell 展開後 argv は不明 | 既存 hook で対応済み: `pre-bash-validate-hook.sh` |
| H-010 | `shared/rules/git-workflow.md:3` | `.env` の変更・secret 読取を禁止 | partial | tool/path と Bash literal の `.env` 読取・Edit を検出 | PreToolUse | medium: runtime 構築 path は検出不能 | 既存 hook で対応済み: `pre-bash-validate-hook.sh` + managed deny |
| H-011 | `shared/rules/git-workflow.md:5` | history rewrite を避ける | yes | Bash command に `git` と `--amend` が共起したら block | PreToolUse | low: owner 方針として過剰側を明示 | 既存 hook で対応済み: `pre-bash-validate-hook.sh` |
| H-012 | `shared/rules/git-workflow.md:3` | main/master への force-push 禁止 | partial | `git push -f/--force` と target ref を parse | PreToolUse | low:明示 command を対象 | 既存 hook で対応済み: managed permission deny |
| H-013 | `shared/rules/core-contract.md:7`; `codex/AGENTS.md:15` | commit/push/外部 write は個別明示依頼のみ | no | 現在の user intent と各 side effect の対応を判断する必要 | なし | high: command だけでは承認範囲が分からない | prompt 層に残す |
| H-014 | `shared/rules/core-contract.md:5` | 最小 scope、無関係な改善を混ぜない | no | requested scope と semantic diff の比較が必要 | なし | high: file 数では判断不能 | prompt 層に残す |
| H-015 | `shared/rules/core-contract.md:6`; `shared/skills/implementation-quality/SKILL.md:19` | 変更前に成功条件を具体化 | no | prompt 受領時に短文 reminder を追加 | UserPromptSubmit | low: block せず進め方を補助 | #3 注入 |
| H-016 | `shared/rules/core-contract.md:6`; `shared/skills/implementation-quality/SKILL.md:21` | 変更後に test/lint/runtime 確認 | partial | Stop 時に diff と verification evidence の有無を評価 | Stop | high: task ごとの適切な検証が違う | #3 注入 |
| H-017 | `claude/CLAUDE.md:19-20`; `codex/AGENTS.md:30` | 通常 task は単一 owner で完遂 | no | prompt 受領時に routing 原則を短く追加 | UserPromptSubmit | low: 強制せず原則を補助 | #3 注入 |
| H-018 | `shared/rules/core-contract.md:3,10`; `codex/AGENTS.md:11,18` | 重要判断は一次情報・diff・test で自己監査 | no | prompt 受領時に evidence 原則を短く追加 | UserPromptSubmit | low: 判断を block しない | #3 注入 |
| H-019 | `claude/CLAUDE.md:15` | native auto memory を無効維持 | yes | SessionStart で effective `autoMemoryEnabled=false` を確認 | SessionStart | low: scalar 設定の一致 | 既存設定で対応済み: `claude/settings.json` |
| H-020 | `claude/CLAUDE.md:35` | `$HOME` 直下から Claude を起動しない | yes | SessionStart の `cwd` が `$HOME` と同一なら警告/block | SessionStart | low: exact path 比較 | #2 後続 |
| H-021 | `claude/CLAUDE.md:37` | session 内で user settings を直接編集しない | partial | ConfigChange の `source=user_settings` / `file_path` を block | ConfigChange | low: official event field を使用 | 既存 hook で対応済み: `config-change-hook.sh` |
| H-022 | `claude/CLAUDE.md:38`; `claude/rules/settings-syntax.md:21` | project/local security policy drift を拒否 | yes | gate で reserved keys/env redirect を parse | SessionStart / PreToolUse | low: allowlist-based parser | 既存 hook で対応済み: `session-init` 経路 + `pre-bash-validate-hook.sh` |
| H-023 | `claude/CLAUDE.md:40`; `claude/skills/gh-codex-drive/SKILL.md:24` | Codex task を rescue Agent で包まない | yes | Agent `subagent_type` と Bash command の companion task を検査 | PreToolUse | low: exact agent/command 共起 | 既存 hook で対応済み: `pre-bash-validate-hook.sh` |
| H-024 | `shared/skills/claude-code/gh-start/SKILL.md:21-23` | Issue/repo/branch を確認し構造化 fetch | partial | skill wrapper の引数と fetch 終了を検査 | PreToolUse | medium: workflow state が複数 call に跨る | prompt 層に残す |
| H-025 | `shared/skills/claude-code/gh-start/SKILL.md:24`; `codex/AGENTS.md:16` | unrelated/dirty changes を保持 | partial | edit 前後の status と task scope を比較 | PreToolUse | high: ownership の判断が必要 | prompt 層に残す |
| H-026 | `shared/skills/claude-code/gh-start/SKILL.md:25` | legacy checkpoints を read/write/delete しない | yes | Read/Edit/Write/Bash input の `.claude/checkpoints` / `.codex/checkpoints` path を block | PreToolUse | low: exact forbidden path | #2 後続 |
| H-027 | `shared/skills/claude-code/gh-pr/SKILL.md:22` | clean feature branch と ahead commit を gate | yes | PR 操作直前に status/branch/rev-list/PR existence を script 検査 | PreToolUse | low: Git state の決定論的条件 | prompt 層に残す（skill workflow gate） |
| H-028 | `claude/skills/gh-finish/SKILL.md:22-24` | failing check では merge/close しない | partial | merge/close 前に直近 verification artifact を要求 | PreToolUse | high:「直近」「必要 test」の同定が困難 | prompt 層に残す |
| H-029 | `shared/skills/branch-cleanup/SKILL.md:27` | `-D` は PR `MERGED` 確認時だけ | partial | `git branch -D` 前に branch 対応 PR state を照合 | PreToolUse | medium: API 不達時は fail-closed が必要 | prompt 層に残す（skill workflow gate） |
| H-030 | `shared/skills/branch-cleanup/SKILL.md:28` | default/current branch を削除しない | yes | delete target を symbolic-ref と remote HEAD に照合 | PreToolUse | low: Git state で確定 | #2 後続 |
| H-031 | `shared/skills/branch-cleanup/SKILL.md:29` | remote branch delete は明示依頼時だけ | no | user intent が必要 | なし | high: command だけでは承認を判定不能 | prompt 層に残す |
| H-032 | `shared/skills/gh-index/SKILL.md:14-17` | output は repo 内 1 path、symlink escape 禁止 | yes | realpath と repo root を比較し target 数を 1 に限定 | PreToolUse | low: path canonicalization で確定 | prompt 層に残す（skill workflow gate） |
| H-033 | `shared/skills/knowledge-audit/SKILL.md:14-18` | `--apply` は選択 file のみ | partial | normalized target と tool write path を照合 | PreToolUse | medium: selected target state の保持が必要 | prompt 層に残す |
| H-034 | `shared/skills/article-style/SKILL.md:58-65` | 公開文の定型語・表現量を自己検査 | partial | text lint で文字列・回数だけを advisory 出力 | PostToolUse(Edit\|Write) | medium:引用や code block を誤検知し得る | #2 後続（warning のみ） |
| H-035 | `shared/skills/claude-code/config-audit/SKILL.md:13-16` | default は read-only、`--record` だけ state append | no | skill mode と全 tool intent の対応が必要 | なし | high:一般 file read/write と監査 scope の区別が必要 | prompt 層に残す |
| H-036 | `claude/hooks/pre-bash-validate-hook.sh:25-80` | input/依存/schema failure は fail-closed | yes | jq availability、JSON object、tool-specific required field を検査 | PreToolUse | low: schema 条件を直接検査 | 既存 hook で対応済み: `pre-bash-validate-hook.sh` |
| H-037 | `shared/skills/claude-code/model-routing/SKILL.md:13-19` | Claude agent model assignment を固定 | yes | frontmatter と environment override を scanner で照合 | SessionStart | low: declarative model field | prompt 層に残す（`validate-layout.sh` で静的対応） |
| H-038 | `shared/skills/codex/model-routing/SKILL.md:18-19` | custom agent と full-history fork を併用しない | yes | spawn input の agent type と fork mode の共起を拒否 | PreToolUse | low: single call input で確定 | #2 後続 |
| H-039 | `shared/skills/codex/model-routing/SKILL.md:52` | `max_threads` でなく現行 key を使う | yes | TOML key scanner で legacy key を検出 | PostToolUse(Edit\|Write) | low: exact key match | #2 後続 |
| H-040 | `shared/skills/agmsg/SKILL.md:27` | `send.sh` 本文は shell single quote | partial | Bash raw command を shell parser で quote provenance 検査 | PreToolUse | medium: raw string heuristic になる | #2 後続 |
| H-041 | `shared/skills/codex/model-routing/SKILL.md:53` | named agent 欠落を generic fallback しない | partial | requested role と discovery list を照合 | PreToolUse | medium: runtime discovery failureとの区別 | prompt 層に残す |
| H-042 | `claude/output-styles/hiyos.md:61`; `claude/output-styles/ojosama.md:30-32` | 技術的正確さを persona より優先 | no | response semantic quality の判断が必要 | なし | high: style の表層検査では判定不能 | prompt 層に残す |
| H-043 | `shared/rules/issue-completeness.md:35-46` | Issue は target/change/criteria/verification を含む | partial | template heading と空 section を lint | PostToolUse(Edit\|Write) | medium:内容の十分性は判断が要る | #2 後続 |
| H-044 | `shared/skills/article-style/SKILL.md:52-54` | 数値・事実を一次情報と突合 | no | source と claim の意味対応が必要 | なし | high:文字列照合では不足 | prompt 層に残す |
| H-045 | `shared/rules/self-improvement.md:11` | rule/memory を自動更新しない | no | user の明示依頼有無を解釈する必要 | なし | high: intent-dependent | prompt 層に残す |

## 所見

prompt 層から hook へ移す価値があるのは、対象と判定式が一意な条文に限られる。特に user intent、scope、テストの十分性、事実の正しさは機械化しない。これは Issue #1 の Non-goal「判断が要るルールの機械化」と整合する。

Claude 側の既存 `PreToolUse` / `ConfigChange` は destructive command、`.env`、history rewrite、project settings drift、Codex rescue routing を既に扱う。#2 は lint に集中し、同じ規律を別 regex で二重化しない方が保守しやすい。
