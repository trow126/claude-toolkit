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
/gh:issue create --from-file claudedocs/brainstorm/auth_requirements_20251031.md

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

3. **GitHub Projectsに追加** 🆕
   ```bash
   source scripts/gh-projects-integration.sh
   gh_projects_set_todo $ISSUE_NUMBER
   ```
   - 自動的にリポジトリのProjectsを検出
   - ステータスを "Todo" に設定
   - プロジェクト未存在時は自動作成
   - 権限エラー時はラベルモードにフォールバック

4. **セッションコンテキストにメタデータ保存**
   - Issueメタデータをセッションコンテキストに保存（セッション内での参照用）
   - `--from-file` で使用したファイルパスも保存（クローズ時の削除用）

5. **結果を表示**
   Issue番号とURLを表示

#### オプション

**`--from-file <path>`**
- **説明**: 指定したファイルの内容をIssue本文として使用します
- **用途**: `/gh:brainstorm`で生成した要件ファイルからIssueを作成する場合
- **推奨**: `claudedocs/brainstorm/` ディレクトリのファイルを使用
- **例**: `/gh:issue create "Feature: Auth" --from-file claudedocs/brainstorm/auth_requirements_20251031.md`

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
# Issueの作業を開始（スマートデフォルト）🆕
/gh:issue work 42
# → 10タスク以上 + Phase情報あり: Phase単位で作成
# → それ以外: 全タスク作成

# 全タスクを強制表示（スマートデフォルトを無効化）
/gh:issue work 42 --all-tasks

# Phase単位を強制（タスク数に関わらず）
/gh:issue work 42 --phase-by-phase

# 特定フェーズから開始
/gh:issue work 42 --phase-by-phase --current-phase "Phase 2"

# 自動クローズなしで作業
/gh:issue work 42 --no-auto-close
```

#### 処理フロー

**実行方法**:
このコマンドは複雑な6ステップ操作のため、**Task toolでgeneral-purpose agentに委譲**して実行されます。

**Agent内での実行ステップ**:

**ステップ1: Issueを解析**（`issue-parser` skillを使用）
```
→ issue-parser skillを起動
→ GitHub からIssue #42のデータを取得（本文 + コメント）
→ タスク、フェーズ、メタデータを抽出
→ 最新のコメントから進捗状態を確認
→ 完了済みタスク（[x]）を識別
```

**ステップ2: TodoWriteに変換**（`issue-todowrite-sync` skillを使用）
```
→ issue-todowrite-sync skillを起動
→ 未完了タスク（[ ]）のみをTodoWrite形式に変換
→ 完了済みタスク（[x]）は除外
→ 各タスクのactiveFormを生成
→ TodoWriteタスクを作成
```

**ステップ3: セッションコンテキストにマッピング保存**
Issue-TodoWriteマッピングをセッションコンテキストに保存（セッション内での追跡用）

**ステップ4: GitHub Projectsステータス更新** 🆕
```
→ scripts/gh-projects-integration.sh を起動
→ ステータスを "In Progress" に更新
→ プロジェクト未存在時は自動作成
```

**ステップ5: TodoWriteタスクを表示**
```
Issue #42の作業を開始しました: Feature: User Authentication

GitHub Projects: ステータスを "In Progress" に更新しました
GitHub進捗: 1/3タスク完了 (33.3%)
完了済みタスク（TodoWriteから除外）:
✅ Database schema

TodoWriteタスクを作成（未完了のみ）:
⏳ 1. API実装
⏳ 2. Frontend components

合計: 2タスク（未完了のみ）
進捗追跡が有効化されました。全タスク完了時にIssueは自動クローズされます。
```

**バックグラウンド: 進捗トラッカー起動**（`progress-tracker` skillを使用）
```
→ progress-tracker skillがTodoWriteを監視開始
→ タスク完了時に自動的にコメント投稿
→ 全タスク完了時にIssueを自動クローズ（有効時）
→ GitHub Projectsステータスも "Done" に自動更新
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

**スマートデフォルト** 🆕
- **説明**: タスク数とPhase情報に基づいて自動的にモードを選択します
- **判定条件**:
  - **Phase単位**: 10個以上の未完了タスク かつ Phase情報あり
  - **全タスク**: それ以外（9個以下、またはPhase情報なし）
- **例**: `/gh:issue work 42`（フラグなし = スマートデフォルト）
- **メリット**:
  - 大規模Issueで自動的に見やすい表示
  - 小規模Issueは従来通り全タスク表示
  - Phase情報なしIssueも問題なく動作
- **無効化**: `--all-tasks`または`--phase-by-phase`で明示的に指定

**`--all-tasks`** 🆕
- **説明**: スマートデフォルトを無効化し、全タスクを強制的に表示します
- **用途**: 10個以上のタスクがあるIssueでも全体を一度に確認したい場合
- **例**: `/gh:issue work 42 --all-tasks`
- **動作**: Phase情報やタスク数に関わらず全タスクをTodoWriteに作成

**`--phase-by-phase`** 🆕
- **説明**: タスク数に関わらずPhase単位で段階的にTodoWriteタスクを作成します
- **用途**: 小規模Issue（<10タスク）でもPhase単位で作業したい場合
- **動作**:
  - 最初の未完了PhaseのタスクのみをTodoWriteに作成
  - Phase完了時に次Phaseを自動展開（progress-tracker skill）
  - `/gh:start` 実行時の表示タスク数を削減
- **例**: `/gh:issue work 42 --phase-by-phase`
- **メリット**:
  - 認知負荷の削減（3-5タスクずつ表示）
  - 現在のPhaseに集中できる
  - Phase完了ごとに達成感を得られる
- **備考**: Phase情報（`## Phase 1` 等）がIssue本文にある場合のみ有効

**`--current-phase <name>`** 🆕
- **説明**: `--phase-by-phase` と併用し、特定のPhaseから作業を開始します
- **用途**: Phase 1をスキップして Phase 2 から開始したい場合
- **例**: `/gh:issue work 42 --phase-by-phase --current-phase "Phase 2: Frontend"`
- **例**: `/gh:issue work 42 --phase-by-phase --current-phase "Frontend"`（部分一致）
- **備考**: `--phase-by-phase` フラグが必須

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

2. **学習を抽出して保存** ✨ (`issue-retrospective` skill)
   - Issue履歴を分析（タイムライン、タスク、コメント）
   - 成功パターン、課題、ブロッカーを抽出
   - 改善提案とパターンを識別
   - 振り返りを記録:
     - **GitHub Issue comment**: 構造化された振り返りコメントを投稿
     - **claudedocs/learnings.md**: プロジェクト全体の知見を追記
   - 振り返りサマリーをユーザーに表示

3. **最終コメントを投稿**
   ```bash
   gh issue comment 42 --body "🎉 Issue完了。全タスク完了しました。"
   ```

4. **GitHub Projectsステータス更新** 🆕
   ```bash
   source scripts/gh-projects-integration.sh
   gh_projects_set_done 42
   ```
   - ステータスを "Done" に設定
   - 権限エラー時はラベルモードにフォールバック

5. **Issueをクローズ**
   ```bash
   gh issue close 42 --reason completed
   ```

6. **セッションコンテキストをクリーンアップ**
   Issue-TodoWriteマッピングをセッションコンテキストから削除

7. **ブレインストーミングファイルを削除**
   - Issue作成時に `--from-file` で使用したファイルを削除
   - `claudedocs/brainstorm/` 内のファイルのみ対象
   - ユーザーに削除を通知

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

**`--no-retro`**
- **説明**: 学習抽出（retrospective）をスキップします
- **用途**: 学習不要、または後で手動実行する場合
- **動作**:
  - `issue-retrospective` skillをスキップ
  - GitHub振り返りコメント投稿なし
  - `claudedocs/learnings.md` への追記なし
  - 振り返りサマリー表示なし
  - 他の処理（コメント投稿、クローズ）は通常通り実行
- **例**: `/gh:issue close 42 --no-retro`
- **備考**: 学習は後から `use issue-retrospective skill for Issue #42` で手動実行可能

**`--keep-brainstorm`**
- **説明**: ブレインストーミングファイルを削除せずに保持します
- **用途**: 後で参照したい、または複数Issueで使用する場合
- **動作**:
  - Issue-TodoWriteマッピングをクリーンアップ
  - `claudedocs/brainstorm/` のファイルは削除しない
- **例**: `/gh:issue close 42 --keep-brainstorm`
- **備考**: 手動で削除が必要になります

---

## Skills連携

このコマンドは4つのSkillsとシームレスに連携します。

**実行アーキテクチャ**:
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
**起動方法**: Agent内で "use issue-parser skill" により起動

**機能**:
- GitHubからIssueを取得（本文 + コメント）
- コメントから最新の進捗状態を確認
- タスク、フェーズ、メタデータを抽出
- 完了済みタスク（[x]）を識別
- 構造化JSONを返す

**呼び出し元コマンド**: `create`, `work`, `view`

### 2. issue-todowrite-sync
**起動方法**: Agent内で "use issue-todowrite-sync skill" により起動

**機能**:
- Issue → TodoWrite変換（未完了タスクのみ）
- 完了済みタスク（[x]）を自動除外
- TodoWrite → GitHub同期
- セッションコンテキストでマッピングを維持

**呼び出し元コマンド**: `work`, `sync`, `status`

### 3. progress-tracker
**起動方法**: Agent内で "use progress-tracker skill" により起動

**機能**:
- TodoWrite完了イベントを監視
- GitHubに進捗コメントを投稿
- 全タスク完了時にIssueを自動クローズ

**呼び出し元コマンド**: `work`実行後のバックグラウンド監視

### 4. issue-retrospective
**起動方法**: `close`コマンド実行時に自動起動（`--no-retro`でスキップ可能）

**機能**:
- Issue履歴を分析（タイムライン、タスク、コメント）
- 成功パターン、課題、ブロッカーを抽出
- プロセス改善提案を生成
- 再利用可能なコードパターンを識別
- 振り返りを記録:
  - **GitHub Issue comment**: 構造化された振り返りコメントを投稿
  - **claudedocs/learnings.md**: プロジェクト全体の知見を追記
- 振り返りサマリーを表示

**呼び出し元コマンド**: `close`（Issue完了前に自動実行）

**記録先**:
- Issue自体に振り返りコメント（GitHub上で閲覧可能）
- プロジェクトルートの `claudedocs/learnings.md` にパターン蓄積

**手動実行**:
```bash
# 完了済みIssueの振り返りを後から実行
"use issue-retrospective skill for Issue #42"
```

---

## GitHub Projects Integration 🆕

### 機能概要
`/gh:issue` コマンドは GitHub Projects V2 と自動連携し、ステータスを視覚的に管理できます。

### 主な特徴
- **ゼロ設定**: コマンド実行だけで自動検出・自動作成
- **3状態管理**: Todo → In Progress → Done
- **自動フォールバック**: 権限エラー時はラベルモードに自動切替
- **完全自動**: プロジェクト検出から更新まで全て自動

### ステータス自動更新
```bash
/gh:issue create   → Projects: "Todo"
/gh:issue work     → Projects: "In Progress"
/gh:issue close    → Projects: "Done"
```

### 進捗確認方法
GitHub Projects UI (ブラウザ) でカンバンボード表示:
```
┌──────────┬──────────────────┬──────────┐
│   Todo   │   In Progress   │   Done   │
├──────────┼──────────────────┼──────────┤
│ Issue #44│    Issue #42    │ Issue #40│
│ Issue #45│    Issue #43    │ Issue #41│
└──────────┴──────────────────┴──────────┘
```

### プロジェクト自動作成
プロジェクトが存在しない場合、自動的に作成されます:
- プロジェクト名: `{repo-name} Issues`
- デフォルトフィールド: Status (Todo/In Progress/Done)
- リポジトリに自動リンク

### Graceful Degradation
GitHub Projects権限がない場合、自動的にラベルモードに切り替わります:
- `status:todo`
- `status:in-progress`
- `status:done`

### 多言語対応
ステータス列名の柔軟なマッピング:
- **Todo**: `todo`, `未着手`, `バックログ`, `backlog`
- **In Progress**: `progress`, `進行中`, `作業中`, `doing`, `in progress`
- **Done**: `done`, `完了`, `終了`, `finished`, `closed`

### 必要な権限
GitHub CLI で `project` スコープが必要です:
```bash
gh auth refresh -s project
```

権限がない場合、自動的にラベルモードにフォールバックするため、エラーにはなりません。

---

## ワークフロー例

### 例1: Brainstorm → Issue → 作業
```bash
# ステップ1: 機能のブレインストーミング
/gh:brainstorm "ユーザー認証機能"
→ 対話的な要件発見
→ ファイルに保存: claudedocs/brainstorm/jwt_auth_requirements_20251031.md

# ステップ2: brainstormからIssue作成
/gh:issue create --from-file claudedocs/brainstorm/jwt_auth_requirements_20251031.md
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

### 例2: 既存Issue → TodoWrite（途中再開）
```bash
# セッション1: 作業開始
/gh:issue work 42
→ Issue #42を解析（本文 + コメント）
→ GitHubで既に3/8タスク完了済み
→ 未完了5タスクのみTodoWriteに変換
→ 進捗追跡を有効化

# タスク作業（2つ完了）
(TodoWriteで2タスク完了)
→ progress-trackerが自動的にGitHub更新

# セッション終了

# セッション2: 翌日再開
/gh:issue work 42 --refresh
→ GitHubから最新状態を取得
→ 現在5/8タスク完了済み
→ 未完了3タスクのみTodoWriteに復元

# 後で進捗確認
/gh:issue status 42
→ 表示: 5/8タスク (62.5%)

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
- Task tool（複雑な操作のagent委譲用）
- Python 3.6+（Skills用）
- Skills: `issue-parser`, `issue-todowrite-sync`, `progress-tracker`

---

## Tips

💡 **Tip 1**: `/gh:issue list --mine`で割り当てられたIssueをすぐに確認

💡 **Tip 2**: `work`コマンドが最強 - Task toolで自動的にagentに委譲され全て処理

💡 **Tip 3**: 複雑な6ステップ操作をagentが実行 - ユーザーは待つだけ

💡 **Tip 4**: 手動でIssueをクローズしたい場合は`--no-auto-close`を使用

💡 **Tip 5**: `/gh:brainstorm`と組み合わせてアイデアから実装まで完全ワークフロー

💡 **Tip 6**: `work`はコメントも確認 - GitHubの最新進捗を自動反映

💡 **Tip 7**: 完了済みタスク（[x]）はTodoWriteから自動除外 - 未完了のみ作業

💡 **Tip 8**: Agent内でSkillsが順次実行 - issue-parser → issue-todowrite-sync → progress-tracker

💡 **Tip 9**: スマートデフォルト有効 🆕 - 10タスク以上で自動的にPhase単位表示

💡 **Tip 10**: 全タスク確認したい？ `--all-tasks`で強制的に全表示可能

💡 **Tip 11**: 小規模Issueでも Phase単位で作業したい？ `--phase-by-phase`を使用

---

## 関連コマンド

- `/gh:brainstorm` - 要件発見（`create --from-file`と相性抜群）
- `/sc:workflow` - IssueからImplementationワークフロー生成
- `/sc:git` - Issue参照付きコミット（例: "feat: auth (#42)"）
- `/sc:implement` - Issueから直接実装

---

**注意**: このコマンドはスラッシュコマンドであり、実行時に**Task tool経由でgeneral-purpose agentに委譲**されます。Agent内でSkillsが順次起動され、複雑な6ステップ操作を自動実行します。これはSuperClaude Frameworkの「Agent Orchestration」ルール（>3 steps = Task delegation）に準拠した設計です。

---

## 実行指示

**あなたは今、`/gh:issue` コマンドを実行しています。**

ユーザーのコマンドを解析し、適切なサブコマンドを実行してください：

### create サブコマンド
1. GitHub Issueを作成します。必要に応じてAskUserQuestionツールで詳細を確認してください。
2. Issue作成後、`scripts/gh-projects-integration.sh`をsourceして`gh_projects_set_todo`を実行
   ```bash
   source scripts/gh-projects-integration.sh
   gh_projects_set_todo $ISSUE_NUMBER
   ```

### list サブコマンド
`gh issue list` を使用してIssue一覧を表示してください。

### view サブコマンド
`gh issue view [number]` を使用してIssue詳細を表示してください。

### work サブコマンド
**重要**: このサブコマンドは複雑な6ステップ操作のため、**必ずTask toolを使用してgeneral-purpose agentに委譲**してください。

**委譲するタスク内容**:
```
GitHub Issue #[number] の作業を開始します。

以下のSkillsを順次実行してください:

1. **issue-parser skillを起動**
   - "use issue-parser skill for Issue #[number]"
   - GitHub APIからIssue本文とコメントを取得
   - 完了済みタスク（[x]）と未完了タスク（[ ]）を識別
   - タスク、フェーズ、メタデータを抽出

2. **issue-todowrite-sync skillを起動**
   - "use issue-todowrite-sync skill to convert Issue #[number] to TodoWrite"
   - 未完了タスク（[ ]）のみをTodoWrite形式に変換
   - 完了済みタスク（[x]）は除外
   - TodoWriteツールを使用してタスクを作成

   **スマートデフォルト** 🆕:
   - デフォルト（フラグなし）:
     * `convert_to_todowrite_by_phase(phase_mode=None)` を使用
     * 10タスク以上 + Phase情報あり → Phase単位作成
     * それ以外 → 全タスク作成
   - `--all-tasks` フラグがある場合:
     * `convert_to_todowrite_by_phase(phase_mode=False)` を使用
     * 全タスクを強制的に作成
   - `--phase-by-phase` フラグがある場合:
     * `convert_to_todowrite_by_phase(phase_mode=True)` を使用
     * 最初の未完了Phaseのタスクのみ変換
   - `--current-phase <name>` フラグがある場合:
     * 指定されたPhaseから開始
     * `target_phase=<name>` を設定

3. **GitHub Projectsステータス更新** 🆕
   - `scripts/gh-projects-integration.sh`をsourceして`gh_projects_set_in_progress`を実行
   ```bash
   source scripts/gh-projects-integration.sh
   gh_projects_set_in_progress [number]
   ```

4. **progress-tracker skillを起動**
   - "use progress-tracker skill for Issue #[number]"
   - TodoWrite完了イベントの監視を開始
   - 進捗の自動同期を有効化

各Skillの実行結果をユーザーに報告してください。

オプション処理:
- デフォルト（フラグなし）: スマートデフォルト（自動判定）
- --all-tasks: 全タスクを強制表示（スマートデフォルト無効化）
- --phase-by-phase: Phase単位を強制（タスク数に関わらず）
- --current-phase <name>: --phase-by-phaseと併用、特定Phaseから開始
- --no-auto-close: 自動クローズを無効化
- --refresh: GitHub最新状態と同期
```

**Task tool呼び出し例**:
```
Task tool with:
- subagent_type: "general-purpose"
- description: "GitHub Issue work command execution"
- prompt: [上記のタスク内容]
```

### status サブコマンド
TodoWriteの現在の進捗状態を表示してください。

### sync サブコマンド
**issue-todowrite-sync skillを使用**して進捗をGitHubに同期してください。

### close サブコマンド
1. **issue-retrospective skillを起動**（`--no-retro`がない場合）
2. 完了サマリーをコメント投稿
3. **GitHub Projectsステータス更新** 🆕
   ```bash
   source scripts/gh-projects-integration.sh
   gh_projects_set_done [number]
   ```
4. `gh issue close [number]` でIssueをクローズ
5. セッションコンテキストをクリーンアップ
6. ブレインストーミングファイルを削除（`--keep-brainstorm`がない場合）

---

**実行ルール**:
- `work`コマンドは**必ずTask toolでagentに委譲**（>3 steps = delegation rule）
- Agent内で**Skillsを順次起動**（issue-parser → issue-todowrite-sync → progress-tracker）
- TodoWriteツールの呼び出しは**Skill内で実行**（このスラッシュコマンド内では直接呼び出さない）
- 各ステップの結果をユーザーに報告
