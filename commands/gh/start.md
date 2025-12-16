---
name: gh:start
description: GitHub Issue駆動開発の統合エントリーポイント。Issue読み込み・タスク変換・依存分析・並列実装・進捗同期を一貫して実行。セッション間の作業継続性を保証。
category: workflow
complexity: standard
mcp-servers: [sequential, context7, magic, playwright, morphllm, serena]
personas: [architect, frontend, backend, security, qa-specialist]
---

# /gh:start - GitHub Issue駆動開発の統合コマンド

> **核心**: GitHub Issue = 永続化層（SSOT）、Serena Memory = チェックポイント、TodoWrite = セッション内キュー

## Triggers
- GitHub Issueでの作業開始（初回）
- セッション再開時の作業継続
- checkpoint からの自動復旧

## Usage

```bash
# Issue番号を指定して作業開始（推奨）
/gh:start 42

→ 自動実行される処理:
  1. Issue #42 を GitHub から取得
  2. タスクを解析・TodoWrite に変換
  3. checkpoint を作成
  4. 依存関係を自動分析（Phase 1.5必須）
  5. 並列グループ作成
  6. 実行プランを表示 📋
  7. 並列可能タスクを並列実行 ⚡

# セッション再開（checkpoint自動復元）
/gh:start
→ checkpoint検索 → 自動復元 → 作業継続

# 特定タスクのみ実行
/gh:start 42 --tasks 2,3
→ 指定タスク間の依存関係を分析
→ プラン表示 → 並列実行

# 強制並列（依存関係分析スキップ・⚠️リスクあり）
/gh:start 42 --parallel
→ Phase 1.5スキップ
→ すべて強制的に並列実行

# 全タスク実行（10タスク超の場合）
/gh:start 42 --all
→ タスク数制限を無視
→ 全pendingタスクを実行
```

## Architecture

```
┌──────────────────────────────────────┐
│  GitHub Issue (永続化層)              │
│  - 全体進捗の唯一の真実               │
│  - セッション間で永続化               │
└──────────┬───────────────────────────┘
           ↓ 同期
┌──────────────────────────────────────┐
│  TodoWrite (セッション内キュー)       │
│  - 現在のセッションの作業管理         │
│  - 未完了タスクのみ含む               │
└──────────────────────────────────────┘

実装フロー:
/gh:start (メインエージェント)
  ↓
Phase 3: Task実装 (Task tool → 実装エージェント)
  ↓
Phase 4: GitHub同期 (Task tool → 同期エージェント)
  - progress-tracker skill起動
  - GitHub Issue更新
  - 全完了時はPR作成を提案（PRマージでIssue自動クローズ）
```

## Behavioral Flow

### Phase 0: Issue Load & Context Sync（統合エントリーポイント）

**🚨 このフェーズは必ず最初に実行してください。**

```yaml
条件分岐:

═══════════════════════════════════════════════════════════════
A) Issue番号が引数で指定された場合 (/gh:start 42)
═══════════════════════════════════════════════════════════════

1. GitHub から Issue 取得:
   gh issue view 42 --json body,comments,state,title

2. Issue 状態確認:
   - closed → エラー「Issue #42 は既にクローズ済みです」
   - open → 続行

3. 既存 checkpoint 確認:
   list_memories() → "issue_42_checkpoint" 検索

   3a. checkpoint 存在 → 復元モード:
       - read_memory("issue_42_checkpoint")
       - GitHub照合（GitHubが勝つ）
       - TodoWrite再構築
       - explore_results復元（あれば）
       - ログ: "✅ Resumed Issue #42 from checkpoint"

   3b. checkpoint 不在 → 新規モード:
       続行（下記 4-8）

4. issue-parser skill 呼び出し:
   Issue本文 + コメントからタスク抽出
   - フェーズ構造の検出
   - チェックボックス状態の解析
   - 完了済み ([x]) と未完了 ([ ]) の識別

5. issue-todowrite-sync skill 呼び出し:
   - スマートデフォルト適用:
     - 8+ タスク + Phase情報あり → 現在Phaseのみ
     - 8+ タスク + Phase情報なし → 最初の5タスクのみ
     - 8未満 → 全タスク
   - 完了済みタスク除外
   - TodoWrite作成

6. checkpoint-manager skill 呼び出し:
   write_memory("issue_42_checkpoint", {
     issue_number: 42,
     issue_title: "...",
     current_phase: "Phase 1",
     task_mapping: [...],
     progress: { completed: 0, total: N, percentage: 0 },
     created_at: now(),
     last_updated: now()
   })

7. GitHub Projects 更新:
   source scripts/gh-projects-integration.sh
   gh_projects_set_in_progress 42

8. 結果表示:
   ✅ Issue #42 loaded: "Issue Title"
   TodoWrite: N タスク（未完了のみ）
   → Phase 1 へ進む

═══════════════════════════════════════════════════════════════
B) Issue番号が未指定の場合 (/gh:start)
═══════════════════════════════════════════════════════════════

1. checkpoint 検索:
   list_memories() → filter "issue_*_checkpoint"

2a. checkpoint なし:
    エラー表示:
    "❌ アクティブなIssueがありません。

    使用方法:
      /gh:start 42    # Issue #42 で作業開始
      /gh:issue create  # 新しいIssue作成"

2b. 単一 checkpoint:
    - read_memory("issue_{number}_checkpoint")
    - GitHub照合（GitHubが勝つ）
    - TodoWrite再構築
    - explore_results復元（あれば）
    - ログ: "✅ Resumed Issue #N from checkpoint"

2c. 複数 checkpoint:
    ⚠️ ユーザーに選択を促す:
    "複数のアクティブIssueが検出されました:
     - Issue #42: 3/8 (37.5%) - Phase 2: API Implementation
     - Issue #45: 1/5 (20%) - Phase 1: Database

     どのIssueを続行しますか？
     → /gh:start 42 または /gh:start 45"

3. GitHub照合（SSOT）:
   a. gh issue view <number> --json body,comments
   b. チェックボックス状態を解析
   c. GitHub状態 vs checkpoint → GitHubが勝つ
   d. 不一致があれば checkpoint を更新

4. TodoWrite再構築:
   a. todowrite_snapshotが存在する場合:
      - snapshotからTodoWrite状態を直接復元
   b. snapshotなし:
      - task_mappingから未完了タスク抽出
   c. TodoWrite作成

5. explore_results復元（Compact耐性）:
   checkpointにexplore_resultsが存在する場合:
   - Phase 2のExplore並列実行をスキップ
   - ログ: "✅ Restored explore_results (skipping Phase 2 Explore)"

6. 結果表示:
   ✅ Resumed Issue #42 from checkpoint
   GitHub進捗: 3/8タスク (37.5%)
   Current Phase: Phase 2 (API Implementation)
   TodoWrite: 2タスク（未完了分）
   → Phase 1 へ進む
```

### Phase 1: Task Selection

```yaml
4. pendingタスクを確認・選択:

   a. 全pendingタスクを取得

   b. 🔴 タスク数チェック（大量タスク対策・必須）:
      pending_count = len(pending_tasks)

      if pending_count > 10:
        ⚠️ 警告表示:
          "{pending_count}個のpendingタスクがあります

          推奨アクション:
          - 特定タスクのみ: /gh:start 42 --tasks 1,2,3
          - 最初の5タスクのみ実行（デフォルト）
          - 全タスク実行: /gh:start 42 --all

          デフォルト動作: 最初の5タスクのみ実行します"

   c. 実行タスク決定:
      - 引数なし + pending ≤ 10 → 全pending（並列判断）
      - 引数なし + pending > 10 → 最初の5タスク（警告表示済み）
      - 番号指定 (例: 1,2,3) → 指定タスクのみ
      - --all フラグ → 全pending強制実行
      - --parallel フラグ → 強制並列
```

### Phase 1.5: Parallel Decision（自動判断・必須ステップ）

**🚨 このフェーズは必ず実行してください。スキップ禁止。**

```yaml
5. 全pendingタスクを収集
   - TodoWriteから status == "pending" のタスクすべて
   - 各タスクの content（説明文）を取得

6. 🔴 依存関係分析（必須・各タスクのcontentを必ず解析）:

   a. 明示的依存検出:
      - "depends on Task N"
      - "requires Task N"
      - "after Task N"
      → Task NがGroup M ⇒ 現タスクはGroup M+1

   b. レイヤー依存検出（キーワードマッチ）:
      - Layer 1 (Database): database, schema, migration, model
      - Layer 2 (Backend): API, endpoint, service, controller
      - Layer 3 (Frontend): UI, component, page, view
      - Layer 4 (Testing): test, E2E, integration
      → 下位レイヤーを先にグループ配置

   c. ファイル競合検出:
      - 同一ファイルパス言及 → 別グループに分離
      - 例: "auth.ts修正" vs "auth.ts修正" → 逐次化

7. 並列グループ作成アルゴリズム:
   groups = []
   current_group = {tasks: [], mode: "parallel"}

   for task in sorted_by_layer:
     if has_dependency(task) OR has_file_conflict(task, current_group):
       # 依存あり OR ファイル競合 → 新グループ作成
       groups.append(current_group)
       current_group = {tasks: [task], mode: "sequential"}
     else:
       # 依存なし・ファイル競合なし → 現グループに追加（制限なし）
       # Claude Codeが動的に最大10並列まで自動バッチング
       current_group.tasks.append(task)

   # ⚠️ 大規模グループ警告（10タスク超）
   for group in groups:
     if len(group.tasks) > 10:
       warn("Group has >10 tasks. Claude Code auto-batches max 10 concurrent.")

   groups.append(current_group)

8. 🔴 実行プランをユーザーに表示（必須）:

   ⚠️ 必ずユーザーに実行プランを見せてください。

   表示形式:
   📋 Parallel Execution Plan:

   Group 1 (sequential): Task 1 "Database setup"
   Group 2 (parallel):   Task 2,3 "API endpoints" ⚡
   Group 3 (parallel):   Task 4,5 "UI components" ⚡
   Group 4 (sequential): Task 6 "E2E tests"

   ⚡ Estimated speedup: 50% (21min → 11min)

   このプラン表示をスキップしないでください。

9. 🔴 checkpoint更新（Compact耐性・必須）:

   checkpoint-manager skillで並列グループを保存:
   - parallel_groups配列をcheckpointに追加
   - Compact後も依存関係分析結果を復元可能
   - write_memory("issue_{number}_checkpoint", updated_yaml)
```

### Phase 2: Context Analysis（Parallel Explore）

```yaml
9. タスクをドメイン別に分類:
   backend_tasks: API, endpoint, service, controller キーワード
   database_tasks: database, schema, migration, model キーワード
   frontend_tasks: UI, component, page, view キーワード

10. ドメイン別Exploreサブエージェントを並列起動:

    ⚠️ 1メッセージ内で複数Task tool呼び出し（真の並列実行）

    # モデル自動判定ロジック:
    if task_count <= 5 AND single_domain:
      model = "haiku"  # 軽量・高速
    else:
      model = "sonnet"  # 複雑タスク対応

    # 並列Explore起動（ドメインが存在する場合のみ）
    Task(
      subagent_type: "Explore",
      model: auto,  # 上記ロジックで判定
      prompt: "Analyze {domain} layer patterns for implementation:
               - Existing patterns and conventions
               - Related files to modify
               - Recommended approach based on codebase"
    )

    例（3ドメイン並列）:
    単一メッセージ内で:
      - Task tool #1: backend Explore
      - Task tool #2: database Explore
      - Task tool #3: frontend Explore
      ↓
    Claude Codeが3つを同時実行 ⚡

11. Explore結果をcheckpointに保存（Compact耐性）:

    checkpoint-manager skill起動:
    update_explore_results(checkpoint_yaml, {
      backend: {
        patterns: ["REST API", "Express middleware"],
        files: ["src/api/routes.ts", "src/middleware/auth.ts"],
        recommendations: "Use existing auth middleware pattern"
      },
      database: {
        patterns: ["Prisma ORM", "PostgreSQL"],
        files: ["prisma/schema.prisma"],
        recommendations: "Extend User model with fields"
      },
      frontend: {
        patterns: ["React", "TailwindCSS"],
        files: ["src/components/Auth/"],
        recommendations: "Follow existing form component pattern"
      }
    })

    → Compact後も再実行不要、explore_resultsから復元

12. フレームワーク検出、ペルソナ自動選択、MCPサーバー決定

オプション: --no-explore でPhase 2のExplore並列実行をスキップ可能
```

### Phase 3: Implementation（並列実行の実装）

```yaml
10. グループごとに実行:

    🚨 CRITICAL: 並列グループは1メッセージで複数Task tool 🚨

    並列グループ（例: tasks [2,3,4]）:
      ステップ:
        1. 1つのメッセージを構築
        2. そのメッセージ内で3つのTask tool呼び出し
        3. 各Taskに詳細なprompt指定:
           - Task 2: "Task 2を実装: ..."
           - Task 3: "Task 3を実装: ..."
           - Task 4: "Task 4を実装: ..."
        4. メッセージ送信 → Claude Code並列実行 ⚡

      ✅ 正しい: 単一メッセージ、複数Task tool
      ❌ 間違い: Task tool → 待機 → Task tool → 待機

    逐次グループ（例: task [1]）:
      - Task tool 1つ呼び出し
      - 完了待ち
      - 次のグループへ

11. 実装エージェント（Task tool内）:
    - Serenaでコードベース理解
    - コード生成・編集
    - テスト実行（--with-tests時）
    - ビルド検証
    - TodoWrite更新
```

### Phase 4: GitHub Sync

```yaml
12. 各タスク完了後、即座にGitHub更新:

    並列実行時の注意:
    - 複数タスクが同時完了 → 競合リスク
    - 解決策: Task tool経由で同期を逐次化

12.5. 🔴 checkpoint更新（タスク完了時・必須）:

    各タスク完了後にcheckpoint-manager skillで更新:
    - task_mapping[i].status = "completed"
    - progress.overall_completed++
    - progress.percentage再計算
    - last_updated = now()
    - write_memory("issue_{number}_checkpoint", updated_yaml)

    ⚠️ 重要: GitHub同期と並行してcheckpoint更新

13. Task tool経由でGitHub同期エージェント起動:

    for completed_task in completed_tasks:
      Task(
        subagent_type: "general-purpose",
        prompt: |
          Issue #<number>のTask <N>が完了。

          1. progress-tracker skill起動
          2. 完了タスクカウント: <N>/<total>
          3. GitHubコメント投稿:
             "✅ Task <N>/<total>: <task_name> (<percentage>%)"
          4. チェックボックス更新: [ ] → [x]
      )

    ⚠️ 重要: Task toolは逐次実行されるため競合なし

14. 全タスク完了時の処理:
    - progress-tracker skillが検出
    - 完了コメント投稿: "🎉 All tasks completed!"
    - PR作成を提案（Issueはクローズしない）:
      "📋 Ready for PR:
       git add . && git commit -m 'feat: Issue #42 implementation'
       gh pr create --title 'Issue #42: タイトル' --body 'Closes #42'

       PRマージ時にIssueが自動クローズされます"
    - GitHub Projects: Status → In Review
```

### Phase 5: Next Task

```yaml
15. 次の未完了タスク提案:
    次のタスク: #2 "Frontend component"
    実行: /gh:start
```

## Real-World Workflow

### Scenario 1: 新規作業開始

```bash
# Issue作成後、作業開始
/gh:issue create --from-file claudedocs/brainstorm/auth.md
→ Issue #42 created

/gh:start 42
→ Issue読み込み → タスク解析 → TodoWrite作成
→ checkpoint作成
→ 依存関係分析 → 並列プラン表示
→ Task 1実装 → GitHub更新
→ Task 2実装 → GitHub更新
# （セッション終了）
```

### Scenario 2: セッション再開

```bash
# Session 2（翌日・別マシン）
/gh:start
→ checkpoint検索 → Issue #42 発見
→ GitHubから最新状態取得（2/5完了確認）
→ 未完了3タスクのみTodoWrite再構築
→ Task 3実装開始

# または明示的にIssue番号指定
/gh:start 42
→ 既存checkpoint発見 → 復元モード
→ Task 3実装開始
```

### Scenario 3: 並列実行（自動判断）

```bash
/gh:start 42

→ 7タスクを分析（10以下なので全実行）
→ 依存関係検出:
  Task 1: Database (Layer 1)
  Task 2: User model (Layer 2, Task 1依存)
  Task 3,4: Login/Logout API (Layer 2, Task 2依存)
  Task 5,6: UI (Layer 3, Task 3依存)
  Task 7: E2E (Layer 4, 全依存)

→ 実行プラン:
  Group 1: [Task 1]     - 逐次
  Group 2: [Task 2]     - 逐次
  Group 3: [Task 3,4]   - 並列 ⚡
  Group 4: [Task 5,6]   - 並列 ⚡
  Group 5: [Task 7]     - 逐次

→ 推定時短: 50% (逐次21分 → 並列11分)
```

### Scenario 4: 大量タスク制御

```bash
# 15タスクある場合
/gh:start 42

→ ⚠️ 15個のpendingタスクがあります
→ 推奨アクション:
  - 特定タスクのみ: /gh:start 42 --tasks 1,2,3
  - 最初の5タスクのみ実行（デフォルト）
  - 全タスク実行: /gh:start 42 --all
→ デフォルト動作: 最初の5タスクのみ実行します

→ Task 1-5を実行...

# 全タスク実行したい場合
/gh:start 42 --all
→ 15タスク全て実行（タスク数制限無視）
```

## MCP Integration

```yaml
Serena: 既存コードパターン理解（進捗管理にはGitHub使用）
Context7: フレームワーク公式ドキュメント参照
Magic: UIコンポーネント自動生成
Sequential: 複雑な実装計画
Playwright: E2Eテスト生成（--with-tests時）
```

## Persona Activation

```yaml
frontend: [frontend, architect]
backend: [backend, security, architect]
fullstack: [architect, frontend, backend, security]
```

## Options

```bash
--tasks <1,2,3>      # 特定タスクのみ実行
--framework <name>   # フレームワーク指定
--with-tests         # テスト自動生成
--parallel           # 強制並列（依存関係分析スキップ）
--all                # 全pendingタスク実行（10タスク超でも実行）
--no-sync            # 自動同期スキップ（非推奨）
--no-explore         # Phase 2のExplore並列実行スキップ（高速化）
```

## Error Handling

```bash
# TodoWriteが空 + checkpointなし
→ /gh:start <issue_number> でIssue番号を指定
→ または /gh:issue create で新規Issue作成

# Issueが見つからない
→ gh issue list --mine で有効なIssue確認

# Issueが既にクローズ済み
→ エラー表示「Issue #N は既にクローズ済みです」
→ gh issue reopen N で再開可能

# 全タスク完了
→ PR作成を提案（"Closes #42"付き）
→ PRマージでIssue自動クローズ
→ /gh:issue close でcheckpoint削除・振り返り

# 同期エラー
→ Issue削除: TodoWriteのみモード続行
→ ネットワーク: --no-syncで一時スキップ
```

## Integration Points

```yaml
Phase 0 (Issue Load):
  - issue-parser skill: Issue解析
  - issue-todowrite-sync skill: TodoWrite作成
  - checkpoint-manager skill: チェックポイント作成
  - GitHub Projects: ステータス更新

checkpoint-manager skill:
  - Phase 0: 新規チェックポイント作成 or 復元
  - Phase 1.5後: parallel_groups保存
  - タスク完了時: status, progress更新
  - PRマージ後: /gh:issue close経由でcheckpoint削除

progress-tracker skill:
  - /gh:start実行時にサブエージェント経由で自動起動
  - Task完了後に同期エージェント起動
  - 完了ごとにGitHub即座更新
  - checkpoint-manager skillと連携
```

## Boundaries

### Will Do ✅
- GitHubから最新状態を自動同期
- タスク完了ごとに即座GitHub更新
- セッション間での作業継続性保証
- 複数デバイス・複数人協調作業支援
- 完了済みタスク自動除外
- 大量タスク警告表示（10タスク超）
- デフォルトで最初の5タスクのみ実行（10タスク超の場合）

### Will Not Do ❌
- Serenaメモリに進捗保存を忘れる（checkpoint-manager skillで自動更新）
- 同期なし作業（--no-sync除く）
- GitHubとTodoWriteの不一致放置
- 警告なしで大量タスクを全実行（--allフラグが必要）
- Phase 0復旧をスキップ（Compact後の必須ステップ）

## 実行指示（重要）

**あなたは今、`/gh:start` コマンドを実行しています。**

### 🔴 デフォルト動作（必ず実行）

**ユーザーが明示的に指示しなくても、以下を自動的に実行してください:**

0. ✅ **Phase 0: Issue Load & Context Sync**
   - Issue番号あり: Issue取得 → 解析 → TodoWrite作成 → checkpoint作成
   - Issue番号なし: checkpoint検索 → 復元 → TodoWrite再構築
1. ✅ TodoWriteから全pendingタスクを取得
2. ✅ タスク数チェック（>10で警告、最初の5タスクに制限）
3. ✅ 各タスクの内容（content）を読み取る
4. ✅ Phase 1.5で依存関係を自動分析
5. ✅ 並列グループを作成 → **checkpoint更新**
6. ✅ **実行プランをユーザーに表示**
7. ✅ グループごとに実装を実行 → **タスク完了ごとにcheckpoint更新**

**⚠️ Phase 0とPhase 1.5はデフォルト動作です。スキップしないでください。**

---

### 引数解析と実行モード

**Issue番号指定 (`/gh:start 42`)**:
- Phase 0: Issue読み込み → タスク解析 → TodoWrite作成
- Phase 1.5: 依存関係分析 → 並列グループ作成 → プラン表示
- Phase 3: 実装実行

**引数なし (`/gh:start`)**:
- Phase 0: checkpoint検索 → 復元
- 以降同様

**タスク指定 (`/gh:start 42 --tasks 2,3`)**:
- 指定タスクのみ実行

**`--all` フラグ (`/gh:start 42 --all`)**:
- タスク数制限を無視して全て実行

**`--parallel` フラグ (`/gh:start 42 --parallel`)** ⚠️:
- Phase 1.5スキップ → 全て強制並列 → リスク: 依存関係違反

### 🔴 必須実行フロー（すべてのステップを実行）

**⚠️ Phase 0とPhase 1.5は必須ステップです。スキップ禁止。**

```yaml
実行順序（すべて必須）:

🚨 Phase 0: Issue Load & Context Sync（最優先）🚨

  A) Issue番号あり (/gh:start 42):
    1. gh issue view 42 --json body,comments,state,title
    2. closed → エラー、open → 続行
    3. checkpoint確認:
       - 存在 → 復元モード（GitHub照合 → TodoWrite再構築）
       - 不在 → 新規モード:
         a. issue-parser skill
         b. issue-todowrite-sync skill
         c. checkpoint-manager skill
         d. GitHub Projects更新

  B) Issue番号なし (/gh:start):
    1. list_memories() → "issue_*_checkpoint" フィルタ
    2. checkpoint発見 → 復元
    3. なし → エラー「/gh:start <issue_number> を指定」

Phase 1: タスク選択
  - 全pendingタスクを取得
  - タスク数チェック（>10で警告、最初の5タスクに制限）
  - TodoWriteから実際のタスク内容を読み取る

🚨 Phase 1.5: 依存関係分析（必須・スキップ禁止）🚨
  ステップ:
    1. 全pendingタスクの内容を解析
    2. 明示的依存を検出（"depends on Task N"）
    3. レイヤー依存を検出（Database/API/UI/Test）
    4. ファイル競合を検出（同一ファイル編集）
    5. 並列グループ作成
    6. 📋 実行プランをユーザーに表示（必須）
    7. 🔴 checkpoint更新: parallel_groups保存

  出力例:
    📋 Parallel Execution Plan:

    Group 1 (sequential): Task 1 "Database setup"
    Group 2 (parallel):   Task 2,3 "API endpoints" ⚡
    Group 3 (sequential): Task 4 "E2E tests"

    ⚡ Estimated speedup: 50%

Phase 2: コンテキスト分析
  - フレームワーク検出
  - ペルソナ選択

Phase 3: グループごとに実装
  - 並列グループ: 1メッセージで複数Task tool
  - 逐次グループ: 1つずつTask tool
  - 🔴 各タスク完了後: checkpoint更新（status, progress）

Phase 4: GitHub同期
  - 完了タスクをGitHub更新
  - checkpoint.last_github_sync更新

Phase 5: 次タスク提案
  - 残りpendingタスクを提示
  - Phase完了時: checkpoint.current_phase更新
```

### 🚨 並列実行の実装（最重要）🚨

**CRITICAL: 並列グループの実装方法**

❌ **間違い（これは逐次実行になる）**:
```python
# Task toolを順番に呼び出し → 逐次実行
response_1 = Task(subagent_type="general", prompt="Task 2実装")
# Task 2完了を待つ ← ここで直列化される
response_2 = Task(subagent_type="general", prompt="Task 3実装")
# Task 3完了を待つ ← ここで直列化される
```

✅ **正しい（真の並列実行）**:
```python
# 1つのメッセージで複数Task tool呼び出し
# Claude Codeが自動的に並列実行する

単一メッセージ内で:
  - Task tool #1: Task 2実装
  - Task tool #2: Task 3実装
  - Task tool #3: Task 4実装
  ↓
Claude Codeが3つを同時実行 ⚡
```

**実装パターン（並列グループ時）**:
```yaml
parallel_group = {tasks: [2, 3, 4], mode: "parallel"}

# このグループを実行する時:
1. 1つのメッセージを準備
2. そのメッセージ内で3つのTask tool呼び出しを記述
3. 各Task toolに個別のpromptを指定
4. 送信 → Claude Codeが並列実行

# ⚠️ 絶対にやらないこと:
- Task tool呼び出し → 結果待ち → 次のTask tool呼び出し
```

**逐次グループ実装**:
```yaml
sequential_group = {tasks: [1], mode: "sequential"}

# 1タスクずつTask tool呼び出し → 完了待ち → 次
```

### 依存関係分析（簡易実装）

**明示的依存**: "depends on Task N" / "requires Task N"

**レイヤー検出**:
- Layer 1: database, schema, migration
- Layer 2: API, endpoint, service
- Layer 3: UI, component, frontend
- Layer 4: test, E2E

**ファイル競合**: 同一ファイルパス言及 → 逐次実行

### 実行プラン生成

1. 依存関係のないタスク収集
2. ファイル競合チェック（同一ファイル編集 → 別グループ）
3. 並列グループ化（制限なし・Claude Code自動バッチング最大10）
4. 依存タスクは別グループ配置
5. 繰り返し

⚠️ 10タスク超のグループは警告表示

### Phase 4: GitHub同期詳細

全タスク完了後:
1. progress-tracker skillでGitHub Issue更新
2. チェックボックス `[x]` 変更
3. checkpoint更新（各タスク完了時）
4. 全タスク完了時にPR作成を提案（Issueはクローズしない）

Task tool経由でサブエージェント委譲:
```yaml
Task tool起動:
  subagent_type: "general-purpose"
  prompt: |
    Issue #<number>のTask <N>が完了。
    1. progress-tracker skill起動
    2. 完了タスクカウント
    3. GitHubコメント投稿: "✅ Task <N>/<total>: <name> (<percentage>%)"
    4. チェックボックス更新
    5. checkpoint-manager skill: タスク状態更新
    6. 全完了時: PR作成を提案（Issueはクローズしない）
```

## Related Commands

```bash
/gh:brainstorm      # 要件発見
/gh:issue create    # Issue作成
/gh:start 42        # 作業開始・継続（このコマンド）
/gh:issue close 42  # Issue完了
```

## Workflow Summary

```bash
# 完全ワークフロー
/gh:brainstorm "feature"
/gh:issue create --from-file ...  # → Issue #42 作成
/gh:start 42                       # → 作業開始
# （セッション終了）

# 翌日再開
/gh:start                          # → checkpoint自動復元 → 作業継続
/gh:start                          # → 全Task完了 → PR作成を提案

# PR作成
git add . && git commit -m "feat: ..."
gh pr create --body "Closes #42"   # → CodeRabbitレビュー

# レビュー対応後、マージ
gh pr merge                        # → Issue #42 自動クローズ

# 振り返り・クリーンアップ
/gh:issue close 42                 # → 振り返り記録 → checkpoint削除
```

## Tips

💡 **初回**: `/gh:start 42` でIssue番号を指定して開始
💡 **再開**: `/gh:start` だけでcheckpointから自動復元
💡 **即座更新**: タスク完了ごとにGitHub自動同期
💡 **PR経由クローズ**: 全タスク完了→PR作成→マージでIssue自動クローズ
💡 **役割分担**: GitHub=SSOT、Serena Memory=checkpoint、TodoWrite=作業キュー
💡 **複数デバイスOK**: 自宅・オフィス・カフェでシームレス継続
💡 **大量タスク制御**: 10タスク超は自動的に最初の5タスクのみ実行
💡 **Compact耐性**: Phase 0で自動復旧、checkpointで状態永続化

---

**Last Updated**: 2025-12-16
**Version**: 2.1.0 (PR経由クローズ - 全タスク完了時はPR作成を提案、Issueはマージで自動クローズ)
