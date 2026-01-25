---
name: gh:guide
description: "Issue駆動開発の完全ワークフローガイド（壁打ち〜クローズまで）"
---

# Issue駆動開発ワークフローガイド

**目的**: 壁打ちからIssueクローズまでの完全な開発フローを理解する

---

## 🚀 クイックスタート（最小構成）

```bash
# 1. アイデアを整理
/gh:brainstorm
→ claudedocs/brainstorm/feature_requirements_20251031.md

# 2. Issueを作成
/gh:issue create --from-file claudedocs/brainstorm/feature_requirements_20251031.md
→ Issue #42 作成

# 3. 作業開始（Issue読み込み + 実装）
/gh:start 42
→ TodoWrite生成 → 依存分析 → 実装開始

# 4. 完了（自動的にクローズ）
(全タスク完了時)
```

---

## 📋 完全ワークフロー

### Phase 1: 壁打ち・要件整理

**目的**: 曖昧なアイデアから明確な要件を抽出

#### 方法A: `/gh:brainstorm` 使用（推奨）

```bash
$ /gh:brainstorm
```

**Claudeとの対話**:
```
あなた: "JWT認証を追加したい"

Claude: 🔍 Discovery Questions:

1. 認証システムの目的
   - 既存システムの問題点は？
   - 誰がどのリソースにアクセス？

2. 技術要件
   - 既存の認証機構は？
   - トークンの保存場所は？
   - セッション管理の方針は？

3. セキュリティ要件
   - トークン有効期限は？
   - リフレッシュトークン必要？

あなた: [回答]

Claude: 📝 要件ブリーフ生成中...

✅ 保存先: claudedocs/brainstorm/jwt_auth_requirements_20251031.md
```

**特徴**:
- Socratic対話による段階的な要件掘り下げ
- 多角的分析（アーキテクチャ、セキュリティ、パフォーマンス）
- Issue形式の構造化された要件ブリーフ生成
- ファイルベースで明示的・追跡可能

**出力**:
- `claudedocs/brainstorm/{feature}_requirements_{YYYYMMDD}.md`
- 明確なタスクリスト
- 技術仕様と制約
- フェーズ分け実装計画

#### 方法B: 直接対話

```bash
あなた: "JWT認証の要件を整理して、Issue作成用のドキュメントにして"
→ Claudeと対話で要件整理
→ 結果を claudedocs/brainstorm/ に保存依頼
```

**使い分け**:
- `/gh:brainstorm`: 体系的な要件整理が必要な時
- 直接対話: シンプルな機能、既に要件が明確な時

---

### Phase 2: Issue作成

**方法A: brainstormファイルから作成**（推奨）

```bash
$ /gh:issue create --from-file claudedocs/brainstorm/jwt_auth_requirements_20251031.md
```

**方法B: 既存ドキュメントから作成**

```bash
$ /gh:issue create --from-file @docs/architecture/analysis.md
```

**方法C: 対話形式**

```bash
$ /gh:issue create
# Claudeが対話的にタイトル・説明・タスクを聞く
```

**作成されるもの**:
- ✅ GitHubにIssue作成
- ✅ タスクリストを含む詳細説明
- ✅ 適切なラベルとマイルストーン

---

### Phase 3: 作業開始

```bash
$ /gh:start 42
```

**自動実行される処理**:

1. **Issue読み込み**:
   - `gh issue view 42 --json body,comments,state`
   - issue-parser skill でタスク抽出

2. **TodoWrite同期**:
   - GitHubのタスクリスト → TodoWriteに変換
   - 完了済み ([x]) は自動除外
   - スマートデフォルト適用（8+ タスク → Phase単位）

3. **checkpoint作成**:
   - Serena Memoryに保存（Compact耐性）
   - セッション再開時に自動復元

4. **GitHub Projects更新**:
   - ステータス → "In Progress"

5. **依存分析 → 実装開始**:
   - 依存関係分析 → 並列実行プラン表示
   - 実装開始

---

### Phase 4: 実装と記録

#### 自動記録されるもの

**タスク状態変化**:
```
TodoWrite: Task 1.1 → in_progress
→ notes.md: [13:00] Task 1.1 started

TodoWrite: Task 1.1 → completed
→ notes.md: [15:00] Task 1.1 completed
```

**セッション終了**:
```
→ セッション終了時にサマリープロンプト
→ 重要な内容を分類して保存
```

#### 手動記録

**設計判断を記録**:
```
"この判断をIssue 42に記録して：
 predict()統一でBaseEvaluationScriptを使う理由は
 継承構造が既にあり、450行のコード重複を削減できるから"

→ decisions.md に追加
```

**実験結果を保存**:
```
"この結果をIssue 42の実験ログに保存：
 パフォーマンステスト結果: 平均5ms"

→ experiments.md に追加
```

**作業メモ**:
```
"Issue 42にメモ：
 XGBoostはDMatrix変換が必要、LightGBM/CatBoostは直接ndarray可"

→ notes.md に追加
```

---

### Phase 5: SuperClaudeとの連携（効率化）

#### パターンA: spawnによる並列実装

```bash
$ /sc:spawn "Issue #42の3タスクを並列実装"
```

**実行フロー**:
```
1. Serenaでコードベース理解
2. タスク依存関係分析
3. 独立タスクを特定
4. サブエージェント起動（並列）
   - Agent 1: Task 1.1 → predict_gbdt()
   - Agent 2: Task 1.2 → BaseTrainer
   - Agent 3: Task 1.3 → CSV dtype
5. 統合とテスト
```

**時間短縮**: 最大55%（9時間 → 4時間）

#### パターンB: taskによる複雑実装

```bash
$ /sc:task "Issue #42のTask 1.1を実装
             複雑なリファクタリングが必要"
```

**使い分け**:
- **spawn**: 並列可能な複数タスク → 高速
- **task**: 複雑な単一タスク → 深い分析

---

### Phase 6: セッション管理

#### パターンA: 1セッション完結（推奨）

```bash
$ /gh:start 42
(全タスクを完了)
→ 自動的にIssue更新・クローズ
```

**メリット**: シンプル、状態管理不要

#### パターンB: セッション中断・再開

**Day 1**:
```bash
$ /gh:start 42
(Task 1.1, 1.2を完了)
# セッション終了
```

**Day 2**:
```bash
$ /gh:start  # checkpoint自動復元
→ checkpoint検出
→ GitHubから最新状態を取得
→ 前回の続きから作業
```

**表示内容**:
```
> Resuming work on Issue #42
> Checkpoint found: issue_42_checkpoint
> Progress: Task 1.1, 1.2 completed (2/3)
> Next: Task 1.3
```

---

### Phase 7: Issue完了とクローズ

#### 自動クローズ（全タスク完了時）

```
TodoWrite: 全タスク completed
→ 自動的にGitHub Issue更新
→ Issue状態: closed
→ progress-tracker が完了コメント投稿
```

#### 手動クローズ

```bash
$ /gh:issue close 42
```

**完了時の処理**:
```
→ issue-retrospective skillによる振り返り
→ GitHub Issueに完了コメント投稿
→ claudedocs/learnings.md に知見追記
```

---

## 🗂️ 情報管理の全体像

### 5つのシステムと役割

| システム | 用途 | 寿命 | 例 |
|---------|------|------|-----|
| **brainstorm/** | 要件整理 | Issue作成まで | "JWT auth requirements" |
| **TodoWrite** | 現在のタスク進捗 | セッション | "Task 1.1 in progress" |
| **GitHub Issue** | タスク定義と履歴 | 永続 | "Add JWT auth" |
| **work/** | 詳細な作業ログ | Issue完了まで | "XGBoost performance test" |
| **docs/** | 抽出された知識 | 永続 | "Auth system design" |
| **Serena** | コードベース理解 | 永続 | "Project auth patterns" |

### 情報フロー

```
壁打ち (/gh:brainstorm)
  ↓ claudedocs/brainstorm/*.md (一時ファイル)
Issue作成 (/gh:issue create --from-file)
  ↓ GitHub Issue (永続・SSOT)
作業開始 (/gh:start 42)
  ├─ Issue読み込み → TodoWrite (揮発)
  ├─ checkpoint → Serena Memory (Compact耐性)
  └─ GitHub Projects → "In Progress"
  ↓
実装作業
  ├─ TodoWrite完了 → GitHub自動更新
  └─ コード変更 → Git commits
  ↓
セッション再開 (/gh:start)
  ├─ checkpoint復元
  └─ GitHub照合 → TodoWrite再構築
  ↓
Issue完了 (/gh:issue close または自動)
  ├─ issue-retrospective (振り返り)
  ├─ GitHub Issue完了コメント
  ├─ claudedocs/learnings.md (知見追記)
  ├─ brainstorm/ 削除（自動）
  ├─ checkpoint削除
  └─ Issue自動クローズ
```

---

## 📖 コマンドリファレンス

### 基本コマンド

| コマンド | 用途 | 例 |
|---------|------|-----|
| `/gh:brainstorm` | 要件整理 | アイデアから要件を抽出 |
| `/gh:issue create` | Issue作成 | `--from-file` でbrainstormファイルから作成 |
| `/gh:issue close N` | 手動クローズ | Issue完了処理 |
| `/gh:start 42` | 作業開始 | Issue読み込み + TodoWrite + 実装 |
| `/gh:start` | 作業再開 | checkpoint自動復元 |

### 効率化コマンド

| コマンド | 用途 | 使い分け |
|---------|------|---------|
| `/sc:spawn` | 並列実装 | 複数の独立タスク |
| `/sc:task` | 複雑実装 | 深い分析が必要な単一タスク |

### 参照コマンド

| コマンド | 内容 |
|---------|------|
| `/gh:brainstorm` | brainstormガイド（詳細な使い方） |
| `/gh:usage` | ユースケース集 |
| `/gh:guide` | このガイド |
| `/serena:reset` | Serenaメモリ管理 |

---

## ⚠️ トラブルシューティング

### `/gh:start`でエラーが出る

**問題**: checkpointが見つからない

**解決策**:
```bash
$ /gh:start 42  # Issue番号を明示的に指定
```

### TodoWriteと同期しない

**問題**: タスク変更がIssueに反映されない

**解決策**:
1. `progress-tracker` スキルが有効か確認
2. セッション内でTodoWriteを使用しているか確認
3. `gh issue view 42` で手動確認

### セッション再開時に状態が失われる

**理解**: これは正常動作です

**理由**:
- TodoWrite = セッション揮発（これは仕様）
- checkpoint = Serena Memoryで永続（Compact耐性）
- GitHub Issue = Single Source of Truth

**対処**:
```bash
$ /gh:start  # checkpoint自動復元
# または
$ /gh:start 42  # Issue番号を明示的に指定
```

### 複数のアクティブIssueがある

**問題**: `/gh:start` で複数のcheckpointが検出された

**解決策**:
```bash
$ /gh:start 42  # 作業したいIssue番号を指定
```

### Serenaメモリが混乱している

**問題**: checkpointやIssue情報がSerenaに残っている

**解決策**:
```bash
$ /serena:reset
# 「issue_*_checkpointを全て削除して」
```

**正しいSerenaの使い方**:
- ✅ コードベース理解（アーキテクチャ、パターン）
- ✅ checkpoint（Issue作業状態の永続化）
- ❌ 手動でのタスク状態管理（自動に任せる）

---

## 💡 ベストプラクティス

### ✅ 推奨

1. **1セッション完結を目指す**
   - セッション管理の複雑さを回避
   - 状態の一貫性を保つ

2. **作業ログは自動に任せる**
   - タスク開始/完了は自動記録
   - 重要な判断だけ手動記録

3. **SuperClaudeで効率化**
   - 並列可能なタスクは `/sc:spawn`
   - 複雑なタスクは `/sc:task`

4. **定期的なGitコミット**
   - 論理的な区切りでコミット
   - work/ファイルはコミット不要

5. **Issueは小さく保つ**
   - 1 Issue = 1〜3日で完了
   - 大きな機能は複数Issueに分割

### ❌ 避けるべき

1. **brainstorm/やwork/ファイルをコミット**
   - 一時ファイル（.gitignoreされている）
   - brainstorm/: Issue作成まで
   - work/: Issue完了まで

2. **Serenaにタスク状態を保存**
   - コードベース理解のみ使用

3. **手動でGitHub Issue編集**
   - Single Source of Truthを保つ
   - 自動同期に任せる

4. **セッション跨ぎの多用**
   - 可能な限り1セッション完結

---

## 🎯 実践例

### 例1: 新機能実装（シンプル）

```bash
# Day 1: 全作業を1セッションで完了
$ /gh:brainstorm
  「JWT認証を追加したい」
  → 対話的に要件整理
  → claudedocs/brainstorm/jwt_auth_requirements_20251031.md

$ /gh:issue create --from-file claudedocs/brainstorm/jwt_auth_requirements_20251031.md
  → Issue #45 created

$ /gh:start 45
  → Issue読み込み → TodoWrite: 3 tasks loaded
  → 依存分析 → 並列実行プラン表示
  → 実装開始

# Task 1.1: JWT middleware実装
(作業中 - 完了ごとにGitHub自動更新)

# Task 1.2, 1.3も完了
→ 自動的にIssue #45 クローズ
→ 振り返り → claudedocs/learnings.md
```

### 例2: 複雑なリファクタリング（並列実装）

```bash
# Day 1: 分析とIssue作成
$ /gh:brainstorm
  「4つのevaluationスクリプトの共通化」
  → 対話的に要件整理
  → claudedocs/brainstorm/pipeline_commonization_requirements_20251031.md

$ /gh:issue create --from-file claudedocs/brainstorm/pipeline_commonization_requirements_20251031.md
  → Issue #42 created (3 tasks)

# Day 2: 並列実装
$ /gh:start 42
  → Issue読み込み → TodoWrite: 3 tasks
  → 依存分析:
    Group 1 (parallel): Task 1,2 ⚡
    Group 2 (sequential): Task 3

→ 並列実行で高速化
→ 自動的にIssue #42 クローズ
```

### 例3: セッション中断と再開

```bash
# Day 1
$ /gh:start 42
(Task 1.1, 1.2完了)
# セッション終了（checkpoint自動保存）

# Day 2
$ /gh:start
> Checkpoint found: issue_42_checkpoint
> Resuming work on Issue #42
> Progress: 2/3 tasks completed
> Next: Task 1.3

(Task 1.3完了)
→ 自動クローズ
```

---

## 📚 関連ドキュメント

- **詳細ガイド**: `docs/workflow/issue_work_recording.md`
- **Work directory**: `claudedocs/work/README.md`
- **ユースケース集**: `/gh:usage`
- **Serenaメモリ管理**: `/serena:reset`
- **Skills**: `.claude/skills/issue-work-logger/SKILL.md`

---

**Last Updated**: 2025-12-05
**Version**: 2.0.0
