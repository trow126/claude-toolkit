# ロードマップ #13 の metrics before/after

tracking Issue #13「#1 監査の修正 Issue（#2〜#12）を依存順に実装する」の close 条件として、[baseline-2026-08-30.txt](baseline-2026-08-30.txt)（commit 60204e4）と完了時点の `master`（commit 12b3ce5）の `scripts/measure-metrics.sh` 出力を比較した。子 Issue 11 件（#11 → #10 → #9 → #8 → #4 → #6 → #12 → #2 → #3 → #7 → #5）はすべて close 済み。

## 実行条件

- 実行日: 2026-08-31（Asia/Tokyo）
- 実行コマンド: `scripts/measure-metrics.sh --repo .` / `python3 scripts/measure-hook-injection.py .`
- 実行環境: Linux (WSL2)、Claude Code 2.1.251（native installer）、python3
- 比較範囲: `60204e4..12b3ce5`（25 commits。うち #1 の監査記録 2 commits、子 Issue の実装 23 commits）

## 変化した key（15 / 56）

| key | before (60204e4) | after (12b3ce5) | 変化 | 由来 |
|---|---:|---:|---:|---|
| `claude_md_bytes` | 3119 | 3144 | +25 | #12: `CLAUDE.md:39` に bypassPermissions 条件を明示 |
| `claude_imported_shared_bytes` | 1407 (1 files) | 1269 (1 files) | −138 | #12: `core-contract:5,8` の短縮 |
| `claude_always_on_total` | 4526 | 4413 | −113 | #12 |
| `codex_agents_md_bytes` | 3564 | 3426 | −138 | #12: 同期 block の短縮 |
| `combined_always_on_total` | 8090 | 7839 | −251 | #12 |
| `active_skill_entrypoint_bytes` | 80740 | 80819 | +79 | #9: `git-operations` の read 条件を明示 |
| `shared_rules_always_on_bytes` | 1407 | 1269 | −138 | #12 |
| `shared_rules_on_demand_bytes` | 10544 | 10445 | −99 | #12: `git-workflow:4-5` −137、#2: `markdown-rules` に hook 参照 +38 |
| `hook_scripts` | 7 | 9 | +2 | #2: `post-edit-lint-hook.sh`、#3: `prompt-submit-hook.sh` |
| `hook_registrations` | 9 | 11 | +2 | #2: PostToolUse `Edit\|Write`、#3: UserPromptSubmit |
| `inventory_audited_elements` | 157 | 164 | +7 | #9 / #6 の test 各 +1、#2 の hook・helper・test +3、#3 の hook・test +2 |
| `user_prompt_submit_injection_typical_bytes` | — | 198 | 新規 | #3: 毎 prompt の注入 bytes（末尾改行込み） |
| `user_prompt_submit_injection_max_bytes` | — | 256 | 新規 | #3: hook 内 `MAX_INJECTION_BYTES` |
| `claude_session_start_injection_typical_bytes` | 4628 | 4515 | −113 | #12（常時 context の短縮分） |
| `claude_session_start_injection_max_bytes` | 5038 | 4925 | −113 | #12 |

常時注入は Claude 側 −113 bytes（−2.5%）、Claude + Codex 合計 −251 bytes（−3.1%）。新設した UserPromptSubmit 層は 1 prompt あたり 198 bytes（上限 256）で、常時 context には含まれない。

## 変化しなかった key（41 / 56）

security・policy 系の key は baseline と同一である。

| key | 値 | 意味 |
|---|---|---|
| `bypass_permissions_default` / `dangerous_mode_prompt_skipped` | yes / yes | EX-003 の owner policy を維持（#7 で再承認） |
| `sandbox_enabled` | no | 同上 |
| `auto_memory_enabled` | no | EX-004 の owner policy を維持（#7 で再承認） |
| `managed_policy_present` / `managed_*_lock_ok` / `auto_mode_lockout_ok` | yes | managed policy の lock を維持（#4 で `requiredMinimumVersion` 2.1.219 に更新） |
| `claude_skills` / `codex_skills` | 21 / 21 | skill の追加・削除なし（#11 は test 期待値と report を実測へ同期） |
| `full_model_pins` / `unconditional_delegation_gh_start` / `always_on_learnings_paths` | 0 / 0 / 0 | 既存の contract を維持 |
| `session_start_system_message_*` / `post_compact_system_message_*` | 102 / 512、128 / 512 | SessionStart / PostCompact の bounded 出力は不変 |

hook 単体の注入計測（`measure-hook-injection.py`）も、SessionStart 102 bytes・PostCompact 128 bytes・上限 512 bytes は baseline と同一で、UserPromptSubmit の 198 / 256 bytes だけが加わった。

## master の検証結果（12b3ce5）

| check | 結果 |
|---|---|
| `scripts/validate-layout.sh` | `PASS: no layout violations found` |
| `tests/test-*.sh`（21 scripts） | 21 / 21 PASS |
| `scripts/package-release.sh --check` | PASS（469 entries） |
| `shared/bin/sync-shared-rules.sh --check` | OK |
| `scripts/check-runtime.sh` | OK（Claude Code 2.1.251 ≥ 2.1.219、native launcher） |
| `scripts/install-managed-policy.sh --check` | OK（managed policy と source が一致） |

## 子 Issue と commit

| Issue | commit | 概要 |
|---|---|---|
| #11 | b307e36, eff9947 | skill 数期待値と `metrics:after` を実測同期、README に同期手順 |
| #10 | 99a9836, 3dc4b33 | inventory の after_path 修正、validator に manifest source 検査 |
| #9 | db2ab81, a5795ed | git-workflow trigger を mutating に限定、contract test 追加 |
| #8 | c5b6e61, 65ddfca | skill-authority を active 全 skill / mode に拡張、双方向 validator |
| #4 | 9690e8e | 最低 version 2.1.219（Opus 5） |
| #6 | 6681f0e, c2363c4 | ConfigChange hook を official field 限定・fail-closed |
| #12 | 1866915, 460d280 | 常時注入条文の短縮と before/after 記録 |
| #2 | ff2c1b0, 674fb7d, eca50f2 | PostToolUse Edit/Write lint hook |
| #3 | e917cb2, 18a4654, 50a712b | UserPromptSubmit 注入層 |
| #7 | 895d2cb, 5bfa27f | EX-003/EX-004 の再承認と hash 拘束 validator |
| #5 | 6384b59, 12b3ce5 | native installer への移行記録と経路診断 |
