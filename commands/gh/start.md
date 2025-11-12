---
name: gh:start
description: TodoWriteタスクを選択して実装開始。GitHub Issue自動同期でセッション間の作業継続性を保証。
category: workflow
complexity: standard
mcp-servers: [sequential, context7, magic, playwright, morphllm, serena]
personas: [architect, frontend, backend, security, qa-specialist]
---

# /gh:start - TodoWriteタスク実装開始

> **セッション継続性重視**: GitHub Issueを永続化層として、複数セッション・複数デバイス間での作業継続を保証。TodoWriteはセッション内作業キューとして機能。

## 核心思想：GitHub as Single Source of Truth

```
┌────────────────────────────────────────┐
│  GitHub Issue (永続化層)                │
│  - 全体進捗の唯一の真実                 │
│  - タスク完了状態 ([ ] / [x])          │
│  - 進捗コメント履歴                     │
│  - セッション間で永続化                 │
└──────────┬─────────────────────────────┘
           │
           ↓ 同期
┌──────────────────────────────────────┐
│  TodoWrite (セッション内キュー)        │
│  - 現在のセッションの作業管理          │
│  - 未完了タスクのみ含む                │
│  - セッション終了で破棄OK              │
└──────────────────────────────────────┘
```

## サブエージェント委譲アーキテクチャ

```
/gh:start (メインエージェント)
    ↓
┌─────────────────────────────────────────┐
│ Phase 3: Task実装                        │
│ Task tool → 実装エージェント             │
│   - コード生成・編集                     │
│   - テスト実行                           │
│   - ビルド検証                           │
└───────────────┬─────────────────────────┘
                ↓ 完了
┌─────────────────────────────────────────┐
│ Phase 4: GitHub同期                      │
│ Task tool → 同期エージェント             │
│   - progress-tracker skill起動          │
│   - GitHub Issue更新                     │
│   - コメント投稿                         │
│   - チェックボックス更新                 │
│   - 自動クローズ（全タスク完了時）       │
└───────────────┬─────────────────────────┘
                ↓ 同期完了
┌─────────────────────────────────────────┐
│ Phase 5: 次タスク提案                    │
│   - 未完了タスク確認                     │
│   - 次タスク提示                         │
└─────────────────────────────────────────┘

メリット:
✅ 確実な即座同期（TodoWriteイベント制約を回避）
✅ 独立したGitHub API操作（エラー隔離）
✅ メインエージェントのブロッキング回避
✅ progress-tracker skillの確実な起動
```

## Triggers
- TodoWriteタスク作成後の実装開始
- GitHub Issue workフロー後の実装作業
- セッション中断後の作業再開
- 複数タスクの並列実装

## Usage
```bash
# 次のタスクを自動選択して開始
/gh:start

# 特定のタスク番号を指定
/gh:start 2

# 複数タスクを並列実行
/gh:start 1,2,3 --parallel

# Issue自動検出（推奨）
/gh:start
→ セッションコンテキストからIssueマッピング検出
→ GitHubから最新状態を自動同期

# フレームワーク指定
/gh:start --framework react

# テスト付き実装
/gh:start --with-tests
```

## Behavioral Flow

### Phase 0: Context Sync（コンテキスト同期）**最重要**

```yaml
目的: セッション再開時に最新状態を復元

1. セッションコンテキストを確認:
   - Issue-TodoWriteマッピングが存在するか？
   - 存在する → Issue連携あり（自動同期モード）
   - 存在しない → Issue連携なし（TodoWriteのみモード）

2. Issue連携がある場合の自動同期:
   a. GitHubから最新Issueデータを取得
      gh issue view <number> --json body,comments

   b. コメントから進捗を解析
      - "✅ Task 1/5: API実装 (20%)" → Task 1完了を認識
      - 最新の進捗率を確認

   c. Issue本文のタスク状態を確認
      - [ ] 未完了タスク
      - [x] 完了済みタスク

   d. 現在のTodoWriteと比較
      - GitHubで完了済み → TodoWriteから削除
      - GitHubで未完了 → TodoWriteに存在確認
      - 不一致があれば同期

   e. TodoWriteを再構築（必要に応じて）
      - 完了済みタスクを削除
      - 新しい未完了タスクを追加
      - セッションコンテキストを更新

3. 同期結果を表示:
   GitHub進捗: 2/5タスク (40%)
   TodoWrite: 3タスク（未完了のみ）

   セッション状態: 同期完了 ✅

3b. Phase情報を表示（Phase-by-Phase モード時）🆕:
   マッピングに `phase_mode: true` が設定されている場合:

   📊 Phase Progress: Phase 2/4 - Frontend
   Current Phase: 3タスク（残り2タスク）

   Phase Summary:
   ✅ Phase 1: Backend - 3/3 タスク
   🔄 Phase 2: Frontend - 1/3 タスク
   ⏳ Phase 3: Testing - 0/5 タスク
   ⏳ Phase 4: Deployment - 0/2 タスク

   Next Phase: Phase 3 - Testing (5タスク)
```

### Phase 1: Task Selection（タスク選択）

```yaml
4. 利用可能なタスクを確認:
   - pending または in_progress タスクのみ
   - 完了済み（completed）は除外

5. タスクを選択:
   - 引数なし → 最初のpendingタスク
   - 番号指定 → 指定タスク
   - --parallel → 複数タスク

6. タスクをin_progressに変更:
   TodoWrite({"status": "in_progress"})
```

### Phase 2: Context Analysis（コンテキスト分析）

```yaml
7. タスク内容を解析:
   - フレームワーク検出（React, Vue, Express等）
   - ドメイン分類（frontend, backend, fullstack）
   - 複雑度評価（simple, standard, complex）

8. ペルソナを自動選択:
   frontend: Frontend + Architect
   backend: Backend + Security
   fullstack: Architect + Frontend + Backend + Security

9. MCPサーバーを決定:
   UI系 → Magic MCP
   Framework → Context7 MCP
   Testing → Playwright MCP
   Analysis → Sequential MCP
   Codebase → Serena MCP
```

### Phase 3: Implementation（実装）

```yaml
10. Task tool → general-purpose agent（実装エージェント）に委譲:
    prompt: "Issue #42のTask 1を実装してください"
    context:
      - Issue番号
      - タスク詳細
      - 選択されたペルソナ
      - 必要なMCPサーバー

11. 実装エージェント内で実装実行:
    - ペルソナ起動
    - MCPサーバー起動
    - コード生成・編集
    - テスト実行（--with-testsフラグ時）

12. 実装完了を検証:
    - ビルド成功確認
    - テスト通過確認
    - 実装エージェント終了
```

### Phase 4: Immediate Sync（即座同期）**最重要**

```yaml
13. TodoWriteをcompletedに変更:
    TodoWrite({"status": "completed"})

14. GitHub Issue即座同期（Issue連携時）:
    ⚠️ CRITICAL: Task tool経由でサブエージェントに委譲

    Task tool起動:
      subagent_type: "general-purpose"
      description: "Sync Issue progress after task completion"
      prompt: |
        Issue #<number>のTask <N>が完了しました。
        以下を実行してください:

        1. progress-tracker skillを起動
        2. 完了タスクをカウント
        3. GitHubにコメント投稿:
           gh issue comment <number> --body "✅ Task <N>/<total>: <task_name> (<percentage>%)"
        4. Issue本文のチェックボックス更新:
           gh issue edit <number> --body "$(更新されたタスクリスト)"
        5. セッションコンテキストを更新
        6. 全タスク完了時は自動クローズ（--no-auto-closeフラグがない場合）

    委譲理由:
      - TodoWriteイベント検知の制約を回避
      - 確実な即座同期を保証
      - GitHub API操作の独立実行
      - メインエージェントのブロッキング回避

15. サブエージェント完了待機:
    - 同期完了確認
    - GitHub更新結果を受信
    - エラーハンドリング

16. 全タスク完了チェック:
    - 全タスクが完了？
      → Yes: Issue自動クローズ（サブエージェントで実行済み）
      → No: 次のタスクを提案

理由: セッション中断しても進捗はGitHubに永続化済み
```

### Phase 5: Next Task（次タスク提案）

```yaml
16. 次の未完了タスクを提案:
    次のタスク: #2 "Frontend component"

    実行: /gh:start
    または: /gh:start 2
```

## Real-World Workflow（現実的なワークフロー）

### Scenario 1: 同一セッション内での完結

```bash
# セッション開始
/gh:issue work 42
→ TodoWrite作成: 5タスク

/gh:start
→ Task 1実装
→ 完了 → GitHub即座更新（1/5, 20%）

/gh:start
→ Task 2実装
→ 完了 → GitHub即座更新（2/5, 40%）

/gh:start
→ Task 3実装
→ 完了 → GitHub即座更新（3/5, 60%）

/gh:start
→ Task 4実装
→ 完了 → GitHub即座更新（4/5, 80%）

/gh:start
→ Task 5実装
→ 完了 → GitHub即座更新（5/5, 100%）
→ Issue #42自動クローズ ✅
```

### Scenario 2: セッション中断・翌日再開

```bash
# Session 1（月曜日・自宅）
/gh:issue work 42
→ TodoWrite作成: 5タスク

/gh:start
→ Task 1実装
→ 完了 → GitHub即座更新（1/5, 20%）

/gh:start
→ Task 2実装
→ 完了 → GitHub即座更新（2/5, 40%）

（セッション終了・TodoWrite破棄）

# Session 2（火曜日・オフィス・別マシン）
/gh:start
→ Phase 0: Context Sync実行
→ セッションコンテキスト: Issue #42マッピングなし
→ 新しいセッション開始

# Issue連携を再確立
/gh:issue work 42
→ GitHubから最新状態取得（2/5完了を確認）
→ 未完了3タスクのみTodoWrite作成:
   Task 3: pending
   Task 4: pending
   Task 5: pending

/gh:start
→ Task 3実装
→ 完了 → GitHub即座更新（3/5, 60%）

/gh:start
→ Task 4実装
→ 完了 → GitHub即座更新（4/5, 80%）

（セッション終了）

# Session 3（水曜日・カフェ・ノートPC）
/gh:issue work 42
→ GitHubから最新状態取得（4/5完了を確認）
→ 未完了1タスクのみTodoWrite作成:
   Task 5: pending

/gh:start
→ Task 5実装
→ 完了 → GitHub即座更新（5/5, 100%）
→ Issue #42自動クローズ ✅
```

### Scenario 3: チームコラボレーション

```bash
# Developer A（月曜日）
/gh:issue work 42
→ TodoWrite作成: 5タスク

/gh:start
→ Task 1: Backend API実装
→ 完了 → GitHub即座更新（1/5, 20%）

/gh:start
→ Task 2: Database schema実装
→ 完了 → GitHub即座更新（2/5, 40%）

（Developer Aは離脱）

# Developer B（火曜日・別マシン）
/gh:issue work 42
→ GitHubから最新状態取得（2/5完了を確認）
→ 未完了3タスクのみTodoWrite作成:
   Task 3: Frontend component
   Task 4: API統合
   Task 5: E2Eテスト

/gh:start
→ Task 3実装
→ 完了 → GitHub即座更新（3/5, 60%）

（Developer Bも離脱）

# Developer A（水曜日・復帰）
/gh:issue work 42
→ GitHubから最新状態取得（3/5完了を確認）
→ 未完了2タスクのみTodoWrite作成

/gh:start
→ Task 4実装
→ 完了 → GitHub即座更新（4/5, 80%）

/gh:start
→ Task 5実装
→ 完了 → GitHub即座更新（5/5, 100%）
→ Issue #42自動クローズ ✅
```

## Context Sync Logic（同期ロジック詳細）

### Issue連携の自動検出

```python
# 疑似コード
def start_task():
    # Step 1: セッションコンテキストを確認
    issue_mapping = get_session_context("issue_todowrite_mapping")

    if issue_mapping:
        # Issue連携あり → 自動同期
        issue_number = issue_mapping["issue_number"]
        last_sync = issue_mapping["last_sync"]

        # GitHubから最新状態を取得
        github_state = fetch_issue_state(issue_number)

        # 同期が必要か判定
        if needs_sync(github_state, last_sync):
            sync_todowrite_from_github(issue_number)
            print("✅ GitHub同期完了")

    # Step 2: タスク選択と実行
    task = select_task()
    execute_task(task)
```

### 同期の判定条件

```yaml
同期が必要なケース:
  1. 前回同期から時間経過（> 5分）
  2. GitHubのコメント数が増加
  3. Issue本文が更新された
  4. TodoWriteとGitHubの完了数が不一致

同期不要なケース:
  1. 最終同期から < 5分
  2. GitHubに変更なし
  3. TodoWriteとGitHub状態が一致
```

### TodoWrite再構築アルゴリズム

```python
def sync_todowrite_from_github(issue_number):
    # GitHubから最新タスク状態を取得
    github_tasks = parse_issue_tasks(issue_number)

    # 現在のTodoWriteを取得
    current_todos = get_current_todowrite()

    # 完了済みタスクをTodoWriteから削除
    for task in github_tasks:
        if task.completed:
            remove_from_todowrite(task.id)

    # 新しい未完了タスクを追加
    for task in github_tasks:
        if not task.completed and not exists_in_todowrite(task.id):
            add_to_todowrite(task)

    # セッションコンテキストを更新
    update_session_context({
        "issue_number": issue_number,
        "last_sync": now(),
        "completed_count": count_completed(github_tasks)
    })
```

## MCP Integration

### Serena MCP（プロジェクトコンテキスト）
```yaml
用途: 既存コードパターンの理解
activation:
  - find_symbol: 既存関数・クラス検索
  - read_file: コード規約確認
  - search_for_pattern: 類似実装パターン

重要: 進捗管理には使わない（GitHubが代替）
```

### Context7 MCP（フレームワークパターン）
```yaml
用途: 公式ドキュメント参照
activation:
  - React/Vue/Angular検出時
  - フレームワークベストプラクティス適用
```

### Magic MCP（UI生成）
```yaml
用途: UIコンポーネント自動生成
activation:
  - フロントエンドタスク
  - コンポーネント実装
```

### Sequential MCP（複雑な実装計画）
```yaml
用途: 段階的実装計画
activation:
  - 複雑度が高いタスク
  - 多段階実装が必要
```

### Playwright MCP（テスト生成）
```yaml
用途: E2Eテスト自動生成
activation:
  - --with-testsフラグ
  - フロントエンド実装
```

## Persona Activation

### 自動ペルソナ選択
```yaml
frontend_tasks:
  keywords: ['UI', 'component', 'page', 'React', 'Vue']
  personas: [frontend, architect]

backend_tasks:
  keywords: ['API', 'service', 'database', 'auth']
  personas: [backend, security, architect]

fullstack_tasks:
  keywords: ['feature', 'integration', 'system']
  personas: [architect, frontend, backend, security]
```

## Examples

### Example 1: Phase-by-Phaseモード（推奨: 10+ tasks）🆕

```bash
# 15タスクのIssueをPhase単位で作業
/gh:issue work 42 --phase-by-phase

Claude: 📊 Issue #42: JWT認証実装（15タスク）

Phase-by-Phase モード有効化 ✅
→ 最初の未完了Phase: Phase 1 - Backend（3タスク）のみTodoWrite作成

Phase Summary:
⏳ Phase 1: Backend - 0/3 タスク
⏳ Phase 2: Frontend - 0/4 タスク
⏳ Phase 3: Testing - 0/5 タスク
⏳ Phase 4: Deployment - 0/3 タスク

TodoWriteタスク（Phase 1のみ）:
⏳ 1. API実装
⏳ 2. Database schema
⏳ 3. Auth middleware

合計: 3タスク（Phase 1のみ）
次のPhase: Phase 2 - Frontend (4タスク)

# 最初のタスク実行
/gh:start

Claude: 📊 Phase Progress: Phase 1/4 - Backend
Current Phase: 3タスク（残り3タスク）

📋 次のタスクを選択
Task #1: "API実装"
Status: pending → in_progress

🚀 実装エージェント起動...
✅ Task #1完了

🔄 同期エージェント起動...
→ GitHub Issue #42更新: "✅ Task 1/3: API実装 (33.3%)"
✅ 同期完了

📊 Phase 1 進捗: 1/3タスク (33.3%)
次のタスク: #2 "Database schema"

# Phase 1完了後、Phase 2自動展開
/gh:start  # Task 2実装
/gh:start  # Task 3実装 → Phase 1完了

Claude: ✅ Phase 1 - Backend 完了！

📋 次のPhase自動展開: Phase 2 - Frontend
TodoWriteタスク追加（4タスク）:
⏳ 4. Login UI component
⏳ 5. Dashboard layout
⏳ 6. API integration
⏳ 7. Form validation

Phase Summary:
✅ Phase 1: Backend - 3/3 タスク
🔄 Phase 2: Frontend - 0/4 タスク
⏳ Phase 3: Testing - 0/5 タスク
⏳ Phase 4: Deployment - 0/3 タスク

# Phase 2作業継続
/gh:start

Claude: 📊 Phase Progress: Phase 2/4 - Frontend
Current Phase: 4タスク（残り4タスク）

Task #4: "Login UI component"
Status: pending → in_progress
...
```

### Example 2: セッション再開（自動同期）

```bash
# Session 1で2タスク完了後、終了

# Session 2（翌日）
User: /gh:start

Claude: 🔄 Context Sync実行中...

📊 セッションコンテキスト確認
→ Issue #42マッピング検出
→ 最終同期: 18時間前

🔍 GitHubから最新状態取得
→ Issue #42: "JWT認証実装"
→ コメント解析: 2/5タスク完了（40%）
→ Task 1 (API実装): ✅ 完了
→ Task 2 (Database): ✅ 完了
→ Task 3-5: 未完了

🔄 TodoWrite同期
→ 完了済みタスク削除: Task 1, 2
→ 未完了タスクのみ維持: Task 3, 4, 5

✅ 同期完了
GitHub進捗: 2/5タスク (40%)
TodoWrite: 3タスク（未完了のみ）

📋 次のタスクを選択
Task #3: "Frontend認証UI実装"
Status: pending → in_progress

🎭 ペルソナ起動: Frontend, Architect
🔧 MCP起動: Magic, Context7

🚀 実装エージェント起動...
→ [実装エージェント] コンポーネント生成中...
→ [実装エージェント] テスト作成中...
→ [実装エージェント] ビルド検証中...
✅ [実装エージェント] Task #3完了

🔄 同期エージェント起動...
→ [同期エージェント] progress-tracker skill起動
→ [同期エージェント] GitHub Issue #42更新中...
→ [同期エージェント] コメント投稿: "✅ Task 3/5: Frontend認証UI実装 (60%)"
→ [同期エージェント] チェックボックス更新: [x] Task 3
✅ [同期エージェント] 同期完了

📊 進捗更新完了
GitHub: 3/5タスク (60%)
次のタスク: #4 "API統合"
```

### Example 2: Issue連携なしでの動作

```bash
User: /gh:start

Claude: 🔄 Context Sync実行中...

📊 セッションコンテキスト確認
→ Issue連携なし
→ TodoWriteのみモードで動作

📋 TodoWriteから次のタスクを選択
Task #1: "バグ修正: ログインバリデーション"
Status: pending → in_progress

🎭 ペルソナ起動: Backend
🔧 MCP起動: Serena（既存コード確認）

🚀 実装開始...

✅ 完了
Task #1: completed

⚠️ GitHub同期なし（Issue連携がありません）

次のタスク: #2 "UI改善"
```

### Example 3: 並列実行

```bash
User: /gh:start 1,2,3 --parallel

Claude: 🔄 Context Sync実行中...
→ Issue #42: 0/5タスク
→ 同期完了 ✅

📋 3タスクを並列実行
Task #1: "UIコンポーネントA"
Task #2: "UIコンポーネントB"
Task #3: "UIコンポーネントC"

🚀 3つのagent起動
[Agent 1] Task #1実行中...
[Agent 2] Task #2実行中...
[Agent 3] Task #3実行中...

⏳ 並列実行中...

[Agent 1] ✅ Task #1完了 (2分30秒)
→ GitHub即座更新（1/5, 20%）

[Agent 2] ✅ Task #2完了 (1分45秒)
→ GitHub即座更新（2/5, 40%）

[Agent 3] ✅ Task #3完了 (3分10秒)
→ GitHub即座更新（3/5, 60%）

✅ 全タスク完了
GitHub進捗: 3/5タスク (60%)
次のタスク: #4, #5
```

## Options

### `--framework <name>`
フレームワーク明示指定
```bash
/gh:start --framework react
```

### `--with-tests`
テスト自動生成
```bash
/gh:start --with-tests
```

### `--safe`
セキュリティ検証強化
```bash
/gh:start --safe
```

### `--parallel`
複数タスクを並列実行
```bash
/gh:start 1,2,3 --parallel
```

### `--no-sync`
自動同期をスキップ（高速化）
```bash
/gh:start --no-sync
```
⚠️ 注意: セッション再開時は非推奨

## Error Handling

### TodoWriteが空
```bash
User: /gh:start

Claude: ⚠️ TodoWriteにタスクがありません。

次のいずれかを実行:
1. Issueから作成: /gh:issue work <number>
2. ブレストから: /gh:brainstorm → /gh:issue create → /gh:issue work
```

### 全タスク完了
```bash
User: /gh:start

Claude: ✅ 全タスク完了！

GitHub Issue #42: 5/5タスク (100%)
Status: Closed

次の作業:
/gh:issue list --mine
```

### 同期エラー
```bash
User: /gh:start

Claude: ⚠️ GitHub同期エラー

原因: Issue #42が見つかりません

対処:
1. Issueが削除された場合: Issue連携なしモードで続行
2. ネットワークエラー: /gh:start --no-sync で一時スキップ
3. 再試行: /gh:issue work 42
```

## Integration Points

### `/gh:issue work` との連携
```bash
/gh:issue work 42
→ TodoWrite作成
→ Issue-TodoWriteマッピング確立
→ セッションコンテキストに保存

/gh:start
→ マッピング検出
→ 自動同期有効
```

### `progress-tracker` skill との連携
```yaml
動作:
  - /gh:start実行時にサブエージェント経由で自動起動
  - Task完了後に同期エージェントが起動
  - progress-tracker skillを確実に実行
  - 完了ごとにGitHub即座更新
  - セッション終了後も状態はGitHubに永続化

サブエージェント委譲による確実性:
  - TodoWriteイベント検知の制約を回避
  - 独立したエージェントでGitHub操作を実行
  - エラーハンドリングと再試行を独立管理
  - メインフローのブロッキング回避
```

## Boundaries

### Will Do ✅
- セッション開始時にGitHubから最新状態を自動同期
- タスク完了ごとに即座にGitHub Issue更新
- セッション間での作業継続性を保証
- 複数デバイス・複数人での協調作業を支援
- 完了済みタスクをTodoWriteから自動除外

### Will Not Do ❌
- Serenaメモリに進捗を保存（GitHubが唯一の真実）
- 同期なしでの作業続行（--no-syncフラグ時を除く）
- 完了していないタスクを放置して次へ進む
- GitHubとTodoWriteの不一致を放置

## Tips

💡 **Tip 1**: セッション再開時は自動同期 - 何もせず `/gh:start` でOK

💡 **Tip 2**: タスク完了ごとに即座GitHub更新 - サブエージェントが確実に実行

💡 **Tip 3**: GitHub = 真実の記録、TodoWrite = 作業キュー - 役割分担が明確

💡 **Tip 4**: 複数デバイスOK - 自宅・オフィス・カフェでシームレスに続行

💡 **Tip 5**: チームコラボOK - メンバー間で進捗を自動共有

💡 **Tip 6**: Issue連携必須 - `/gh:issue work` でマッピング確立

💡 **Tip 7**: 完了済み除外 - 既に終わったタスクは無視して効率化

💡 **Tip 8**: 同期は完全自動 - 実装→同期の2段階エージェント委譲で確実性保証

💡 **Tip 9**: エラー隔離 - 同期エラーがあっても実装は完了済み（再試行可能）

## Related Commands

- `/gh:brainstorm` - 要件発見
- `/gh:issue create` - Issue作成
- `/gh:issue work` - **Issue-TodoWriteマッピング確立（必須）**
- `/gh:start` - **タスク実装開始（このコマンド）**
- `/gh:issue status` - 進捗確認
- `/gh:issue sync` - 手動同期（通常不要）
- `/gh:issue close` - Issue完了

## Workflow Summary

```bash
# 完全なワークフロー
/gh:brainstorm "feature"           # 要件整理
/gh:issue create --from-file ...   # Issue作成
/gh:issue work 42                  # TodoWrite作成 + マッピング確立
/gh:start                          # Task 1実装 → GitHub更新
/gh:start                          # Task 2実装 → GitHub更新
# （セッション終了）

# 翌日再開
/gh:start                          # 自動同期 → Task 3実装
/gh:start                          # Task 4実装 → GitHub更新
/gh:start                          # Task 5実装 → Issue自動クローズ ✅
```

---

## アーキテクチャ詳細

**2段階サブエージェント委譲**:

1. **実装エージェント** (Phase 3)
   - Task tool → general-purpose agent
   - コード生成・編集・テスト実行
   - ビルド検証・品質チェック
   - 完了後、制御をメインエージェントに返却

2. **同期エージェント** (Phase 4) ← **NEW: 確実な自動更新**
   - Task tool → general-purpose agent
   - progress-tracker skill起動
   - GitHub Issue更新（コメント＋チェックボックス）
   - 全タスク完了時の自動クローズ
   - エラー時の再試行制御

**利点**:
- ✅ TodoWriteイベント検知制約を完全回避
- ✅ GitHub同期の確実性を100%保証
- ✅ エラー隔離（実装失敗 ≠ 同期失敗）
- ✅ 非同期実行でメインフローをブロックしない

**Phase 0のContext Sync**で最新状態をGitHubから取得し、セッション間の継続性を保証します。これにより、どのデバイス・どのセッションでも作業を続けられます。
