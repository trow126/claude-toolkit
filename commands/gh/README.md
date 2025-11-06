# GitHub Issue駆動開発システム

壁打ち → Issue化 → タスク化 → 進捗管理を実現するClaude Code拡張機能

## 📁 構成

### スラッシュコマンド
```
.claude/commands/gh/
└── issue.md          # /gh:issue コマンド
```

### Skills（自動起動）
```
.claude/skills/
├── issue-parser/
│   ├── SKILL.md
│   └── scripts/parse_issue.py
│
├── issue-todowrite-sync/
│   ├── SKILL.md
│   └── scripts/
│       ├── convert_to_todowrite.py
│       └── sync_progress.py
│
└── progress-tracker/
    └── SKILL.md
```

## 🚀 基本的な使い方

### 1. Issueで作業開始

```bash
/gh:issue work 42
```

**何が起こるか**:
1. `issue-parser` skill が自動起動 → Issue #42を解析
2. `issue-todowrite-sync` skill が自動起動 → TodoWriteタスクに変換
3. `progress-tracker` skill がバックグラウンドで監視開始

**結果**:
```
Started work on Issue #42: Feature: User Authentication

TodoWrite Tasks Created:
✓ 1. API実装
✓ 2. Frontend components
⏳ 3. Database schema

Total: 3 tasks
Progress tracking enabled.
```

### 2. タスク作業

TodoWriteでタスクを完了させるだけ！

```
(TodoWriteでタスク #1 "API実装" を完了)
```

**自動実行**:
- `progress-tracker` が完了を検知
- GitHub Issue #42 にコメント投稿:
  ```
  ✅ Task Completed: API実装
  Progress: 1/3 tasks (33.3%)
  ```

### 3. 進捗確認

```bash
/gh:issue status 42
```

**表示**:
```
Issue #42: Feature: User Authentication

Progress: 1/3 tasks (33.3%)

✅ API実装 (completed)
🔄 Frontend components (in progress)
⏳ Database schema (pending)

Last synced: 2025-10-30 12:30:45
```

### 4. 全タスク完了時

最後のタスクを完了すると:

**自動実行**:
- `progress-tracker` が全完了を検知
- GitHub Issue #42 にコメント投稿: "🎉 All tasks completed!"
- Issue #42 を自動クローズ（`reason: completed`）

## 🔄 完全なワークフロー例

### シナリオ: 新機能開発

```bash
# ステップ1: アイデアを壁打ち
/gh:brainstorm "ユーザー認証機能"
→ 対話的に要件整理
→ ファイル保存: claudedocs/brainstorm/jwt_auth_requirements_20251031.md

# ステップ2: Issue作成
/gh:issue create --from-file claudedocs/brainstorm/jwt_auth_requirements_20251031.md
→ Issue #42 作成

# ステップ3: 作業開始
/gh:issue work 42
→ TodoWrite タスク作成
→ 進捗追跡有効化

# ステップ4: 実装作業
(TodoWriteでタスクを完了していく)
→ 自動的にGitHub更新

# ステップ5: 完了
(最後のタスク完了)
→ Issue自動クローズ ✅
```

## 📋 全コマンド一覧

### Issue作成
```bash
/gh:issue create "タイトル"
/gh:issue create --from-file claudedocs/brainstorm/feature_requirements_20251031.md
/gh:issue create --interactive
```

### Issue表示
```bash
/gh:issue list                    # 開いているIssue一覧
/gh:issue list --mine             # 自分のIssue
/gh:issue list --state all        # 全Issue
/gh:issue view 42                 # Issue詳細
/gh:issue view 42 --with-todos    # TodoWrite状態も表示
```

### Issue作業
```bash
/gh:issue work 42                 # 作業開始
/gh:issue work 42 --no-auto-close # 自動クローズ無効
/gh:issue status 42               # 進捗確認
/gh:issue sync 42                 # 手動同期
/gh:issue sync --all              # 全Issue同期
/gh:issue close 42                # Issue完了
```

## 🤖 Skills実行アーキテクチャ

コマンドは**Task toolでagentに委譲**され、agent内でSkillsが起動されます：

```
/gh:issue work 42
  ↓
Task tool → general-purpose agent
  ↓
Agent内でSkills実行:
  1. issue-parser skill
  2. issue-todowrite-sync skill
  3. progress-tracker skill
  4. issue-retrospective skill (closeコマンド時)
```

### issue-parser
**起動方法**: Agent内で明示的に起動

**機能**:
- Issue本文 + コメントのMarkdown解析
- コメントから最新進捗を確認
- タスクリスト（`- [ ]` / `- [x]`）抽出
- 完了済みタスク（[x]）を識別
- フェーズ（`##`見出し）認識

### issue-todowrite-sync
**起動方法**: Agent内で明示的に起動

**機能**:
- Issue → TodoWrite変換（未完了タスクのみ）
- 完了済みタスク（[x]）を自動除外
- TodoWrite → GitHub同期
- セッション内で状態管理

### progress-tracker
**起動方法**: Agent内で明示的に起動

**機能**:
- TodoWrite完了検知
- GitHub進捗コメント投稿
- 全完了時のIssue自動クローズ

### issue-retrospective
**起動方法**: `close`コマンド実行時に自動起動（`--no-retro`でスキップ可能）

**機能**:
- Issue完了後の学習抽出
- タイムライン、成功パターン、課題を分析
- 振り返りを記録:
  - **GitHub Issue comment**: 構造化された振り返りコメント
  - **claudedocs/learnings.md**: プロジェクト全体の知見蓄積
- 継続的改善サイクルを実現

## 📝 セッション内での作業

最適なワークフローは1セッション内での完結です：

```bash
# 同一セッション内での完結（推奨）
/gh:issue work 42
(全タスク完了)
→ 自動的にIssue更新・クローズ

# セッション間で中断・再開する場合
# セッション1
/gh:issue work 42
(2タスク完了、セッション終了)

# セッション2（別の日）
/gh:issue work 42  # 再実行でGitHubから最新状態取得
→ 残りタスクがTodoWriteに復元される
(残りのタスクを完了)
→ 自動的にIssue更新・クローズ
```

## ⚙️ 設定オプション

### 自動クローズを無効化
```bash
/gh:issue work 42 --no-auto-close
```

### 明示的Skill呼び出し
```bash
"issue-parser skillを使ってIssue #42を詳細分析して"
"issue-todowrite-sync skillでIssue #42を同期"
```

## 🔧 トラブルシューティング

### GitHub CLI認証エラー
```bash
gh auth login
```

### Skillsが起動しない
- Skills名を明示的に言及: "use issue-parser skill"
- コマンド再実行: `/gh:issue work 42`

### 進捗が同期されない
```bash
/gh:issue sync 42              # 手動同期
/gh:issue status 42 --refresh  # 強制更新
```

## 📚 詳細ドキュメント

- **コマンド詳細**: `.claude/commands/gh/issue.md`
- **issue-parser**: `.claude/skills/issue-parser/SKILL.md`
- **issue-todowrite-sync**: `.claude/skills/issue-todowrite-sync/SKILL.md`
- **progress-tracker**: `.claude/skills/progress-tracker/SKILL.md`

## 🎯 Tips

💡 **Tip 1**: `/gh:issue work <number>` だけで全て自動セットアップ

💡 **Tip 2**: TodoWriteで作業するだけでGitHubが自動更新される

💡 **Tip 3**: `/gh:brainstorm` → `/gh:issue create --from-file` が最強の組み合わせ

💡 **Tip 4**: セッション内で作業完結が最も効率的

💡 **Tip 5**: Task toolがagentに委譲 - 複雑な操作も自動処理

💡 **Tip 6**: `work`はコメントも確認 - GitHubの最新進捗を自動反映

💡 **Tip 7**: 完了済みタスク（[x]）はTodoWriteから自動除外 - 未完了のみ作業

💡 **Tip 8**: Agent内でSkills順次実行 - issue-parser → issue-todowrite-sync → progress-tracker

💡 **Tip 9**: `close`で自動振り返り - 学習がGitHub + `claudedocs/learnings.md` に記録され、次のIssueに活かされる

## 🏗️ アーキテクチャ

```
┌─────────────────────┐
│  /gh:issue work 42  │  ← ユーザー操作
│  (スラッシュコマンド)│
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────┐
│  Task Tool               │  ← 複雑な操作を委譲（>3 steps）
│  (Agent Orchestration)   │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────────┐
│  general-purpose Agent       │
│                              │
│  ┌─────────────────────┐    │
│  │ issue-parser skill  │    │
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
           ▼
┌──────────────────────────┐
│  GitHub Issues           │
│  TodoWrite               │
│  Session Context         │
└──────────────────────────┘
```

---

**実装完了日**: 2025-10-30
**バージョン**: 1.0.0
**動作確認**: 要テスト
