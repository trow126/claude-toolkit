---
name: gh:issue
description: "TodoWrite連携によるGitHub Issue駆動開発ワークフロー。Issueの管理、タスク変換、進捗追跡、双方向同期を実現。"
category: workflow
complexity: standard
mcp-servers: []
personas: []
---

# GitHub Issue管理コマンド

TodoWrite自動連携と進捗追跡機能を持つ包括的なGitHub Issueワークフロー

## 利用可能なコマンド

### create - 新しいIssueを作成

複数の入力方法でGitHub Issueを作成します。

```bash
# 基本的な作成
/gh:issue create "Feature: User Authentication"

# ファイルから作成
/gh:issue create --from-file claudedocs/brainstorm/auth_requirements_20251031.md

# 対話的に作成
/gh:issue create --interactive
```

**処理フロー**:
1. Issue詳細の収集
2. GitHubに作成
   ```bash
   gh issue create --title "..." --body "..." --assignee "@me"
   ```
3. GitHub Projectsに追加（ステータス: "Todo"）
   ```bash
   source scripts/gh-projects-integration.sh
   gh_projects_set_todo $ISSUE_NUMBER
   ```
4. セッションコンテキストにメタデータ保存

**オプション**:
- `--from-file <path>`: ファイル内容をIssue本文として使用
- `--interactive`: 対話的に詳細を入力
- `--assignee <user>`: 担当者を指定（`@me`で自分）

---

### list - Issue一覧表示

```bash
# 開いているIssueを表示
/gh:issue list

# 自分に割り当てられたIssue
/gh:issue list --mine

# ラベルでフィルタ
/gh:issue list --label feature
```

**オプション**:
- `--state <open|closed|all>`: Issue状態でフィルタリング
- `--label <label>`: 指定ラベルのIssueのみ表示
- `--mine`: 自分に割り当てられたIssue（`--assignee @me --state open`の短縮形）

---

### view - Issue詳細表示

```bash
# 基本的な表示
/gh:issue view 42

# 詳細表示（コメント含む）
/gh:issue view 42 --detailed
```

**オプション**:
- `--detailed`: コメント履歴と詳細情報を含めて表示
- `--with-todos`: TodoWrite同期状態も合わせて表示

---

### work - Issue作業開始

IssueをTodoWriteタスクに変換して追跡を開始します。

**このコマンドがSkillsを起動するメインコマンドです！**

```bash
# スマートデフォルト（自動判定）
/gh:issue work 42

# 全タスクを強制表示
/gh:issue work 42 --all-tasks

# Phase単位を強制
/gh:issue work 42 --phase-by-phase
```

**処理フロー**:

このコマンドは**Task toolでgeneral-purpose agentに委譲**して実行されます。

1. **issue-parser skill**: Issue解析（本文+コメント、完了済み/未完了タスク識別）
2. **issue-todowrite-sync skill**: 未完了タスクのみTodoWriteに変換（Phase単位制限適用）
3. **checkpoint-manager skill**: Serena Memoryにチェックポイント保存（Compact耐性）
4. **GitHub Projects更新**: ステータス → "In Progress"
5. **progress-tracker skill**: バックグラウンド監視開始（自動同期、完了時自動クローズ）

**スマートデフォルト（Compact耐性設計）**:
- **8タスク以上 + Phase情報あり**: Phase単位で作成（現在Phaseのみ）
- **8タスク以上 + Phase情報なし**: 最初の5タスクのみ
- **8タスク未満**: 全タスク作成

**⚠️ 重要**: 一度に大量のタスクをTodoWriteに入れない設計です。
Phase完了後は再度 `/gh:issue work` を実行して次Phaseをロードします。

**オプション**:
- `--all-tasks`: 全タスクを強制表示（スマートデフォルト無効化）
- `--phase-by-phase`: Phase単位を強制（タスク数に関わらず）
- `--current-phase <name>`: 特定Phaseから開始
- `--no-auto-close`: 全タスク完了時の自動クローズを無効化
- `--refresh`: GitHub最新状態と同期してTodoWrite更新

---

### status - Issue進捗表示

```bash
# 進捗を表示
/gh:issue status 42

# GitHubから強制更新
/gh:issue status 42 --refresh
```

セッションコンテキストから読み取り、現在のTodoWrite状態を表示します。

---

### sync - 進捗をGitHubに同期

```bash
# 特定のIssueを同期
/gh:issue sync 42

# 全アクティブIssueを同期
/gh:issue sync --all
```

`issue-todowrite-sync` skillを使用してTodoWriteの進捗をGitHub Issueに手動同期します。

---

### close - Issueを完了してクローズ

```bash
# Issueをクローズ
/gh:issue close 42

# 理由を指定
/gh:issue close 42 --reason completed

# 学習抽出スキップ
/gh:issue close 42 --no-retro
```

**処理フロー**:
1. **issue-retrospective skill**（`--no-retro`がない場合）
   - Issue履歴分析（タイムライン、タスク、コメント）
   - 成功パターン、課題、ブロッカー抽出
   - GitHub Issueに振り返りコメント投稿
   - `claudedocs/learnings.md` に知見追記
2. 完了サマリーをコメント投稿
3. GitHub Projects更新（ステータス → "Done"）
4. Issueをクローズ
5. セッションコンテキストをクリーンアップ
6. ブレインストーミングファイルを削除（`--from-file`で使用した場合）

**オプション**:
- `--reason <completed|not_planned|duplicate>`: クローズ理由
- `--quiet`: 完了サマリーコメントをスキップ
- `--no-retro`: 学習抽出（retrospective）をスキップ
- `--keep-brainstorm`: ブレインストーミングファイルを削除せずに保持

---

## Skills連携

### アーキテクチャ
```
/gh:issue work 42
  ↓
Task tool → general-purpose agent
  ↓
Agent内でSkills起動:
  1. issue-parser skill
  2. issue-todowrite-sync skill
  3. progress-tracker skill
```

### 1. issue-parser
- GitHubからIssue取得（本文+コメント）
- タスク、フェーズ、メタデータ抽出
- 完了済みタスク（[x]）識別

### 2. issue-todowrite-sync
- Issue → TodoWrite変換（未完了のみ）
- TodoWrite → GitHub同期
- セッションコンテキストでマッピング維持

### 3. progress-tracker
- TodoWrite完了イベント監視
- GitHub進捗コメント投稿
- 全タスク完了時Issue自動クローズ

### 4. checkpoint-manager
- Serena Memoryにチェックポイント保存
- タスク完了・Phase遷移時に更新
- Compact後の復旧サポート
- Issue完了時にチェックポイント削除

### 5. issue-retrospective
- Issue履歴分析
- 成功パターン、課題、ブロッカー抽出
- GitHub + `claudedocs/learnings.md` に記録

---

## GitHub Projects Integration

### 主な特徴
- **ゼロ設定**: 自動検出・自動作成
- **3状態管理**: Todo → In Progress → Done
- **自動フォールバック**: 権限エラー時はラベルモードに自動切替

### ステータス自動更新
```bash
/gh:issue create   → Projects: "Todo"
/gh:issue work     → Projects: "In Progress"
/gh:issue close    → Projects: "Done"
```

### Graceful Degradation
GitHub Projects権限がない場合、自動的にラベルモードに切り替わります:
- `status:todo`
- `status:in-progress`
- `status:done`

---

## ワークフロー例

### 例1: Brainstorm → Issue → 作業
```bash
# ステップ1: ブレインストーミング
/gh:brainstorm "ユーザー認証機能"
→ claudedocs/brainstorm/jwt_auth_requirements_20251031.md に保存

# ステップ2: Issue作成
/gh:issue create --from-file claudedocs/brainstorm/jwt_auth_requirements_20251031.md
→ Issue #42作成

# ステップ3: 作業開始
/gh:issue work 42
→ TodoWrite変換、進捗トラッカー起動

# ステップ4: タスク完了時
→ progress-trackerが自動的にGitHub更新
→ 全タスク完了で自動クローズ
```

### 例2: 既存Issue → TodoWrite（途中再開）
```bash
# セッション1
/gh:issue work 42
→ 既に3/8タスク完了済み → 未完了5タスクのみTodoWrite変換

# セッション2（翌日再開）
/gh:issue work 42 --refresh
→ 最新状態を取得 → 未完了タスクのみ復元
```

---

## エラー処理

- **GitHub CLI未検出**: インストール手順を提供
- **gitリポジトリ外**: デフォルトリポジトリ使用、または`--repo`フラグを促す
- **Issue未発見**: 明確なエラーメッセージ
- **ネットワークエラー**: 1回リトライ後適切に失敗
- **セッションコンテキストエラー**: セッション内メモリのみにフォールバック

---

## 依存関係

- `gh` CLI (GitHub CLI) - 認証済み
- Gitリポジトリコンテキスト
- TodoWriteツール（Claude Code組み込み）
- Task tool（agent委譲用）
- Python 3.6+（Skills用）
- Skills: `issue-parser`, `issue-todowrite-sync`, `checkpoint-manager`, `progress-tracker`, `issue-retrospective`

---

## Tips

💡 **Tip 1**: `/gh:issue list --mine`で割り当てられたIssueをすぐ確認

💡 **Tip 2**: `work`コマンドが最強 - Task toolで自動的にagentに委譲され全て処理

💡 **Tip 3**: 完了済みタスク（[x]）はTodoWriteから自動除外 - 未完了のみ作業

💡 **Tip 4**: スマートデフォルト有効 - 8タスク以上で自動的にPhase単位表示

💡 **Tip 5**: `/gh:brainstorm`と組み合わせてアイデアから実装まで完全ワークフロー

---

## 関連コマンド

- `/gh:brainstorm` - 要件発見（`create --from-file`と相性抜群）
- `/sc:workflow` - IssueからImplementationワークフロー生成
- `/sc:git` - Issue参照付きコミット（例: "feat: auth (#42)"）

---

## 実行指示

**あなたは今、`/gh:issue` コマンドを実行しています。**

ユーザーのコマンドを解析し、適切なサブコマンドを実行してください。

### create サブコマンド
1. **ラベル自動推論**: `issue-parser` skillでタイトル+本文から推論
2. **タスク数確認**: 8個以上で警告表示（分割推奨）
3. **GitHub Issue作成**: `gh issue create`
4. **GitHub Projects追加**: `scripts/gh-projects-integration.sh` → `gh_projects_set_todo`

### work サブコマンド
**重要**: このサブコマンドは**必ずTask toolを使用してgeneral-purpose agentに委譲**

**⚠️ 実装禁止**: このコマンドは準備と追跡設定のみ。実装コードは一切書かない。

**委譲するタスク内容**:
```
GitHub Issue #[number] の追跡準備を行います。

⚠️ 重要な制約:
- 実装コードは一切書かない
- タスクの変換と追跡設定のみ実行
- 完了後はユーザーに報告して待機

以下のSkillsを順次実行してください:

1. issue-parser skill: "use issue-parser skill for Issue #[number]"

2. issue-todowrite-sync skill: "use issue-todowrite-sync skill to convert Issue #[number] to TodoWrite"
   - スマートデフォルト（Compact耐性）:
     - 8タスク以上 + Phase情報あり → 現在Phaseのみ
     - 8タスク以上 + Phase情報なし → 最初の5タスクのみ
     - 8タスク未満 → 全タスク
   - `--all-tasks`: 全タスク強制（非推奨・Compact脆弱）
   - `--phase-by-phase`: Phase単位強制

3. checkpoint-manager skill: "use checkpoint-manager skill to create checkpoint for Issue #[number]"
   - Serena Memoryにチェックポイント保存
   - write_memory("issue_{number}_checkpoint", checkpoint_data)

4. GitHub Projects更新: `scripts/gh-projects-integration.sh` → `gh_projects_set_in_progress`

5. progress-tracker skill: "use progress-tracker skill for Issue #[number]"
```

### close サブコマンド
1. **issue-retrospective skill**（`--no-retro`がない場合）
2. 完了サマリーをコメント投稿
3. GitHub Projects更新: `gh_projects_set_done`
4. Issueクローズ: `gh issue close [number]`
5. **checkpoint-manager skill**: チェックポイント削除
   ```
   delete_memory("issue_{number}_checkpoint")
   ```
6. セッションコンテキストクリーンアップ
7. ブレインストーミングファイル削除（`--from-file`使用時）

---

**実行ルール**:
- `work`コマンドは**必ずTask toolでagentに委譲**（>3 steps = delegation rule）
- Agent内で**Skillsを順次起動**
- TodoWriteツールの呼び出しは**Skill内で実行**
- 各ステップの結果をユーザーに報告
- **⚠️ workコマンド完了後、実装には絶対に入らない** - ユーザーの明示的な指示を待つ

---

**Last Updated**: 2025-11-25
**Version**: 1.2.0 (Compact耐性設計)
