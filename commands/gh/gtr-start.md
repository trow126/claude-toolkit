---
name: gh:gtr-start
description: Git Worktree + GitHub Issue駆動開発の統合エントリーポイント。ワークツリー作成からIssue作業開始まで一貫して実行。
---

# /gh:gtr-start - Git Worktree統合ワークフロー

> **核心**: 独立したワークツリーでIssue作業を行い、並列開発とコンテキスト分離を実現

## Triggers
- Issue作業を独立したワークツリーで開始したい
- 複数Issue並列作業が必要
- メインブランチを汚さずに作業したい

## Usage

```bash
# ターミナルから（推奨・シームレスUX）
gtr-start 42

# Claude Code内から（このコマンド）
/gh:gtr-start 42
```

## Behavioral Flow

### Phase 0: 環境検出

```yaml
1. 現在のディレクトリ/ブランチを確認:
   git rev-parse --abbrev-ref HEAD

2. 分岐:
   a. ワークツリー内（issue-* ブランチ）:
      → Issue番号を抽出
      → /gh:start に委譲
      → "✅ Already in worktree issue-42, running /gh:start 42"

   b. メインリポジトリ:
      → Phase 1 へ進む
```

### Phase 1: ワークツリー作成

```yaml
3. Issue番号の確認:
   - 引数あり → その番号を使用
   - 引数なし → エラー表示

4. ワークツリー存在チェック:
   git worktree list | grep issue-<number>

   存在する場合:
   → "✅ Worktree already exists"
   → Phase 2 へ

   存在しない場合:
   → git gtr new issue-<number>
   → postCreate hook実行（uv sync + symlink）

5. ワークツリーパス確認:
   - デフォルト: ../sample-ml-project-worktrees/issue-<number>
```

### Phase 2: 次のステップ案内

```yaml
6. Claude Code内での制約:
   - ディレクトリ変更不可（セッション固定）
   - 新セッション起動が必要

7. ユーザーへの案内:
   "✅ Worktree created: ~/sample-ml-project-worktrees/issue-42

   📋 Next Steps:

   Option A (推奨): ターミナルで実行
   $ gtr-start 42
   → ワークツリーでClaude Code自動起動 + /gh:start 42実行

   Option B: 手動で移動
   $ cd ~/sample-ml-project-worktrees/issue-42
   $ claude "/gh:start 42"

   Option C: git gtr使用
   $ git gtr ai issue-42
   → 新セッションで /gh:start 42 を手動実行"
```

## Real-World Workflow

### シナリオ1: ターミナルからの作業開始（推奨）

```bash
# ターミナルで
$ gtr-start 42
→ ワークツリー作成
→ Claude Code起動
→ /gh:start 42 自動実行
→ Issue作業開始
```

### シナリオ2: Claude Code内からの作業開始

```bash
# メインリポジトリのClaude Codeセッション内
/gh:gtr-start 42
→ ワークツリー作成
→ 案内表示「gtr-start 42を実行してください」
→ このセッション終了
→ ターミナルでgtr-start 42
```

### シナリオ3: 既存ワークツリーでの再開

```bash
# ワークツリー内のClaude Codeセッション
/gh:gtr-start
→ ブランチからIssue番号検出
→ /gh:start 42 に自動委譲
```

## Options

```bash
--force     # 既存ワークツリーを削除して再作成
--no-ai     # ワークツリー作成のみ（Claude Code起動しない）
```

## Error Handling

```bash
# Issue番号未指定
→ エラー「Issue番号を指定してください: /gh:gtr-start 42」

# ワークツリー作成失敗
→ git gtr エラーメッセージを表示
→ 手動作成コマンドを案内

# git-worktree-runner未インストール
→ エラー「git gtr が見つかりません」
→ インストール手順を案内
```

## Integration Points

```yaml
git-worktree-runner:
  - git gtr new: ワークツリー作成
  - postCreate hook: uv sync + symlink

/gh:start:
  - ワークツリー内でIssue作業を開始
  - checkpoint管理、TodoWrite、GitHub同期

gtr-start (shell script):
  - ターミナルからのシームレス起動
  - ~/.local/bin/gtr-start
```

## Boundaries

### Will Do ✅
- ワークツリー作成
- 次のステップ案内
- ワークツリー内検出時の/gh:start委譲

### Will Not Do ❌
- Claude Code内でのディレクトリ変更（技術的制約）
- メインセッションから直接ワークツリーで作業

## 実行指示

**あなたは今、`/gh:gtr-start` コマンドを実行しています。**

### 実行フロー

```yaml
1. 環境検出:
   - git rev-parse --abbrev-ref HEAD でブランチ名取得
   - issue-* パターンマッチでワークツリー判定

2. ワークツリー内の場合:
   - Issue番号抽出（issue-42 → 42）
   - /gh:start <number> を実行
   - 完了

3. メインリポジトリの場合:
   a. 引数からIssue番号取得
   b. ワークツリー存在チェック
   c. 存在しない → git gtr new issue-<number>
   d. 存在する → スキップ
   e. 次のステップ案内を表示:
      - gtr-start コマンドの推奨
      - 手動移動オプション
```

### 出力フォーマット

```markdown
✅ Worktree ready: ~/sample-ml-project-worktrees/issue-42

📋 **Next Steps** (choose one):

**Option A** (推奨 - シームレスUX):
\`\`\`bash
gtr-start 42
\`\`\`

**Option B** (手動):
\`\`\`bash
cd ~/sample-ml-project-worktrees/issue-42
claude "/gh:start 42"
\`\`\`

**Option C** (git gtr使用):
\`\`\`bash
git gtr ai issue-42
# 新セッションで: /gh:start 42
\`\`\`
```

## Related Commands

```bash
gtr-start <number>      # ターミナルからの統合起動（推奨）
/gh:start <number>      # Issue作業開始
/gh:issue create        # Issue作成
git gtr new <name>      # ワークツリー作成のみ
git gtr rm <name>       # ワークツリー削除
git gtr list            # ワークツリー一覧
```

## Tips

💡 **ターミナル推奨**: `gtr-start 42` が最もシームレスなUX
💡 **並列作業**: 複数ワークツリーで複数Issue同時作業可能
💡 **データ共有**: symlink で data/, models/ は自動共有
💡 **完了後**: `git gtr rm issue-42` でワークツリー削除

---

**Last Updated**: 2025-12-16
**Version**: 1.0.0
