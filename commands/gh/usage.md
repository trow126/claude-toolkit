---
name: gh:usage
description: "GitHub Issue駆動開発の効率的な使い方パターンとシナリオ別ワークフロー例"
category: reference
complexity: basic
---

# /gh:usage - ユースケース集

Issue駆動開発システムの効率的な活用パターン集

---

## クイックリファレンス

### コマンド逆引き

| やりたいこと | コマンド |
|-------------|---------|
| アイデアを整理したい | `/gh:brainstorm "テーマ"` |
| Issueを作りたい | `/gh:issue create` |
| ファイルからIssue作成 | `/gh:issue create --from-file claudedocs/brainstorm/xxx.md` |
| Issueの作業を始めたい | `/gh:issue work 42` |
| タスクを実装したい | `/gh:start` |
| 進捗を確認したい | `/gh:issue status 42` |
| Issueを完了したい | `/gh:issue close 42` |
| 完全ガイドを見たい | `/gh:guide` |

---

## シナリオ別ワークフロー

### シナリオ1: 新機能の企画から実装まで（推奨フロー）

**状況**: 新しい機能のアイデアがあるが、詳細が固まっていない

```bash
# Step 1: アイデアを対話で整理
/gh:brainstorm "ユーザー認証機能を追加したい"
→ Claudeと対話して要件を明確化
→ claudedocs/brainstorm/user_auth_requirements_20251125.md に保存

# Step 2: 整理した要件からIssue作成
/gh:issue create --from-file claudedocs/brainstorm/user_auth_requirements_20251125.md
→ Issue #42 作成

# Step 3: 作業開始（TodoWrite同期）
/gh:issue work 42
→ 未完了タスクがTodoWriteに変換される

# Step 4: 実装
/gh:start
→ 依存関係分析 → 並列実行プラン → 実装
→ 完了ごとにGitHub自動更新

# 全タスク完了時
→ Issue自動クローズ + 振り返り記録
```

**ポイント**:
- `brainstorm → create → work → start` の流れが最も効率的
- brainstormファイルは対応Issueクローズ時に自動削除

---

### シナリオ2: 既存Issueから作業開始

**状況**: すでにGitHub Issueが存在する（他者作成/過去作成）

```bash
# Issue確認
/gh:issue view 42

# 作業開始（未完了タスクのみTodoWrite化）
/gh:issue work 42

# 実装
/gh:start
```

**ポイント**:
- `[x]`でマークされた完了タスクは自動除外
- 途中参加でも未完了分だけ作業可能

---

### シナリオ3: セッション中断と再開

**状況**: 作業途中でセッション終了、翌日再開

```bash
# Day 1: 途中まで作業
/gh:issue work 42
/gh:start  # Task 1,2完了
# セッション終了

# Day 2: 再開
/gh:start
→ GitHubから最新状態を自動取得
→ 未完了Task 3,4,5がTodoWriteに復元
→ Task 3から再開
```

**ポイント**:
- `/gh:start`再実行だけで前回の続きから再開
- GitHub Issueが唯一の真実（Single Source of Truth）

---

### シナリオ4: 大量タスクの段階的実行

**状況**: 15タスク以上の大きなIssue

```bash
# Phase単位で作業
/gh:issue work 42 --current-phase "Phase 1"
/gh:start
→ Phase 1のタスクのみTodoWriteに変換

# Phase 1完了後、次のPhaseへ
/gh:issue work 42 --current-phase "Phase 2"
/gh:start
```

**代替案**:
```bash
# 特定タスクのみ指定
/gh:start 1,2,3
→ Task 1,2,3のみ実行

# 全タスク強制実行
/gh:start --all
```

---

### シナリオ5: 並列実装で高速化

**状況**: 独立したタスクを並列実行したい

```bash
/gh:start
→ 自動的に依存関係を分析

出力例:
📋 Parallel Execution Plan:
Group 1 (sequential): Task 1 "Database setup"
Group 2 (parallel):   Task 2,3 "API endpoints" ⚡
Group 3 (parallel):   Task 4,5 "UI components" ⚡
Group 4 (sequential): Task 6 "E2E tests"

⚡ Estimated speedup: 50%

→ 並列可能なタスクは自動的に並列実行
```

**強制並列（依存関係無視）**:
```bash
/gh:start 2,3,4 --parallel
# ⚠️ 依存関係違反リスクあり
```

---

### シナリオ6: バグ修正の水平展開

**状況**: バグを修正したが、同じ問題が他にもありそう

```bash
# バグ修正後に類似箇所を調査
/gh:find-similar "nullチェック追加"
→ 同一パターンの潜在的バグ箇所をリスト化

# 検出結果からIssue作成
/gh:find-similar "nullチェック追加" --create-issue
→ 水平展開タスクを含むIssue自動作成
```

---

### シナリオ7: リファクタリング影響調査

**状況**: 関数名を変更したい、影響範囲を把握したい

```bash
# 影響範囲を調査
/gh:find-similar --symbol validateUser --scope project

出力例:
## 📊 概要
- 検出箇所: 23件
- 直接呼び出し: 15件
- 間接参照: 8件

## 🎯 影響範囲マップ
- src/auth/: 8箇所（高優先度）
- src/api/: 10箇所（中優先度）
- tests/: 5箇所（テスト）
```

---

## Tips & Tricks

### 💡 効率化Tips

**Tip 1: 最短ルート**
```bash
# アイデアが明確な場合はbrainstormスキップ可
/gh:issue create "バグ修正: ログインエラー" "## Tasks\n- [ ] Task 1"
```

**Tip 2: Issue分割の目安**
- 5-8タスク: 最適（1-3日で完了）
- 12+タスク: 分割推奨
- 15+タスク: 必ず分割

**Tip 3: commit連携**
```bash
/sc:git commit "feat: 認証機能追加 (#42)"
# Issue番号を含めると自動リンク
```

**Tip 4: 進捗の手動同期**
```bash
/gh:issue sync 42
# 自動同期が失敗した場合の手動フォールバック
```

**Tip 5: 振り返りスキップ**
```bash
/gh:issue close 42 --no-retro
# 小さなバグ修正など、振り返り不要な場合
```

### ⚠️ よくある間違い

**間違い1: brainstormファイルをコミット**
```bash
# ❌ claudedocs/brainstorm/ は一時ファイル
# ✅ .gitignoreで除外済み、Issue作成後に自動削除
```

**間違い2: TodoWrite状態を永続化と勘違い**
```bash
# ❌ TodoWriteはセッション揮発
# ✅ GitHub Issueが永続化層、/gh:startで復元可能
```

**間違い3: 手動でGitHub Issue編集**
```bash
# ❌ 手動編集すると同期ずれのリスク
# ✅ コマンド経由で操作、自動同期に任せる
```

---

## コマンド組み合わせパターン

### パターンA: 壁打ち → 実装完了（フルフロー）
```
/gh:brainstorm → /gh:issue create --from-file → /gh:issue work → /gh:start → 自動クローズ
```

### パターンB: 既存Issue → 実装（ショートカット）
```
/gh:issue work 42 → /gh:start → 自動クローズ
```

### パターンC: 調査 → Issue化 → 実装
```
/gh:find-similar → /gh:find-similar --create-issue → /gh:issue work → /gh:start
```

### パターンD: 並列実装（高速化）
```
/gh:issue work 42 → /gh:start (自動並列判断) → 並列実行
```

---

## トラブルシューティング

### Q: TodoWriteが空で/gh:startが動かない
```bash
# A: 先に/gh:issue workを実行
/gh:issue work 42
/gh:start
```

### Q: 進捗がGitHubに反映されない
```bash
# A: 手動同期を試す
/gh:issue sync 42
```

### Q: セッション再開時に前回の状態がない
```bash
# A: これは正常動作。/gh:startで復元
/gh:start
# GitHubから最新状態を取得してTodoWrite再構築
```

### Q: 大量タスクで警告が出る
```bash
# A: Phase単位または特定タスクで実行
/gh:issue work 42 --current-phase "Phase 1"
# または
/gh:start 1,2,3,4,5
```

---

## 関連コマンド

| コマンド | 用途 |
|---------|------|
| `/gh:brainstorm` | 要件整理（壁打ち） |
| `/gh:issue` | Issue管理（create/work/close等） |
| `/gh:start` | タスク実装開始 |
| `/gh:find-similar` | 類似パターン検索 |
| `/gh:guide` | 完全ワークフローガイド |
| `/sc:spawn` | 並列実装（SuperClaude連携） |
| `/sc:task` | 複雑タスク実装（SuperClaude連携） |

---

**Last Updated**: 2025-11-25
**Version**: 1.1.0
