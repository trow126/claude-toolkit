---
name: issue
description: TodoWrite連携によるGitHub Issue駆動開発ワークフロー。Issueの管理、タスク変換、進捗追跡、双方向同期を実現。
category: workflow
complexity: standard
---

# GitHub Issue管理コマンド

TodoWrite自動連携と進捗追跡機能を持つ包括的なGitHub Issueワークフロー

## 利用可能なコマンド

### create - 新しいIssueを作成

複数の入力方法でGitHub Issueを作成します。

#### 使い方
```bash
# 基本的な作成
/gh:issue create "Feature: User Authentication"

# ファイルから作成
/gh:issue create --from-file ClaudeDocs/brainstorm/auth-requirements.md

# セッションメモリから作成（brainstorm後など）
/gh:issue create --from-memory brainstorm_auth

# 対話的に作成
/gh:issue create --interactive
```

#### 処理フロー
1. **Issue詳細の収集**
   - タイトル（必須）
   - 本文・説明
   - ラベル（任意）
   - 担当者（任意）

2. **GitHubに作成**
   ```bash
   gh issue create \
     --title "Feature: User Authentication" \
     --body "$(cat issue_body.md)" \
     --label "feature,high-priority" \
     --assignee "@me"
   ```

3. **セッションコンテキストにメタデータ保存**
   Issueメタデータをセッションコンテキストに保存（セッション内での参照用）

4. **結果を表示**
   Issue番号とURLを表示

#### オプション

**`--from-file <path>`**
- **説明**: 指定したファイルの内容をIssue本文として使用します
- **用途**: Markdownファイルや要件定義書からIssueを作成する場合に便利
- **例**: `/gh:issue create "Feature: Auth" --from-file docs/auth-spec.md`

**`--from-memory <key>`**
- **説明**: セッションメモリに保存されたコンテンツをIssue本文として使用します
- **用途**: `/sc:brainstorm`の結果や過去のメモからIssueを作成する場合
- **例**: `/gh:issue create "New Feature" --from-memory brainstorm_auth`

**`--interactive`**
- **説明**: タイトル、本文、ラベル、担当者などを対話的に入力します
- **用途**: 複数の詳細情報を段階的に入力したい場合
- **例**: `/gh:issue create --interactive`（全て対話形式で入力）

**`--label <labels>`**
- **説明**: Issueにラベルを付与します（カンマ区切りで複数指定可能）
- **用途**: Issueの分類や優先度を明示的に設定する場合
- **例**: `/gh:issue create "Bug fix" --label bug,urgent,backend`

**`--assignee <user>`**
- **説明**: Issueを特定のユーザーに割り当てます（`@me`で自分に割り当て）
- **用途**: 作業担当者を明確にする場合
- **例**: `/gh:issue create "Task" --assignee @me`（自分に割り当て）
- **例**: `/gh:issue create "Task" --assignee username`（特定ユーザーに割り当て）

---

### list - Issue一覧表示

フィルタリングされたGitHub Issue一覧を表示します。

#### 使い方
```bash
# 開いているIssueを表示（デフォルト）
/gh:issue list

# 全てのIssueを表示
/gh:issue list --state all

# ラベルでフィルタ
/gh:issue list --label feature

# 自分に割り当てられたIssue
/gh:issue list --mine

# クローズ済みIssue
/gh:issue list --state closed
```

#### 処理フロー
1. **GitHubからIssueを取得**
   ```bash
   gh issue list \
     --state <state> \
     --label <label> \
     --assignee <assignee> \
     --json number,title,labels,state,url \
     --limit 20
   ```

2. **表示用にフォーマット**
   ```
   Open Issues:
   #42  Feature: User Authentication        [feature, high-priority]
   #43  Fix: Login timeout                  [bug, urgent]
   #44  Docs: API reference update          [documentation]
   ```

3. **セッションコンテキストから読み込み**
   TodoWriteタスクがアクティブなIssueを表示

#### オプション

**`--state <open|closed|all>`**
- **説明**: Issue状態でフィルタリングします
- **用途**: 特定の状態のIssueのみを表示したい場合
- **デフォルト**: `open`（開いているIssueのみ）
- **例**: `/gh:issue list --state all`（全てのIssue）
- **例**: `/gh:issue list --state closed`（クローズ済みIssue）

**`--label <label>`**
- **説明**: 指定したラベルを持つIssueのみを表示します
- **用途**: 特定のカテゴリやタグでIssueを絞り込む場合
- **例**: `/gh:issue list --label bug`（bugラベルのIssueのみ）
- **例**: `/gh:issue list --label feature,high-priority`（複数ラベルで絞り込み）

**`--assignee <user>`**
- **説明**: 指定したユーザーに割り当てられたIssueのみを表示します
- **用途**: 特定の担当者のタスクを確認する場合
- **例**: `/gh:issue list --assignee @me`（自分に割り当てられたIssue）
- **例**: `/gh:issue list --assignee username`（特定ユーザーのIssue）

**`--mine`**
- **説明**: 自分に割り当てられた開いているIssueを表示します
- **用途**: 自分のタスク一覧を素早く確認する場合
- **実質的な意味**: `--assignee @me --state open` の短縮形
- **例**: `/gh:issue list --mine`

**`--limit <n>`**
- **説明**: 表示するIssue数を制限します
- **用途**: 大量のIssueがある場合に表示数を絞る
- **デフォルト**: `20`
- **例**: `/gh:issue list --limit 10`（最新10件のみ表示）
- **例**: `/gh:issue list --limit 50`（最新50件まで表示）

---

### view - Issue詳細表示

Issueの詳細情報を表示します。

#### 使い方
```bash
# 基本的な表示
/gh:issue view 42

# 詳細表示（コメント含む）
/gh:issue view 42 --detailed

# TodoWrite状態も表示
/gh:issue view 42 --with-todos
```

#### 処理フロー
1. **Issueデータを取得**
   ```bash
   gh issue view 42 --json number,title,body,labels,state,url,comments
   ```

2. **フォーマットして表示**
   ```
   Issue #42: Feature: User Authentication
   State: open
   URL: https://github.com/user/repo/issues/42
   Labels: feature, high-priority

   Description:
   [Issue body content]

   Tasks:
   - [ ] API implementation
   - [ ] Frontend components
   - [x] Database schema

   Progress: 1/3 tasks (33.3%)
   ```

3. **TodoWrite状態を確認**
   `--with-todos`指定時、セッションコンテキストから読み取りTodoWrite同期状態を表示

#### オプション

**`--detailed`**
- **説明**: コメント履歴と詳細情報を含めて表示します
- **用途**: Issueの全コンテキストを確認したい場合
- **含まれる情報**: Issue本文、コメント、更新履歴、参加者
- **例**: `/gh:issue view 42 --detailed`

**`--with-todos`**
- **説明**: TodoWrite同期状態も合わせて表示します
- **用途**: `/gh:issue work`でTodoWriteに変換済みのIssueの進捗を確認する場合
- **含まれる情報**: TodoWriteタスクの完了状況、進捗率、最終同期時刻
- **例**: `/gh:issue view 42 --with-todos`
- **備考**: TodoWrite連携していないIssueでは追加情報なし

---

### work - Issue作業開始

IssueをTodoWriteタスクに変換して追跡を開始します。

**このコマンドがSkillsを起動するメインコマンドです！**

#### 使い方
```bash
# Issueの作業を開始
/gh:issue work 42

# 自動クローズなしで作業
/gh:issue work 42 --no-auto-close

# 特定フェーズのみ変換
/gh:issue work 42 --phase "Phase 1"
```

#### 処理フロー

**ステップ1: Issueを解析**（`issue-parser` skillを使用）
```
→ issue-parser skillを自動起動
→ GitHub からIssue #42のデータを取得
→ タスク、フェーズ、メタデータを抽出
```

**ステップ2: TodoWriteに変換**（`issue-todowrite-sync` skillを使用）
```
→ issue-todowrite-sync skillを自動起動
→ 解析済みタスクをTodoWrite形式に変換
→ 各タスクのactiveFormを生成
→ TodoWriteタスクを作成
```

**ステップ3: セッションコンテキストにマッピング保存**
Issue-TodoWriteマッピングをセッションコンテキストに保存（セッション内での追跡用）

**ステップ4: TodoWriteタスクを表示**
```
Issue #42の作業を開始しました: Feature: User Authentication

TodoWriteタスクを作成:
✓ 1. API実装
✓ 2. Frontend components
⏳ 3. Database schema (completed)

合計: 3タスク
完了: 1タスク (33.3%)
未完: 2タスク

進捗追跡が有効化されました。全タスク完了時にIssueは自動クローズされます。
```

**バックグラウンド: 進捗トラッカー起動**（`progress-tracker` skillを使用）
```
→ progress-tracker skillがTodoWriteを監視開始
→ タスク完了時に自動的にコメント投稿
→ 全タスク完了時にIssueを自動クローズ（有効時）
```

#### オプション

**`--no-auto-close`**
- **説明**: 全タスク完了時の自動Issueクローズを無効化します
- **用途**: タスク完了後も手動でクローズしたい場合や、追加作業が発生する可能性がある場合
- **デフォルト動作**: 有効化されていない（全タスク完了時に自動クローズ）
- **例**: `/gh:issue work 42 --no-auto-close`
- **備考**: 手動で `/gh:issue close 42` を実行する必要があります

**`--phase <name>`**
- **説明**: 特定のフェーズ（見出し）のタスクのみをTodoWriteに変換します
- **用途**: 大きなIssueを段階的に進める場合や、特定パートだけ作業したい場合
- **フェーズの定義**: Issue本文内の `## Phase 1` のような見出しで区切られたセクション
- **例**: `/gh:issue work 42 --phase "Phase 1: Backend"`
- **例**: `/gh:issue work 42 --phase "Frontend"`（部分一致で検索）
- **備考**: 指定したフェーズのタスクのみがTodoWriteに追加されます

**`--refresh`**
- **説明**: GitHubの最新状態と同期してTodoWriteを更新します
- **用途**: Issueが外部で更新された場合や、同期が古くなった場合
- **動作**:
  - GitHubから最新のIssue内容を取得
  - 既存のTodoWriteタスクと比較
  - 差分があれば TodoWrite を更新
- **例**: `/gh:issue work 42 --refresh`
- **備考**: 既存の進捗状態は可能な限り保持されます

---

### status - Issue進捗表示

TodoWriteタスクを持つIssueの現在の進捗を表示します。

#### 使い方
```bash
# 進捗を表示
/gh:issue status 42

# GitHubから強制更新
/gh:issue status 42 --refresh
```

#### 処理フロー
1. **セッションコンテキストから読み取り**
   Issue-TodoWriteマッピングをセッションコンテキストから取得

2. **現在のTodoWrite状態を取得**
   現在のTodoWriteタスクとその状態を読み取り

3. **進捗を表示**
   ```
   Issue #42: Feature: User Authentication

   進捗: 2/3タスク (66.7%)

   ✅ API実装 (completed)
   ✅ Frontend components (completed)
   🔄 Database schema (in progress)

   最終同期: 2025-10-30 12:30:45
   GitHub Issue: https://github.com/user/repo/issues/42
   ```

#### オプション

**`--refresh`**
- **説明**: GitHubの最新状態と同期してから進捗を表示します
- **用途**: Issueが外部で更新された可能性がある場合や、最新の状態を確認したい場合
- **動作**:
  - GitHubから最新のIssue状態を取得
  - セッションコンテキストの情報を更新
  - 最新の進捗状態を表示
- **例**: `/gh:issue status 42 --refresh`
- **備考**: 通常はセッションコンテキストの情報のみ表示（高速）

---

### sync - 進捗をGitHubに同期

TodoWriteの進捗を手動でGitHub Issueに同期します。

#### 使い方
```bash
# 特定のIssueを同期
/gh:issue sync 42

# 全アクティブIssueを同期
/gh:issue sync --all
```

#### 処理フロー
**`issue-todowrite-sync` skillを使用:**

1. **セッションコンテキストからマッピングを読み取り**
   Issue-TodoWriteマッピングをセッションコンテキストから取得

2. **進捗を計算**
   - 完了 vs 未完TodoWriteタスクをカウント
   - 前回同期からの変更を判定

3. **GitHubを更新**
   ```bash
   gh issue comment 42 --body "✅ 進捗更新: 2/3タスク (66.7%)"
   ```

4. **セッションコンテキストを更新**
   最終同期時刻などのメタデータをセッションコンテキストに保存

#### オプション

**`--all`**
- **説明**: アクティブなTodoWriteタスクを持つ全Issueを一括同期します
- **用途**: 複数のIssueで作業している場合に、全ての進捗を一度にGitHubに反映する
- **動作**:
  - セッションコンテキストから全アクティブIssueマッピングを取得
  - 各IssueのTodoWrite進捗を確認
  - 変更があったIssueのみをGitHubに同期
- **例**: `/gh:issue sync --all`
- **出力**: 同期したIssue一覧と各進捗率

**`--force`**
- **説明**: 変更の有無に関わらず強制的に同期します
- **用途**: 同期状態が不明な場合や、GitHubのコメントを再投稿したい場合
- **動作**:
  - 前回同期からの変更チェックをスキップ
  - 現在の進捗を必ずGitHubに投稿
- **例**: `/gh:issue sync 42 --force`
- **例**: `/gh:issue sync --all --force`（全Issue強制同期）
- **備考**: GitHubに重複コメントが投稿される可能性があります

---

### close - Issueを完了してクローズ

完了サマリーと共にIssueをクローズします。

#### 使い方
```bash
# Issueをクローズ
/gh:issue close 42

# 理由を指定してクローズ
/gh:issue close 42 --reason "completed"

# コメントなしでクローズ
/gh:issue close 42 --quiet
```

#### 処理フロー
1. **完了サマリーを生成**
   - セッションコンテキストからTodoWrite進捗を読み取り
   - サマリーコメントを生成

2. **最終コメントを投稿**
   ```bash
   gh issue comment 42 --body "🎉 Issue完了。全タスク完了しました。"
   ```

3. **Issueをクローズ**
   ```bash
   gh issue close 42 --reason completed
   ```

4. **セッションコンテキストをクリーンアップ**
   Issue-TodoWriteマッピングをセッションコンテキストから削除

#### オプション

**`--reason <completed|not_planned|duplicate>`**
- **説明**: Issueをクローズする理由を指定します
- **用途**: GitHubでクローズ理由を明確にする場合
- **選択肢**:
  - `completed`: 作業完了（デフォルト）
  - `not_planned`: 予定外・実施しない
  - `duplicate`: 重複Issue
- **例**: `/gh:issue close 42 --reason completed`（作業完了）
- **例**: `/gh:issue close 42 --reason not_planned`（実施しない）
- **例**: `/gh:issue close 42 --reason duplicate`（重複）
- **デフォルト**: `completed`

**`--quiet`**
- **説明**: 完了サマリーコメントを投稿せずに静かにクローズします
- **用途**: 自動クローズ時やコメント不要の場合
- **動作**:
  - 完了サマリーコメントをスキップ
  - Issueをクローズ
  - セッションコンテキストをクリーンアップ
- **例**: `/gh:issue close 42 --quiet`
- **備考**: GitHubには「Closed」のみが記録されます

---

## Skills連携

このコマンドは3つのSkillsとシームレスに連携します：

### 1. issue-parser
**自動起動タイミング**: Issue内容の解析が必要な時

**機能**:
- GitHubからIssueを取得
- タスク、フェーズ、メタデータを抽出
- 構造化JSONを返す

**呼び出し元**: `create`, `work`, `view`

### 2. issue-todowrite-sync
**自動起動タイミング**: タスクの変換または同期時

**機能**:
- Issue → TodoWrite変換
- TodoWrite → GitHub同期
- セッションコンテキストでマッピングを維持

**呼び出し元**: `work`, `sync`, `status`

### 3. progress-tracker
**自動起動タイミング**: TodoWriteタスク完了時

**機能**:
- TodoWrite完了イベントを監視
- GitHubに進捗コメントを投稿
- 全タスク完了時にIssueを自動クローズ

**呼び出し元**: `work`実行後のバックグラウンドプロセス

---

## ワークフロー例

### 例1: Brainstorm → Issue → 作業
```bash
# ステップ1: 機能のブレインストーミング
/sc:brainstorm "ユーザー認証機能"
→ 対話的な要件発見
→ メモリに保存: brainstorm_auth

# ステップ2: brainstormからIssue作成
/gh:issue create --from-memory brainstorm_auth
→ Issue #42を作成
→ メタデータをセッションコンテキストに保存

# ステップ3: 作業開始
/gh:issue work 42
→ Issueを解析（issue-parser skill）
→ TodoWriteに変換（issue-todowrite-sync skill）
→ 5個のTodoWriteタスクを作成
→ 進捗トラッカーを起動

# ステップ4: タスク作業
(TodoWriteタスクを完了)
→ progress-trackerが自動的にIssue #42に投稿
→ "✅ タスク完了: API実装 (1/5タスク, 20%)"

# ステップ5: 完了
(全タスクを完了)
→ progress-trackerがIssue #42を自動クローズ
→ "🎉 全タスク完了！"
```

### 例2: 既存Issue → TodoWrite
```bash
# 既存Issueで作業開始
/gh:issue work 42
→ Issue #42を解析
→ 8個のTodoWriteタスクを作成
→ 進捗追跡を有効化

# 後で進捗確認
/gh:issue status 42
→ 表示: 3/8タスク (37.5%)

# 必要に応じて手動同期
/gh:issue sync 42
→ 最新の進捗でGitHubを更新
```

### 例3: 複数Issue
```bash
# 自分のIssue一覧
/gh:issue list --mine
→ #42, #43, #44

# 複数のIssueで作業
/gh:issue work 42
/gh:issue work 43

# 全て同期
/gh:issue sync --all
→ 全アクティブIssueを同期
```

---

## エラー処理

- **GitHub CLI未検出**: `gh` CLIの有無を確認し、インストール手順を提供
- **gitリポジトリ外**: `gh`のデフォルトリポジトリを使用、または`--repo`フラグを促す
- **Issue未発見**: Issue番号を含む明確なエラーメッセージ
- **ネットワークエラー**: 1回リトライし、その後適切に失敗
- **セッションコンテキストエラー**: セッション内メモリのみにフォールバック
- **TodoWrite競合**: ユーザーの変更を保持し、同期について警告

---

## 依存関係

- `gh` CLI (GitHub CLI) - 認証済みであること
- Gitリポジトリコンテキスト（デフォルトリポジトリ検出用）
- TodoWriteツール（Claude Code組み込み）
- Python 3.6+（Skills用）
- Skills: `issue-parser`, `issue-todowrite-sync`, `progress-tracker`

---

## Tips

💡 **Tip 1**: `/gh:issue list --mine`で割り当てられたIssueをすぐに確認

💡 **Tip 2**: `work`コマンドが最強 - 全て自動でセットアップ

💡 **Tip 3**: Skillsは自動実行される - 明示的に呼び出す必要なし

💡 **Tip 4**: 手動でIssueをクローズしたい場合は`--no-auto-close`を使用

💡 **Tip 5**: `/sc:brainstorm`と組み合わせてアイデアから実装まで完全ワークフロー

---

## 関連コマンド

- `/sc:brainstorm` - 要件発見（`create --from-memory`と相性抜群）
- `/sc:workflow` - IssueからImplementationワークフロー生成
- `/sc:git` - Issue参照付きコミット（例: "feat: auth (#42)"）
- `/sc:implement` - Issueから直接実装

---

**注意**: このコマンドはユーザーインターフェースとワークフロー制御を提供します。実際のロジックはSkillsに実装されており、必要に応じて自動的に起動します。
