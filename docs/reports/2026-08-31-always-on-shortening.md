# 常時注入条文の短縮結果

GitHub Issue #12「本体 harness prompt と重複・矛盾する常時注入条文を短縮する」に対応し、[system prompt 重複・矛盾実測](2026-08-30-system-prompt-overlap.md) の A2-01 / A2-02 対象を短縮した。Claude Code harness、core contract、SessionStart hook、PreToolUse hook が既に担う説明を削り、repository 固有条件と hook にない制約は維持した。

## メトリクス

| metric | before (master) | after |
|---|---:|---:|
| `claude_md_bytes` | 3119 | 3144 |
| `claude_imported_shared_bytes` | 1407 | 1269 |
| `claude_always_on_total` | 4526 | 4413 |
| `codex_agents_md_bytes` | 3564 | 3426 |
| `combined_always_on_total` | 8090 | 7839 |
| `shared_rules_always_on_bytes` | 1407 | 1269 |
| `shared_rules_on_demand_bytes` | 10544 | 10407 |

after は `scripts/measure-metrics.sh --repo .` の実測値である。

## 条文差分

### 1. `shared/rules/core-contract.md:5`

変更前:

```text
- 依頼された成果に必要な最小scopeで、既存の構造・規約・surrounding codeに適合する完成した変更を行う。無関係な改善を混ぜない。
```

変更後:

```text
- 依頼scopeに限定し、既存の構造・規約・surrounding codeに適合する完成した変更を行う。
```

### 2. `shared/rules/core-contract.md:8`

変更前:

```text
- 破壊操作の対象は事前にread-onlyで特定する。ユーザー所有・既存・無関係なfileやstateを削除せず、片付けは現在の作業で自分が作成した安全な一時物に限定する。
```

変更後:

```text
- 破壊操作は対象を事前にread-onlyで特定してから行い、片付けは自分が作成した安全な一時物に限定する。
```

### 3. `claude/CLAUDE.md:39`

変更前:

```text
- Git操作はpromptなしで実行され得るため、commit・push・外部writeの個別承認を厳守する。
```

変更後:

```text
- bypassPermissions下ではGit操作がpromptなしで実行されるため、commit・push・外部writeの承認はcore contractに従う。
```

### 4. `claude/CLAUDE.md:40`

変更前:

```text
- Codexへのtask委任は`codex:codex-rescue` Agentで包まない。Claudeのmain sessionから`codex-companion.mjs task`を直接`Bash(run_in_background=true)`で起動し、完了通知のownerをmain sessionに保つ。
```

変更後:

```text
- Codex委任は`codex:codex-rescue` Agentで包まない（hookが拒否し、完了通知がmain sessionに届かない）。`codex-companion.mjs task`はmain sessionから`Bash(run_in_background=true)`で起動する。
```

### 5. `shared/rules/git-workflow.md:4-5`

変更前:

```text
- 作業は feature ブランチで行い、セッション開始時に `git status` / `git branch` で現在地を確認する
- 明示的な依頼なしにコミットしない。依頼されたコミットは意味単位で分割し、ステージング前に `git diff` で内容を確認する
```

変更後:

```text
- 作業は feature ブランチで行う
- 依頼されたコミットは意味単位で分割し、ステージング前に `git diff` で内容を確認する
```

## 強制と期待値の同期

`CLAUDE.md:40` の禁止は `claude/hooks/pre-bash-validate-hook.sh` が引き続き強制する。`tests/test-pre-bash-hook.sh` の「codex-rescue Agent は background指定でも block」「Agent block理由が main session ownership を指示する」「codex-rescue の task --background を block」「codex-rescue の Bash run_in_background=true を block」「codex-rescue の foreground task も block」「main session相当の companion Bash background は許可」で、禁止理由と正しい起動経路を検証する。

byte 数の追随期待値は `tests/test-measure-metrics.sh` の `shared_rules_always_on_bytes` を 1407 から 1269 へ更新した。他の test に変更済み byte 数または対象条文の固定期待値はなかった。
