# 設定監査の修正 Issue 草案

本ファイルは草案の記録である。GitHub Issue は 2026-08-30 に owner の明示依頼で作成済みで、対応は次のとおり。

| 草案 ID | GitHub Issue |
|---|---|
| D-01 | [#4](https://github.com/trow126/agents-toolkit/issues/4) |
| D-02 | [#5](https://github.com/trow126/agents-toolkit/issues/5) |
| D-03 | [#6](https://github.com/trow126/agents-toolkit/issues/6) |
| D-04 | [#7](https://github.com/trow126/agents-toolkit/issues/7) |
| D-05 | [#8](https://github.com/trow126/agents-toolkit/issues/8) |
| D-06 | [#9](https://github.com/trow126/agents-toolkit/issues/9) |
| D-07 | [#10](https://github.com/trow126/agents-toolkit/issues/10) |
| D-08 | [#11](https://github.com/trow126/agents-toolkit/issues/11) |
| D-09 | [#12](https://github.com/trow126/agents-toolkit/issues/12) |

各草案は `$HOME/.github/ISSUE_TEMPLATE/implementation.md` または `bug.md` の見出しと、`codex/skills/issue-writing/SKILL.md`、`~/.agents/rules/issue-completeness.md` の必須要素に合わせた。`D-01`〜`D-09` は [監査レポート](2026-08-30-config-audit.md) の「対応 Issue 草案 ID」と一致する。

## D-01: Claude Code の最低 version を現行 model 契約に合わせる

### Implementation kind / 実装種別

`implementation`

### Purpose / 目的

`opus` alias が `claude-opus-5` を指すという routing 契約を、許容するすべての Claude Code version で成立させる。

### Exact target / 対象

- `claude/managed-settings.json` の `requiredMinimumVersion`
- `scripts/check-runtime.sh` の Claude Code 最低 version
- 関連する runtime/managed-policy test fixture と documentation

### Remaining problem / 残っている問題

現在の下限は `2.1.218` だが、Claude Opus 5 と既定 `opus` alias は `2.1.219` で追加された。`claude/CLAUDE.md` と `shared/skills/claude-code/model-routing/SKILL.md` は Opus 5 前提の `opus` routing を定義するため、下限 version 上では契約を満たせない。

### Required changes / 必要な変更

- 最低 version を少なくとも `2.1.219` へ引き上げる。新しい hook event を採用する場合は、その導入 version まで引き上げる。
- managed settings と runtime check の値を同一にする。
- 境界値の直前を拒否し、境界値を受け入れる test を追加または更新する。
- 変更理由として Opus 5 の導入 version を一次情報 URL とともに残す。

### Non-goals / 非目標

- agent ごとの model routing の再設計
- `claude/settings.json` の main model 変更
- 最新 version への無条件な自動更新

### Acceptance criteria / 受け入れ条件

- [ ] managed settings と runtime check が同じ最低 version を要求する。
- [ ] その最低 version で `opus` routing の現行 model 契約が成立する。
- [ ] 境界値 test が pass する。
- [ ] `scripts/validate-layout.sh` が pass する。

### Verification commands / 検証コマンド

```bash
scripts/check-runtime.sh
scripts/validate-layout.sh
rg -n '2\.1\.[0-9]+' claude/managed-settings.json scripts/check-runtime.sh tests
```

### Related context / 関連コンテキスト

- Issue #1
- `2026-08-30-config-audit.md` の `A1-01`
- Claude Code CHANGELOG `2.1.219`

## D-02: `claude doctor` の auto-update warning を解消する

### Implementation kind / 実装種別

`bug/fix`

### Purpose / 目的

Claude Code の更新経路を writable かつ再現可能にし、`claude doctor` を warning なしで完了させる。

### Exact target / 対象

- Claude Code の install/update 手順を管理する installer または bootstrap documentation
- 必要なら runtime check の診断メッセージ

### Remaining problem / 残っている問題

Claude Code `2.1.251` 自体は起動するが、`claude doctor` は npm global folder が writable でないため auto-update できないと報告する。将来の security/runtime 更新が自動適用されない可能性がある。

### Reproduction / 再現手順

```bash
claude doctor </dev/null
```

`Can't auto-update: npm global folder isn't writable` が表示される。

### Expected behavior / 期待動作

owner が選択した install 方式で update path が writable であり、`claude doctor` が auto-update warning を出さない。

### Required changes / 必要な変更

- native installer へ移行するか、sudo を要しない npm prefix を明示的に構成する。
- installer/bootstrap の既存構造に合わせて選択した方式を記録する。
- 再実行した `claude doctor` の結果を検証証跡に残す。

### Non-goals / 非目標

- Claude Code の model/routing 変更
- root 権限での global npm install の強制
- Codex CLI の install 経路変更

### Acceptance criteria / 受け入れ条件

- [ ] `claude doctor </dev/null` が auto-update warning なしで終了する。
- [ ] `claude --version` が期待 version を返す。
- [ ] install/update 手順が既存 bootstrap 規約に記録される。

### Verification commands / 検証コマンド

```bash
claude --version
claude doctor </dev/null
scripts/check-runtime.sh
```

### Environment / 環境

- 監査日: 2026-08-30
- Claude Code: `2.1.251`
- shell: Bash / Linux

### Related context / 関連コンテキスト

- Issue #1
- `2026-08-30-config-audit.md` の `A1-02`

## D-03: ConfigChange hook を公式 input schema に限定する

### Implementation kind / 実装種別

`implementation`

### Purpose / 目的

`ConfigChange` hook の判定を公式 field `source`、`file_path`、共通 `cwd` に合わせ、未文書の legacy fallback に依存しないようにする。

### Exact target / 対象

- `claude/hooks/config-change-hook.sh`
- ConfigChange hook の unit/fixture tests

### Remaining problem / 残っている問題

hook は `.tool_input.file_path`、`.path`、`.tool_input.cwd` も受け付け、`~/.claude/settings.local.json` を user scope として扱う。現行公式仕様では `source` と optional `file_path` が event-specific field で、user settings は `~/.claude/settings.json`、project local は project root の `.claude/settings.local.json` である。互換 fallback が malformed input を正常入力に見せる余地がある。

### Required changes / 必要な変更

- official common fields と `source` / `file_path` だけを parse する。
- `source` と `file_path` の対応を検証し、不正型・必須 field 欠落は fail-closed にする。
- user/project/local/policy/skills の fixture と malformed input fixture を更新する。
- block 対象と block 理由は現行 security intent を維持する。

### Non-goals / 非目標

- project 固有 settings の内容監査
- security policy の緩和
- 新しい hook event の追加

### Acceptance criteria / 受け入れ条件

- [ ] hook が公式 field だけで正常 event を判定する。
- [ ] legacy-only field の input を正常入力として受け入れない。
- [ ] user/project/local settings の既存 block/gate behavior が test で維持される。
- [ ] `scripts/validate-layout.sh` が pass する。

### Verification commands / 検証コマンド

```bash
bash -n claude/hooks/config-change-hook.sh
tests/test-managed-policy.sh
tests/test-pre-bash-validate.sh
scripts/validate-layout.sh
```

### Related context / 関連コンテキスト

- Issue #1
- `2026-08-30-config-audit.md` の `A1-03`
- Claude Code hooks reference の `ConfigChange input`

## D-04: accepted exceptions の artifact hash を owner 再確認後に更新する

### Implementation kind / 実装種別

`implementation`

### Purpose / 目的

EX-003 と EX-004 の owner-authored decision が、現在の exact artifact に適用されるかを明確にする。

### Exact target / 対象

- `docs/reports/accepted-exceptions.md` の EX-003 / EX-004
- `claude/managed-settings.json`
- `claude/settings.json`

### Remaining problem / 残っている問題

台帳の SHA-256 と current artifact の実測値が一致しない。hash だけを機械的に更新すると、変更後 artifact への owner 承認を循環的に推論することになる。

### Required changes / 必要な変更

- current artifact と台帳記載時 artifact の diff を owner に提示する。
- owner が policy decision の継続を明示した場合だけ、新しい承認日時・承認文参照・SHA-256 を記録する。
- 継続しない場合は例外を close し、artifact を別 Issue で policy に合わせる。
- validator で active exception の artifact hash mismatch を検出できるか検討する。

### Non-goals / 非目標

- owner 承認なしの hash 差し替え
- bypass/sandbox/memory policy の暗黙変更
- 過去 decision record の削除

### Acceptance criteria / 受け入れ条件

- [ ] EX-003/EX-004 の各 hash が current artifact と一致するか、例外が明示的に close される。
- [ ] active の場合は current artifact に対する owner の明示承認が参照される。
- [ ] 失効条件が維持または明示的に更新される。
- [ ] `scripts/validate-layout.sh` が pass する。

### Verification commands / 検証コマンド

```bash
sha256sum claude/managed-settings.json claude/settings.json
rg -n 'EX-003|EX-004|SHA-256' docs/reports/accepted-exceptions.md
scripts/validate-layout.sh
```

### Related context / 関連コンテキスト

- Issue #1
- `2026-08-30-config-audit.md` の `A4-01`

## D-05: skill-authority に active skill と mode を網羅する

### Implementation kind / 実装種別

`implementation`

### Purpose / 目的

すべての active skill について、repo/state/commit/push/GitHub/delete authority を機械可読な契約として定義する。

### Exact target / 対象

- `docs/contracts/skill-authority.tsv`
- authority contract を検証する script/test
- active `SKILL.md` の mode 宣言

### Remaining problem / 残っている問題

active skill 13 種が authority table に存在せず、`gh-index --force` も実体にだけ存在する。side effect の許可範囲を table から完全には判定できない。

### Required changes / 必要な変更

- 次を mode 単位で追加する: `gh-codex-drive`、`gh-finish`、`gh-roadmap-drive`、`claude-second-opinion`、`doctor`、`issue-writing`、`kaggle`、`branch-cleanup`、`break-consensus`、`model-routing`、`plan-review`、`pr-review`、`python-refactor-analysis`。
- `gh-index --force` の authority を実体に合わせて明示する。
- runtime ごとの wrapper が同名 skill の authority を変えないことを確認する。
- active `SKILL.md` の skill/mode が authority table にない場合を validator で検出する。

### Non-goals / 非目標

- skill の新規追加・削除
- skill workflow の機能変更
- authority の一括緩和

### Acceptance criteria / 受け入れ条件

- [ ] active skill の全 mode が authority table の行に対応する。
- [ ] 各 side effect 列が skill 本文の Required behavior と一致する。
- [ ] 未登録 skill/mode の fixture で validator が fail する。
- [ ] `scripts/validate-layout.sh` が pass する。

### Verification commands / 検証コマンド

```bash
find claude/skills shared/skills codex/skills -name SKILL.md -type f -print | sort
column -t -s $'\t' docs/contracts/skill-authority.tsv
scripts/validate-layout.sh
```

### Related context / 関連コンテキスト

- Issue #1
- `2026-08-30-config-audit.md` の `A4-02`

## D-06: git-workflow consumer 契約と実読込条件を一致させる

### Implementation kind / 実装種別

`implementation`

### Purpose / 目的

`docs/contracts/context-consumers.tsv` の trigger と `git-operations` が実際に rule を読む条件を一致させる。

### Exact target / 対象

- `docs/contracts/context-consumers.tsv` の `git-workflow` / `git-operations` 行
- `shared/skills/git-operations/SKILL.md`
- consumer contract test

### Remaining problem / 残っている問題

contract は `generic git operation` で on-demand load と定義する一方、skill は `mutating Git operation` の前だけ読む。read-only inspection で rule を読むのか、contract trigger を mutation に限定するのかが不一致である。

### Required changes / 必要な変更

- read-only mode に `git-workflow` が必要かを owner policy と rule 内容から決める。
- 必要なら skill の read 条件を generic operation に広げ、不要なら contract trigger を mutating operation に狭める。
- consumer の trigger と実読込表現の一致を test する。

### Non-goals / 非目標

- Git command policy の全面改定
- commit/push authority の変更
- GitHub workflow skill の変更

### Acceptance criteria / 受け入れ条件

- [ ] contract trigger と skill の read 条件が同じ scope を表す。
- [ ] read-only と mutating の両 fixture で期待する load behavior が確認できる。
- [ ] `scripts/validate-layout.sh` が pass する。

### Verification commands / 検証コマンド

```bash
rg -n 'git-workflow|generic git|mutating Git' docs/contracts/context-consumers.tsv shared/skills/git-operations/SKILL.md
scripts/validate-layout.sh
```

### Related context / 関連コンテキスト

- Issue #1
- `2026-08-30-config-audit.md` の `A4-03`

## D-07: inventory の branch-cleanup after_path を正本に合わせる

### Implementation kind / 実装種別

`implementation`

### Purpose / 目的

inventory が `branch-cleanup` の current canonical source を正確に示すようにする。

### Exact target / 対象

- `docs/reports/inventory-elements.tsv` の `claude-skill:branch-cleanup` 行
- manifest/install mapping の整合 test

### Remaining problem / 残っている問題

inventory は after_path を `claude/skills/branch-cleanup/SKILL.md` と記録するが、current source は `shared/skills/branch-cleanup/SKILL.md` であり、manifest が runtime 先へ install する。source と installed path が混同されている。

### Required changes / 必要な変更

- after_path を canonical source path に修正する。
- installed runtime path が必要なら別 evidence または列の意味に沿う場所へ記録する。
- manifest mapping と inventory after_path の semantic check を追加する。

### Non-goals / 非目標

- `branch-cleanup` skill 本文の変更
- install destination の変更
- inventory 全体の schema 再設計

### Acceptance criteria / 受け入れ条件

- [ ] inventory の after_path が current canonical source と一致する。
- [ ] manifest が intended runtime destinations を引き続き示す。
- [ ] `scripts/validate-layout.sh` が pass する。

### Verification commands / 検証コマンド

```bash
rg -n 'branch-cleanup' docs/reports/inventory-elements.tsv install/manifest.tsv
test -f shared/skills/branch-cleanup/SKILL.md
scripts/validate-layout.sh
```

### Related context / 関連コンテキスト

- Issue #1
- `2026-08-30-config-audit.md` の `A4-04`

## D-08: skill 数の期待値と metrics report を実測へ同期する

### Implementation kind / 実装種別

`implementation`

### Purpose / 目的

skill 追加後も metrics test と modernization report の machine-readable block が current tree の実測値に一致する状態を保つ。

### Exact target / 対象

- `tests/test-measure-metrics.sh` の実 repository 向け期待値
- `docs/plans/2026-07-23-agents-toolkit-modernization.md` の `metrics:after` block
- skill 追加時の metrics 更新手順または生成経路

### Remaining problem / 残っている問題

`tests/test-measure-metrics.sh` は `claude_skills=18` を期待するが、`scripts/measure-metrics.sh` の current 実測は 21 である。modernization report の `metrics:after` block も `claude_skills: 18`、`active_skill_entrypoints: 31`、`active_skill_entrypoint_bytes: 72766` のままで、実測 21 / 34 / 80740 と乖離し、`tests/test-report-consistency.sh` が FAIL する。

clean な `master` (`60204e4`) で全 tests を実行しても、この 2 件だけが変更前から FAIL し、他 15 件は PASS した。commit `2749265` で `gh-codex-drive` / `gh-finish`、commit `eee8652` で `gh-roadmap-drive` が追加された際に、test 期待値と report block が更新されていない。

### Required changes / 必要な変更

- `claude_skills` の test 期待値を current 実測 21 に同期する。
- `metrics:after` block の全 key を `scripts/measure-metrics.sh` の current 出力へ同期する。
- skill 追加時に test 期待値と report block の両方を更新する手順を定義するか、実測から生成する方式を検討する。
- stale 値と欠落 key を検出する既存 fail-closed behavior を維持する。

### Non-goals / 非目標

- skill の追加・削除・内容変更
- metrics の定義変更
- stale 値を許容するための test 緩和

### Acceptance criteria / 受け入れ条件

- [ ] `claude_skills` の test 期待値が current 実測と一致する。
- [ ] `metrics:after` block が全 measured key で current 実測と一致する。
- [ ] skill 追加時の同期手順または生成経路が明確になる。
- [ ] 対象 2 tests が pass する。

### Verification commands / 検証コマンド

```bash
tests/test-measure-metrics.sh
tests/test-report-consistency.sh
scripts/measure-metrics.sh
```

### Related context / 関連コンテキスト

- Issue #1
- `2026-08-30-config-audit.md` の `A4-05`
- commits `2749265`、`eee8652`

## D-09: 本体 harness prompt と重複・矛盾する常時注入条文を短縮する

### Implementation kind / 実装種別

`implementation`

### Purpose / 目的

本体 harness prompt と重複する常時注入条文を、本体にない owner policy と理由説明を保持したまま短縮する。hook で強制済みの `CLAUDE.md:40` は禁止事項の再説明を減らす。

### Exact target / 対象

- `shared/rules/core-contract.md` の `core-contract:5`、`core-contract:8`
- `claude/CLAUDE.md:39-40`
- `shared/rules/git-workflow.md:4-5`
- 同期済み core-contract block と metrics 証跡

### Remaining problem / 残っている問題

`core-contract:5`、`core-contract:8`、`CLAUDE.md:39`、`shared/rules/git-workflow.md:4-5` は本体 harness prompt と重複し、常時または on-demand context を増やしている。`CLAUDE.md:40` は plugin 由来 agent 説明と矛盾するが、`pre-bash-validate-hook.sh` が禁止を強制済みであり、長い条文は理由説明としてのみ必要である。

### Required changes / 必要な変更

- 重複条文を、本体にない owner policy と repository 固有条件だけが残る short form にする。
- `CLAUDE.md:40` は hook 強制を前提に、禁止理由と正しい起動経路だけを短く説明する。
- short 化の before/after を `scripts/measure-metrics.sh` の `claude_always_on_total` / `combined_always_on_total` で記録する。
- core-contract は shared 正本を編集し、`shared/bin/sync-shared-rules.sh` で Claude/Codex の同期 block へ反映する。
- 意味と enforcement が維持されることを既存 hook test と同期 check で確認する。

### Non-goals / 非目標

- 本体に対応節がない条文（`core-contract:9` 等）の削除
- 意味の変更
- hook enforcement の削除または緩和

### Acceptance criteria / 受け入れ条件

- [ ] 対象条文が本体との重複を減らし、owner policy 固有の意味を保持する。
- [ ] `CLAUDE.md:40` の禁止が既存 hook で引き続き強制される。
- [ ] core-contract の全同期 block が shared 正本と一致する。
- [ ] `claude_always_on_total` と `combined_always_on_total` の before/after が記録される。
- [ ] `scripts/validate-layout.sh` が pass する。

### Verification commands / 検証コマンド

```bash
scripts/measure-metrics.sh
shared/bin/sync-shared-rules.sh --check
tests/test-pre-bash-validate.sh
scripts/validate-layout.sh
```

### Related context / 関連コンテキスト

- Issue #1
- `2026-08-30-config-audit.md` の `A2-01`、`A2-02`
- `2026-08-30-system-prompt-overlap.md`

## 草案化しない観測

- Codex 公式 hooks 仕様には現在 `PostToolUse` と `UserPromptSubmit` が存在するが、Issue #1 の Non-goal「Codex 側 PostToolUse 相当」に従い、本監査では実装草案を作らない。
- 個別 project settings の監査は対象外である。
- RUN 1〜4 の無出力/timeout は Codex 実行環境の非 PTY exec wrapper 起因と推定するが確定しておらず、repo 修正としては草案化しない。
- `SchemaStore` が Claude Code `2.1.251` の `PreModelSwitch` / `PostModelSwitch` に追随していない点は upstream 観測であり、repo 修正草案にはしない。
