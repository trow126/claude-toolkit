---
name: gh:start
description: TodoWriteタスクを自動並列判断で実装。Phase 1.5（依存関係分析）は必須ステップ。並列実行プランを表示後、最適化された並列実行を自動実行。GitHub Issue自動同期でセッション間の作業継続性を保証。
category: workflow
complexity: standard
mcp-servers: [sequential, context7, magic, playwright, morphllm, serena]
personas: [architect, frontend, backend, security, qa-specialist]
---

# /gh:start - TodoWriteタスク実装開始

> **核心**: GitHub Issue = 永続化層、TodoWrite = セッション内キュー

## Triggers
- TodoWriteタスク作成後の実装開始
- GitHub Issue workフロー後の実装作業
- セッション再開時の作業継続

## Usage

```bash
# デフォルト（推奨・自動並列判断）
/gh:start

→ 自動実行される処理:
  1. TodoWriteから全pendingタスク取得
  2. タスク内容を読み取り
  3. 依存関係を自動分析（Phase 1.5必須）
  4. 並列グループ作成
  5. 実行プランを表示 📋
  6. 並列可能タスクを並列実行 ⚡

# 特定タスクのみ実行（依存関係分析は実行される）
/gh:start 2,3
→ 指定タスク間の依存関係を分析
→ プラン表示 → 並列実行

# 強制並列（依存関係分析スキップ・⚠️リスクあり）
/gh:start 1,2,3 --parallel
→ Phase 1.5スキップ
→ すべて強制的に並列実行
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
  - 自動クローズ（全完了時）
```

## Behavioral Flow

### Phase 0: Context Sync（最重要）

```yaml
1. セッションコンテキスト確認:
   - Issue-TodoWriteマッピング存在？
   - 存在する → GitHub連携モード
   - 存在しない → TodoWriteのみモード

2. GitHub連携モード時の自動同期:
   a. GitHubから最新Issue取得
      gh issue view <number> --json body,comments

   b. コメントから進捗解析
      "✅ Task 1/5: API実装 (20%)" → Task 1完了

   c. TodoWriteを再構築
      - 完了済みタスク削除
      - 未完了タスクのみ維持

3. 同期結果表示:
   GitHub進捗: 2/5タスク (40%)
   TodoWrite: 3タスク（未完了のみ）
```

### Phase 1: Task Selection

```yaml
4. pendingタスクを確認・選択:
   - 引数なし → 全pending（並列判断）
   - 番号指定 → 指定タスク
   - --parallel → 強制並列
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
     if has_dependency(task):
       # 依存あり → 新グループ作成
       groups.append(current_group)
       current_group = {tasks: [task], mode: "sequential"}
     else:
       # 依存なし → 現グループに追加（最大3タスク）
       if len(current_group.tasks) < 3:
         current_group.tasks.append(task)
       else:
         groups.append(current_group)
         current_group = {tasks: [task], mode: "parallel"}

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
```

### Phase 2: Context Analysis

```yaml
9. 各タスクの解析:
   - フレームワーク検出
   - ドメイン分類（frontend/backend/fullstack）
   - ペルソナ自動選択
   - MCPサーバー決定
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
          5. 全完了判定 → Issue自動クローズ
      )

    ⚠️ 重要: Task toolは逐次実行されるため競合なし

14. 全タスク完了時の自動処理:
    - progress-tracker skillが検出
    - 完了コメント投稿: "🎉 All tasks completed!"
    - Issue状態: open → closed
    - GitHub Projects: Status → Done
```

### Phase 5: Next Task

```yaml
15. 次の未完了タスク提案:
    次のタスク: #2 "Frontend component"
    実行: /gh:start
```

## Real-World Workflow

### Scenario 1: セッション再開

```bash
# Session 1（月曜）
/gh:issue work 42  # 5タスク作成
/gh:start          # Task 1実装 → GitHub更新
/gh:start          # Task 2実装 → GitHub更新
# （セッション終了）

# Session 2（火曜・別マシン）
/gh:start
→ Context Sync実行
→ GitHubから最新状態取得（2/5完了確認）
→ 未完了3タスクのみTodoWrite再構築
→ Task 3実装開始
```

### Scenario 2: 並列実行（自動判断）

```bash
/gh:start  # 引数なし = 全pendingタスク

→ 7タスクを分析
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
--framework <name>   # フレームワーク指定
--with-tests         # テスト自動生成
--parallel           # 強制並列（依存関係分析スキップ）
--no-sync            # 自動同期スキップ（非推奨）
```

## Error Handling

```bash
# TodoWriteが空
→ /gh:issue work <number> または /gh:brainstorm

# 全タスク完了
→ GitHub Issue自動クローズ
→ /gh:issue list --mine

# 同期エラー
→ Issue削除: TodoWriteのみモード続行
→ ネットワーク: --no-syncで一時スキップ
```

## Integration Points

```yaml
/gh:issue work:
  - TodoWrite作成
  - Issue-TodoWriteマッピング確立
  - セッションコンテキスト保存

progress-tracker skill:
  - /gh:start実行時にサブエージェント経由で自動起動
  - Task完了後に同期エージェント起動
  - 完了ごとにGitHub即座更新
```

## Boundaries

### Will Do ✅
- GitHubから最新状態を自動同期
- タスク完了ごとに即座GitHub更新
- セッション間での作業継続性保証
- 複数デバイス・複数人協調作業支援
- 完了済みタスク自動除外

### Will Not Do ❌
- Serenaメモリに進捗保存（GitHubが真実）
- 同期なし作業（--no-sync除く）
- GitHubとTodoWriteの不一致放置

## 実行指示（重要）

**あなたは今、`/gh:start` コマンドを実行しています。**

### 🔴 デフォルト動作（必ず実行）

**ユーザーが明示的に指示しなくても、以下を自動的に実行してください:**

1. ✅ TodoWriteから全pendingタスクを取得
2. ✅ 各タスクの内容（content）を読み取る
3. ✅ Phase 1.5で依存関係を自動分析
4. ✅ 並列グループを作成
5. ✅ **実行プランをユーザーに表示**
6. ✅ グループごとに実装を実行

**⚠️ Phase 1.5（依存関係分析）はデフォルト動作です。スキップしないでください。**

---

### 引数解析と実行モード

**引数なし (`/gh:start`)**:
- 全pendingタスク → Phase 1.5必須実行 → 並列グループ作成 → プラン表示 → 実装

**タスク番号指定 (`/gh:start 1,2,3`)**:
- 指定タスク → Phase 1.5必須実行 → 並列グループ作成 → プラン表示 → 実装

**`--parallel` フラグ (`/gh:start 1,2,3 --parallel`)** ⚠️:
- Phase 1.5スキップ → 全て強制並列 → リスク: 依存関係違反
- このモードのみPhase 1.5をスキップ可能

### 🔴 必須実行フロー（すべてのステップを実行）

**⚠️ Phase 1.5は必須ステップです。スキップ禁止。**

```yaml
実行順序（すべて必須）:

Phase 0: GitHub同期
  - Issue-TodoWriteマッピング確認
  - GitHub最新状態取得

Phase 1: タスク選択
  - 全pendingタスクを取得
  - TodoWriteから実際のタスク内容（content）を読み取る

🚨 Phase 1.5: 依存関係分析（必須・スキップ禁止）🚨
  ステップ:
    1. 全pendingタスクの内容を解析
    2. 明示的依存を検出（"depends on Task N"）
    3. レイヤー依存を検出（Database/API/UI/Test）
    4. ファイル競合を検出（同一ファイル編集）
    5. 並列グループ作成
    6. 📋 実行プランをユーザーに表示（必須）

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

Phase 4: GitHub同期
  - 完了タスクをGitHub更新

Phase 5: 次タスク提案
  - 残りpendingタスクを提示
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
2. 最大3タスクまで並列グループ化
3. 依存タスクは別グループ配置
4. 繰り返し

### Phase 4: GitHub同期詳細

全タスク完了後:
1. progress-tracker skillでGitHub Issue更新
2. チェックボックス `[x]` 変更
3. 全タスク完了時にIssue自動クローズ

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
    5. 全完了時: Issue自動クローズ
```

## Related Commands

```bash
/gh:brainstorm      # 要件発見
/gh:issue create    # Issue作成
/gh:issue work      # マッピング確立（必須）
/gh:start           # 実装開始（このコマンド）
/gh:issue status    # 進捗確認
/gh:issue close     # Issue完了
```

## Workflow Summary

```bash
/gh:brainstorm "feature"
/gh:issue create --from-file ...
/gh:issue work 42
/gh:start  # Task 1 → GitHub更新
/gh:start  # Task 2 → GitHub更新
# セッション終了

# 翌日再開
/gh:start  # 自動同期 → Task 3
/gh:start  # Task 4 → 完了 → 自動クローズ ✅
```

## Tips

💡 **セッション再開**: 何もせず `/gh:start` で自動同期
💡 **即座更新**: タスク完了ごとにサブエージェントが確実実行
💡 **役割分担**: GitHub=真実、TodoWrite=作業キュー
💡 **複数デバイスOK**: 自宅・オフィス・カフェでシームレス継続
💡 **Issue連携必須**: `/gh:issue work` でマッピング確立
