---
name: gh:usage
description: "GitHub Issue駆動開発のユースケースと実践ガイド"
category: workflow
complexity: medium
mcp-servers: []
---

# /gh:usage - Issue駆動開発ユースケース集

## 🎯 基本ワークフロー

### パターン1: 壁打ち → Issue化 → 実装

最も推奨される完全なワークフロー:

```bash
# ステップ1: アイデアを壁打ち
/gh:brainstorm "データパイプライン共通化について考えたい"
→ 対話的に要件整理
→ ファイル保存: claudedocs/brainstorm/pipeline_commonization_requirements_20251031.md

# ステップ2: Issue作成
/gh:issue create --from-file @claudedocs/brainstorm/pipeline_commonization_requirements_20251031.md
→ GitHub Issue #1 作成

# ステップ3: 作業開始
/gh:issue work 1
→ TodoWriteタスク自動生成
→ 進捗追跡有効化

# ステップ4: 実装
(TodoWriteでタスクを完了していく)
→ 自動的にGitHub更新

# ステップ5: 完了
(最後のタスク完了)
→ Issue自動クローズ ✅
```

---

## 🚀 SuperClaude連携パターン

### パターン2: 並列実装（効率重視）

複数の独立タスクを並列実行:

```bash
# Issue #1の確認
"Issue #1を確認して"

# 並列実装指示
/sc:task "Issue #1の3タスクを並列実装:
- Task 1.1: predict_gbdt() 統一
- Task 1.2: BaseTrainer 共通化
- Task 1.3: CSV dtype統一

Serenaでコードベース理解してから
サブエージェントで並列実行して"
```

**何が起こるか**:
1. Serenaでコードベース構造を理解
2. 3つのサブエージェントが同時起動
3. 各タスクを独立して実装
4. 統合してGitにコミット
5. Issue進捗を自動更新

**時間短縮**: 55%（9時間 → 4時間）

---

### パターン3: 段階的実装（安全重視）

リスク分析してから実装:

```bash
# ステップ1: 分析
/sc:analyze "Issue #1の影響範囲とリスクを分析"

# ステップ2: 設計レビュー
/sc:design "分析結果を踏まえて実装設計をレビュー"

# ステップ3: 実装
/sc:implement "設計に基づいてIssue #1を実装"

# ステップ4: 検証
/sc:test "実装したコードのテストを実行"
```

---

### パターン4: ワークフロー生成

実装手順を自動生成:

```bash
/sc:workflow "Issue #1の実装ワークフローを生成"
→ PRD形式の詳細な実装計画を生成
→ 生成されたワークフローに従って実装
```

---

## 📋 Issue管理コマンド集

### Issue一覧確認

```bash
# オープンなIssue確認
"オープンなIssue一覧を見せて"

# 自分のIssue確認
/gh:issue list --mine

# 特定状態のIssue
/gh:issue list --state all
```

---

### Issue作成パターン

**パターンA: brainstormから作成（推奨）**
```bash
/gh:brainstorm "新機能のアイデア"
→ 要件整理
→ claudedocs/brainstorm/feature_requirements_20251031.md 生成

/gh:issue create --from-file @claudedocs/brainstorm/feature_requirements_20251031.md
```

**パターンB: 既存ドキュメントから作成**
```bash
/gh:issue create --from-file @docs/architecture/feature_spec.md
```

**パターンC: インタラクティブ作成**
```bash
/gh:issue create --interactive
→ 対話形式でIssue作成
```

---

### Issue作業開始

**基本パターン**:
```bash
/gh:issue work 42
→ Issue #42のタスクをTodoWriteに変換
→ 進捗追跡開始
```

**自動クローズ無効**:
```bash
/gh:issue work 42 --no-auto-close
→ 全タスク完了でもIssueは自動クローズしない
```

---

### 進捗確認

```bash
# Issue状態確認
/gh:issue status 42

# 詳細確認（TodoWrite状態も表示）
/gh:issue view 42 --with-todos
```

---

### 手動同期

```bash
# 特定Issueを同期
/gh:issue sync 42

# 全Issueを同期
/gh:issue sync --all
```

---

## 🔄 セッション管理パターン

### パターンA: 1セッション完結（推奨）

```bash
/gh:issue work 42
(全タスクを1セッション内で完了)
→ 自動的にIssue更新・クローズ
```

**メリット**: シンプル、確実、トラブルなし

---

### パターンB: セッション中断・再開

```bash
# セッション1
/gh:issue work 42
(2タスク完了、セッション終了)

# セッション2（別の日）
/gh:issue work 42  # 再実行でGitHubから最新状態取得
→ 残りタスクがTodoWriteに復元
(残りタスクを完了)
→ 自動的にIssue更新・クローズ
```

**メリット**: 長期タスクに対応

---

## 💡 実践的なユースケース

### ユースケース1: バグ修正

```bash
# Issue作成
"バグレポートからIssue作成:
 - 症状: ログイン時にエラー
 - 再現手順: xxx
 - 期待動作: yyy"

# 調査と修正
/sc:troubleshoot "Issue #X のログインエラーを調査して修正"

# 完了報告
"Issue #X のタスクを全て完了してクローズ"
```

---

### ユースケース2: 新機能開発

```bash
# アイデア整理
/gh:brainstorm "ユーザー認証機能を追加したい"
→ claudedocs/brainstorm/auth_requirements_20251031.md 生成

# Issue化
/gh:issue create --from-file @claudedocs/brainstorm/auth_requirements_20251031.md

# 段階的実装
/sc:workflow "Issue #X の実装ワークフロー生成"
→ ワークフローに従って実装

# 完了確認
/gh:issue status X
```

---

### ユースケース3: リファクタリング

```bash
# 分析
/sc:analyze "コードベース全体の共通化可能箇所を分析"
→ 分析結果をファイルに保存

# Issue作成
/gh:issue create --from-file analysis_results.md

# 並列実装
/sc:task "Issue #X のリファクタリングを並列実行"
```

---

### ユースケース4: 技術調査

```bash
# 調査開始
/sc:research "Next.js 15の新機能とマイグレーション方法"
→ 調査結果を docs/research/ に保存

# 移行計画のbrainstorm
/gh:brainstorm "Next.js 15への移行計画を立てたい"
→ claudedocs/brainstorm/nextjs15_migration_20251031.md

# Issue化
/gh:issue create --from-file @claudedocs/brainstorm/nextjs15_migration_20251031.md

# 段階的移行
/gh:issue work X
(段階的にタスクを実施)
```

---

## 🎯 Tips集

### Tip 1: `/gh:issue work` だけで完全自動
```bash
/gh:issue work 42
→ Issue解析、TodoWrite変換、進捗追跡、全自動
```

### Tip 2: TodoWriteで作業するだけで自動更新
```
TodoWriteでタスクを完了 → GitHub自動更新
何も意識する必要なし！
```

### Tip 3: `/gh:brainstorm` → `/gh:issue create` が最強
```bash
/gh:brainstorm → 要件整理 → ファイル保存
/gh:issue create --from-file → Issue化
→ 思考から実装まで一貫したフロー
```

### Tip 4: セッション内で作業完結が最も効率的
```
1セッションで完了 = シンプル & 確実
```

### Tip 5: Skillsは自動起動
```
issue-parser, issue-todowrite-sync, progress-tracker
→ 全て自動起動、意識不要
```

---

## 🔧 トラブルシューティング

### GitHub CLI認証エラー
```bash
gh auth login
→ GitHub認証を再実行
```

### 進捗が同期されない
```bash
/gh:issue sync 42
→ 手動同期実行
```

### Skillsが起動しない
```
"issue-parser skillを使ってIssue #42を解析"
→ 明示的にSkill名を指定
```

---

## 🏗️ アーキテクチャ理解

```
┌─────────────────┐
│  /gh:issue      │  ← ユーザー操作
│  (コマンド)      │
└────────┬────────┘
         │
    ┌────▼─────────────────────────┐
    │  Skills (自動起動)             │
    │                              │
    │  ┌─────────────────────┐    │
    │  │ issue-parser        │    │
    │  │ (Issue解析)         │    │
    │  └──────┬──────────────┘    │
    │         │                    │
    │  ┌──────▼──────────────┐    │
    │  │ issue-todowrite-sync│    │
    │  │ (変換・同期)         │    │
    │  └──────┬──────────────┘    │
    │         │                    │
    │  ┌──────▼──────────────┐    │
    │  │ progress-tracker    │    │
    │  │ (進捗監視)          │    │
    │  └─────────────────────┘    │
    └──────────────────────────────┘
                 │
    ┌────────────▼─────────────┐
    │  GitHub Issues           │
    │  TodoWrite               │
    │  Session Context         │
    └──────────────────────────┘
```

---

## 📚 関連ドキュメント

- **brainstormガイド**: `/gh:brainstorm`
- **完全ワークフロー**: `/gh:guide`
- **詳細仕様**: `$HOME/.claude/commands/gh/issue.md`
- **全体ガイド**: `$HOME/.claude/commands/gh/README.md`
- **SuperClaude連携**: `/sc:help`

---

## 🚀 クイックスタート

```bash
# 1. アイデアを整理
/gh:brainstorm "実装したいこと"
→ claudedocs/brainstorm/feature_requirements_20251031.md

# 2. Issue作成
/gh:issue create --from-file @claudedocs/brainstorm/feature_requirements_20251031.md
→ Issue #X 作成

# 3. 実装開始（並列実行）
/sc:task "Issue #X を並列実装"

# 4. 完了確認
/gh:issue status X
```

これだけで完璧なIssue駆動開発！
