# GitHub Issue駆動開発システム

壁打ち → Issue化 → 作業 → 完了を実現するClaude Code拡張機能

## 何ができるか

**シンプルなワークフロー**:
1. **壁打ち → Issue化**: `/gh:brainstorm`で要件整理 → `/gh:issue create`でGitHub Issue作成
2. **作業開始・継続**: `/gh:start 42`で作業開始、セッション再開も自動
3. **自動進捗同期**: TodoWrite完了 → GitHub自動更新 → 全完了でIssue自動クローズ

**なぜ使うか**:
- Issue駆動開発を自然な会話フローで実現
- TodoWriteで作業するだけでGitHub自動同期
- セッション間での作業継続性を確保
- 完了後の振り返りを自動記録

## クイックスタート

### 最小手順（3コマンド）

```bash
# 1. アイデアを整理（任意）
/gh:brainstorm "ユーザー認証機能"
# → 対話的に要件整理 → claudedocs/brainstorm/*.md に保存

# 2. Issue作成
/gh:issue create --from-file claudedocs/brainstorm/auth_requirements.md
# → GitHub Issue #42 作成完了

# 3. 作業開始
/gh:start 42
# → Issue読み込み → TodoWrite自動生成 → 実装開始
```

### セッション再開

```bash
# 翌日、別マシンから
/gh:start
# → checkpoint自動検出 → 前回の続きから再開
```

### 自動で起こること

**`/gh:start 42`実行時**:
1. Issue #42取得・タスクリスト解析
2. 未完了タスクのみTodoWriteに変換
3. checkpoint作成（Compact耐性）
4. 依存関係分析 → 並列実行プラン表示
5. 実装開始

**TodoWriteでタスク完了時**:
1. 完了を自動検知
2. GitHub Issue #42にコメント投稿（進捗%）
3. 全タスク完了時 → PR作成を提案（マージでIssue自動クローズ）

## コマンド一覧

### メインコマンド

| コマンド | 用途 | 例 |
|---------|------|-----|
| `/gh:issue create` | Issue作成 | `create "タイトル"` |
| `/gh:start 42` | 作業開始 | `start 42` |
| `/gh:start` | セッション再開 | checkpoint自動復元 |
| `/gh:issue close 42` | Issue完了 | `close 42` |

### 壁打ち・企画

| コマンド | 用途 | 例 |
|---------|------|-----|
| `/gh:brainstorm` | 対話的要件整理 | `brainstorm "新機能"` |
| `/gh:guide` | ワークフロー完全ガイド | `guide` |
| `/gh:usage` | ユースケース集 | `usage` |

### ログ分析・検証

| コマンド | 用途 | 例 |
|---------|------|-----|
| `/gh:verify <path>` | ログ分析・検証 | `verify /var/log/app.log` |
| `/gh:find-similar <target>` | 水平展開調査 | `find-similar src/auth/login.ts` |

### 廃止されたコマンド

以下は `gh` CLI を直接使用してください：

| 旧コマンド | 新しい方法 |
|-----------|-----------|
| `/gh:issue list` | `gh issue list --mine` |
| `/gh:issue view 42` | `gh issue view 42` |
| `/gh:issue work 42` | `/gh:start 42` |
| `/gh:issue status 42` | `gh issue view 42` |
| `/gh:issue sync 42` | 自動（/gh:start内） |

## アーキテクチャ概要

### コマンド責務

```
/gh:issue = Issueライフサイクル（作成・完了）
  ├── create  Issue作成
  └── close   Issue完了

/gh:start = 作業の全て
  ├── Issue読み込み・解析
  ├── TodoWrite変換
  ├── checkpoint管理
  ├── 依存分析・並列実行
  └── 進捗同期
```

### データフロー

```
GitHub Issue (SSOT・永続化)
    ↑↓ 同期
TodoWrite (セッション内キュー)
    ↑↓ 復元
Serena Memory (checkpoint)
```

### Skills

| Skill | 役割 | 呼び出し元 |
|-------|------|-----------|
| issue-parser | Issue解析 | /gh:start |
| issue-todowrite-sync | TodoWrite変換 | /gh:start |
| checkpoint-manager | 状態永続化 | /gh:start |
| progress-tracker | GitHub同期 | /gh:start |
| issue-retrospective | 振り返り | /gh:issue close |

## セッション管理

### 推奨パターン

```bash
# Session 1
/gh:issue create --from-file ...  # Issue #42 作成
/gh:start 42                       # 作業開始
# → Task 1, 2 完了
# （セッション終了）

# Session 2（翌日・別マシン）
/gh:start                          # checkpoint自動復元
# → Task 3, 4, 5 完了
# → 全完了 → Issue自動クローズ ✅
```

### Compact耐性

Claude Codeのコンテキストリセット（Compact）後も、`/gh:start` で自動復旧。

```bash
# Compact発生後
/gh:start
# → checkpoint検出 → GitHub照合 → TodoWrite再構築
# → 作業継続
```

## トラブルシューティング

### GitHub認証エラー
```bash
gh auth login
gh auth status  # 確認
```

### checkpointがない
```bash
/gh:start 42  # Issue番号を明示的に指定
```

### 複数のアクティブIssue
```bash
/gh:start
# → "複数のアクティブIssueが検出されました"
# → Issue番号を選択: /gh:start 42
```

## Tips

**💡 Tip 1**: `/gh:start 42` で作業開始、`/gh:start` で再開

**💡 Tip 2**: TodoWriteで作業するだけでGitHub自動更新

**💡 Tip 3**: `/gh:brainstorm` → `--from-file` が最強の壁打ちフロー

**💡 Tip 4**: Compact後も `/gh:start` で自動復旧

**💡 Tip 5**: 完了時の振り返りは自動記録（`claudedocs/learnings.md`）

## ファイル構成

```
.claude/
├── commands/gh/
│   ├── README.md (このファイル)
│   ├── issue.md (create/close)
│   ├── start.md (作業開始・継続)
│   ├── brainstorm.md (壁打ち)
│   ├── guide.md (詳細ガイド)
│   ├── usage.md (ユースケース)
│   ├── verify.md (ログ分析)
│   └── find-similar.md (類似パターン検索)
│
└── skills/
    ├── issue-parser/
    ├── issue-todowrite-sync/
    ├── checkpoint-manager/
    ├── progress-tracker/
    └── issue-retrospective/
```

---

**バージョン**: 2.1.0 (統合コマンド体系)
**最終更新**: 2025-12-05
