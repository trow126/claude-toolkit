---
name: gh:review
description: CodeRabbitレビュー指摘をIssue・計画との整合性を確認しながら処理。採用/却下を判断し、修正・テスト・再プッシュまで一貫実行。
---

# /gh:review - CodeRabbitレビュー対応コマンド

> **核心**: レビュー指摘を盲目的に修正せず、Issue要件・プロジェクト方針との整合性を確認してから対応

## Triggers
- CodeRabbitがPRにレビューコメントを投稿した後
- レビュー指摘への対応が必要な時
- PR修正サイクルの実行

## Usage

```bash
# PR番号を指定してレビュー対応開始
/gh:review 17

# 特定の指摘のみ処理
/gh:review 17 --comments 1,3,5

# 自動採用モード（Trivial指摘のみ自動修正）
/gh:review 17 --auto-trivial

# ドライラン（修正内容を確認のみ）
/gh:review 17 --dry-run
```

## Behavioral Flow

### Phase 0: Context Loading

```yaml
1. PR情報取得:
   gh pr view <number> --json headRefName,body,title
   → PRブランチ名、関連Issue番号を抽出

2. 関連Issue取得（"Closes #N" から）:
   gh issue view <N> --json body,title
   → Issue要件を取得

3. プロジェクト方針読み込み:
   - CLAUDE.md（コーディング規約）
   - docs/PLAN.md（アーキテクチャ方針）
   - .coderabbit.yaml（レビュー設定）

4. 🆕 技術的負債状況確認:
   claudedocs/technical_debt.md を読み込み
   → 未対応件数を表示:
   ┌──────────────────────────────────────┐
   │ ⚠️ 技術的負債: 12件の未対応指摘あり  │
   │   - Critical: 2件                   │
   │   - High: 5件                       │
   │   - Medium: 5件                     │
   └──────────────────────────────────────┘

5. ローカルブランチ準備:
   git fetch origin <branch>
   git checkout <branch>
   # または worktree の場合は cd
```

### Phase 1: Review Comments Fetch

```yaml
5. レビューコメント取得:
   gh api repos/{owner}/{repo}/pulls/{number}/comments

6. コメント分類:
   - Potential issue (🟡 Minor, 🔴 Major)
   - Nitpick (🔵 Trivial)
   - Question
   - Suggestion

7. 各コメントを構造化:
   {
     id: "comment_id",
     path: "src/data/realtime.py",
     line: 276,
     severity: "minor",  # trivial, minor, major, critical
     category: "bug",    # bug, style, performance, security
     body: "asyncio.create_task の参照を保持...",
     suggested_fix: "diff code block if present"
   }
```

### Phase 2: Alignment Analysis（各指摘に対して）

```yaml
8. 🔴 整合性分析（必須・各指摘に対して実行）:

   a. Issue要件との整合性:
      - 指摘が Issue の要件範囲内か
      - 修正が Issue の成果物に影響するか
      - スコープ外の変更を要求していないか

   b. プロジェクト方針との整合性:
      - CLAUDE.md のコーディング規約に沿うか
      - アーキテクチャ方針と矛盾しないか
      - 既存パターンと一貫性があるか

   c. 技術的妥当性:
      - 指摘内容が技術的に正しいか
      - 副作用やリグレッションのリスク
      - 修正コストと効果のバランス

9. 推奨アクション決定:

   採用 (accept):
     - バグ修正（技術的に正しい指摘）
     - セキュリティ問題
     - 明確なパフォーマンス改善
     - プロジェクト規約違反の修正

   検討 (discuss):
     - 大規模リファクタリング提案
     - トレードオフのある変更
     - Issue スコープ境界の変更

   却下 (reject):
     - Issue スコープ外
     - プロジェクト方針と矛盾
     - 過度な最適化要求
     - 誤った指摘（false positive）
```

### Phase 3: User Decision（一括確認）

```yaml
10. 全指摘を一覧表示:

    ┌─────────────────────────────────────────────────────────────┐
    │ 📋 CodeRabbit 指摘一覧 (6件)                                │
    ├─────┬───────────────────────┬────────┬────────┬─────────────┤
    │ #   │ ファイル:行           │ 重要度 │ 整合性 │ 推奨        │
    ├─────┼───────────────────────┼────────┼────────┼─────────────┤
    │ 1   │ realtime.py:276       │ 🟡 Minor│ ✅     │ 採用        │
    │ 2   │ realtime.py:392       │ 🟡 Minor│ ✅     │ 採用        │
    │ 3   │ stream_data.py:118    │ 🔵 Triv │ ✅     │ スキップ    │
    │ 4   │ auth.py:45            │ 🟡 Minor│ ⚠️ 外  │ 却下        │
    │ 5   │ util.py:120           │ 🔵 Triv │ ✅     │ スキップ    │
    │ 6   │ stream_data.py:317    │ 🟡 Minor│ ✅     │ 採用        │
    └─────┴───────────────────────┴────────┴────────┴─────────────┘

    各指摘の詳細（折りたたみ表示）:
    
    <details>
    <summary>#1 realtime.py:276 - asyncio.create_task 参照保持</summary>
    
    💬 指摘内容: asyncio.create_task の参照を保持する必要あり
    📋 Issue整合性: ✅ 接続安定性要件に直接関連
    📐 方針整合性: ✅ CLAUDE.md のエラーハンドリング方針
    📝 修正案: `self._task = asyncio.create_task(...)`
    </details>
    
    （以下同様に全件表示）

11. AskUserQuestion（1回のみ・一括確認）:

    "上記の推奨アクションで進めますか？"
    
    選択肢:
      - 推奨通り実行（採用3件、スキップ2件、却下1件）
      - 個別に調整する → 詳細確認モードへ（後述）
      - 全て採用
      - 全てスキップ

12. 「個別に調整する」選択時のみ詳細確認:

    AskUserQuestion（multiSelect: true）:
    "変更したい指摘を選択してください"
    
    選択肢:
      - #1 realtime.py:276 [現在: 採用] → 却下に変更
      - #3 stream_data.py:118 [現在: スキップ] → 採用に変更
      - #4 auth.py:45 [現在: 却下] → 採用に変更
      - #5 util.py:120 [現在: スキップ] → 採用に変更
    
    ※ 却下に変更した指摘は理由入力を求める

13. 却下指摘への CodeRabbit 返信（まとめて実行）:

    却下が確定した指摘に対して一括返信:
    
    gh pr comment <number> --body "
    @coderabbitai

    以下の指摘について対応を見送ります:

    **realtime.py:276** - [理由]
    **auth.py:45** - Issue #8 スコープ外のため

    フォローアップは Issue #XX で対応予定です。
    "
```

### Phase 3.5: Technical Debt Tracking（🆕 必須）

```yaml
12. 却下/スキップした指摘を記録（🔴 CRITICAL - 取りこぼし防止）:

    記録対象:
      - 却下した指摘（reject）
      - スキップした指摘（skip）
      - 「スコープ外」として見送った指摘

    claudedocs/technical_debt.md に追記:
    ```markdown
    ## PR #17 (2026-01-27)
    
    ### 却下
    | ファイル | 行 | 重要度 | 指摘内容 | 却下理由 |
    |----------|-----|--------|----------|----------|
    | src/auth.py | 45 | 🟡 Minor | 入力バリデーション追加 | Issue #8 スコープ外 |
    
    ### スキップ（後で対応）
    | ファイル | 行 | 重要度 | 指摘内容 |
    |----------|-----|--------|----------|
    | src/util.py | 120 | 🔵 Trivial | docstring追加 |
    ```

13. 🔴 「スコープ外」却下時の追加確認:

    技術的に正しい指摘を「スコープ外」で却下する場合:

    AskUserQuestion:
      "⚠️ 技術的に正しい指摘をスコープ外で却下します。
       
       指摘: src/auth.py:45 - 入力バリデーション追加
       
       フォローアップ対応:
       1. 新規Issueを作成する（推奨）
       2. technical_debt.md に記録のみ
       3. 対応不要（本当に不要な場合のみ）"

    新規Issue作成時:
      gh issue create --title "Tech debt: [指摘内容]" \
        --body "元PR: #17\n元指摘: [内容]\n理由: スコープ外\n\n対応方針: TBD"

14. 負債サマリー表示:
    ┌──────────────────────────────────────────┐
    │ 📊 技術的負債更新                        │
    │                                          │
    │ 今回追加: 3件                            │
    │   - 却下: 1件（→ Issue #45 作成済み）   │
    │   - スキップ: 2件                        │
    │                                          │
    │ 累計未対応: 15件（+3）                   │
    │   ⚠️ 20件超過で警告レベル上昇           │
    └──────────────────────────────────────────┘
```

### Phase 4: Apply Fixes

```yaml
12. 採用した指摘を適用:

    for comment in accepted_comments:
      if comment.suggested_fix:
        # 提案された diff を適用
        apply_suggested_fix(comment)
      else:
        # 手動で修正実装
        implement_fix(comment)

      # 修正後にファイル内容を確認
      verify_fix(comment.path)

13. 修正サマリー表示:
    ✅ Applied 4/6 fixes:
    - src/data/realtime.py:276 - asyncio.create_task 参照保持
    - src/data/realtime.py:392 - 同上
    - src/data/realtime.py:399 - 同上
    - scripts/stream_data.py:317 - signal_handler タスク参照

    ⏭️ Skipped 2/6:
    - scripts/stream_data.py:118 - asyncio.Event (Trivial)
    - scripts/stream_data.py:213 - 冗長チェック (Trivial)
```

### Phase 5: Verification

```yaml
14. Lint チェック:
    uv run ruff check src/ scripts/

    エラー時:
    - 自動修正可能 → uv run ruff check --fix
    - 手動修正必要 → 該当箇所を表示

15. フォーマットチェック:
    uv run ruff format --check src/ scripts/

    差分あり → uv run ruff format src/ scripts/

16. テスト実行:
    uv run pytest tests/ -v

    失敗時:
    - 失敗テストを表示
    - 修正箇所との関連を分析
    - 追加修正が必要か判断

17. 検証結果サマリー:
    ✅ Lint: passed
    ✅ Format: passed
    ✅ Tests: 56 passed in 1.2s
```

### Phase 6: Commit & Push

```yaml
18. 確認付きコミット:

    AskUserQuestion:
      "📋 コミット・プッシュを実行しますか？

       修正ファイル: 3 files
       テスト: ✅ All passed

       コミットメッセージ:
       fix(data): Address CodeRabbit review comments

       - Hold asyncio.create_task references to prevent GC
       - Fix signal handler task reference

       1. 実行する（推奨）
       2. メッセージ編集
       3. スキップ"

19. コミット実行:
    git add <modified_files>
    git commit -m "<message>"

20. プッシュ:
    git push origin <branch>

21. 完了メッセージ:
    ✅ Changes pushed to origin/issue-8

    CodeRabbit が自動で再レビューを開始します。
    確認: https://github.com/owner/repo/pull/17

    次のステップ:
    - 再レビュー結果を待つ
    - 追加指摘があれば /gh:review 17 を再実行
    - レビュー通過後 gh pr merge 17
```

## Options

```bash
--dry-run           # 修正内容を表示のみ（実行しない）
--auto-trivial      # Trivial指摘は自動採用
--auto-all          # 全指摘を自動採用（確認なし・危険）
--comments <1,2,3>  # 特定のコメントのみ処理
--skip-tests        # テスト実行をスキップ（非推奨）
--no-push           # コミットまでで停止（pushしない）
--no-debt-tracking  # 技術的負債記録をスキップ（非推奨）
```

## Error Handling

```bash
# PRが見つからない
→ エラー「PR #N が見つかりません」

# レビューコメントがない
→ 「レビューコメントがありません。CodeRabbitのレビュー完了を待ってください」

# ブランチがローカルにない
→ git fetch && git checkout で自動取得

# テスト失敗
→ 失敗テストを表示、修正を促す
→ --skip-tests で続行可能（非推奨）

# 修正適用失敗
→ 手動修正を促す、該当ファイルを開く
```

## Integration Points

```yaml
CodeRabbit API:
  - gh api pulls/{n}/comments: レビューコメント取得
  - gh pr comment: 却下理由の返信

Issue連携:
  - PR body から "Closes #N" を抽出
  - Issue 要件との整合性確認

プロジェクト文脈:
  - CLAUDE.md: コーディング規約
  - docs/PLAN.md: アーキテクチャ方針
  - .coderabbit.yaml: レビュー設定

検証ツール:
  - ruff check/format: Lint・フォーマット
  - pytest: テスト実行
```

## 実行指示

**あなたは今、`/gh:review` コマンドを実行しています。**

### 🚨 CRITICAL: 見逃し防止ルール

```yaml
絶対禁止事項:
  - ❌ 「対応済み」マークを見て自動スキップ
  - ❌ 「推奨」「Trivial」を確認なしでスキップ
  - ❌ Phase 3 の AskUserQuestion を省略
  - ❌ コメント件数を確認せず完了宣言

必須確認事項:
  - ✅ 取得した全コメントを一覧表形式でユーザーに提示
  - ✅ 推奨アクションを提示し、AskUserQuestion で一括確認
  - ✅ 「対応済み」でもユーザーに報告
  - ✅ 完了前に対応サマリーを表示（採用/却下/スキップ件数）
```

### 必須実行フロー

```yaml
1. Phase 0: Context Loading
   - PR情報取得（ブランチ名、関連Issue）
   - Issue要件取得
   - CLAUDE.md / docs/PLAN.md 読み込み
   - 🆕 claudedocs/technical_debt.md 読み込み → 未対応件数表示
   - ローカルブランチ準備

2. Phase 1: Review Comments Fetch（🔴 全件取得必須）
   - gh api でコメント取得
   - severity/category で分類
   - 🚨 コメント総数を記録: "N件のコメントを取得"

3. Phase 2: Alignment Analysis（🔴 必須）
   - 各指摘に対して整合性分析
   - Issue要件との照合
   - プロジェクト方針との照合
   - 推奨アクション決定

4. Phase 3: User Decision（🔴 必須・一括確認）
   - 🚨 全コメントを一覧表形式で表示
   - 🚨 AskUserQuestion 1回で一括確認（推奨通り/個別調整/全採用/全スキップ）
   - 「個別に調整」選択時のみ詳細確認モードへ
   - 却下確定後に CodeRabbit へ一括返信

5. Phase 3.5: Technical Debt Tracking（🔴 必須・取りこぼし防止）
   - 却下/スキップした指摘を claudedocs/technical_debt.md に記録
   - 🚨 「スコープ外」却下時はフォローアップIssue作成を確認
   - 負債サマリー表示（累計件数）

6. Phase 4: Apply Fixes
   - 採用した指摘を修正
   - 修正サマリー表示

7. Phase 5: Verification（🔴 必須）
   - ruff check
   - ruff format
   - pytest

8. Phase 6: Commit & Push
   - 確認付きコミット
   - プッシュ
   - 🚨 最終チェックリスト確認:
     ```
     ✅ 全 N 件のコメントを確認済み
     ✅ 対応: X件 / スキップ: Y件 / 却下: Z件
     ✅ 技術的負債記録: Y+Z件を追記
     ```
   - 再レビュー待ち案内
```

### 指摘分析のポイント

```yaml
採用すべき指摘:
  - バグ（GC、メモリリーク、競合状態）
  - セキュリティ（入力検証、認証）
  - 明確なパフォーマンス問題
  - 規約違反（型ヒント欠落、docstring不足）

検討が必要な指摘:
  - アーキテクチャ変更を伴う提案
  - 大規模リファクタリング
  - Issue スコープ境界

却下候補の指摘:
  - Issue スコープ外の機能追加
  - 過度な最適化（premature optimization）
  - プロジェクト方針と矛盾する変更
  - 誤検知（false positive）
```

## Related Commands

```bash
/gh:start 42        # Issue作業開始
/gh:review 17       # レビュー対応（このコマンド）
/gh:issue close 42  # Issue完了・振り返り
```

## Tips

💡 **Trivial も記録**: 後回しにする場合は必ず technical_debt.md に記録
💡 **却下は理由を明記**: CodeRabbit への返信で次回レビュー改善
💡 **テスト必須**: 修正後は必ずテスト実行
💡 **再レビュー自動**: push すれば CodeRabbit が自動で再確認

---

**Last Updated**: 2026-01-27
**Version**: 1.2.0
**Changelog**: 
- v1.2.0 - Added Phase 3.5 Technical Debt Tracking to prevent long-term oversight
- v1.1.0 - Added CRITICAL section to prevent comment oversight (Phase 3 enforcement)
