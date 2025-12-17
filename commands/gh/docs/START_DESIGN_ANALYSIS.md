# /gh:start 設計分析レポート

**作成日**: 2025-12-17
**対象**: `/gh:start` コマンド (v2.2.0)
**目的**: 設計上の問題点の特定と改善提案

---

## エグゼクティブサマリー

`/gh:start` は GitHub Issue駆動開発の統合コマンドとして設計されているが、**プロンプトベースの仕様書（926行）として実装されており、実行の確実性に課題がある**。

主な問題:
1. 並列実行は理想であり保証ではない
2. 複雑すぎて実行漏れリスクが高い
3. Skills依存だがテストされていない
4. Checkpoint競合リスク

---

## 1. 根本的な問題

### 1.1 プロンプト ≠ コード

| 特性 | プロンプト（現状） | コード（理想） |
|------|-------------------|---------------|
| 強制力 | なし（Claudeの解釈依存） | あり（コンパイル/ランタイム） |
| エラー検出 | 実行時のみ、不確実 | 静的解析可能 |
| テスト | 困難 | 単体テスト可能 |
| 再現性 | 低（LLMの確率的動作） | 高（決定論的） |

### 1.2 複雑性の問題

```
現在の構造:
- 926行のMarkdownファイル
- 5+フェーズ（Phase 0, 1, 1.5, 2, 3, 4, 5）
- 多数の条件分岐（Issue番号有無、checkpoint有無、タスク数...）
- 複数のSkills呼び出し
- 並列/逐次の判断ロジック
```

**問題**: Claudeが毎回このすべてを正確に解釈・実行する保証がない。

### 1.3 仕様と実行のギャップ

```yaml
# 設計の意図
Phase 1.5を必ず実行 → 依存関係分析 → 並列グループ作成 → checkpoint保存

# 実際に起こりうること
- Phase 1.5をスキップ（長いプロンプトで見落とし）
- 依存関係分析が不完全
- checkpoint保存を忘れる
- 並列実行のつもりが逐次実行
```

---

## 2. 具体的な問題点

### 2.1 並列実行の実装問題

**設計の主張**:
```yaml
✅ 正しい: 1メッセージ内で複数Task tool → Claude Code並列実行
❌ 間違い: Task tool → 待機 → Task tool（逐次化）
```

**現実**:
- Claude Codeは技術的に並列実行可能
- しかし、Claudeが正しくバッチ構築するかは不確実
- Claudeのデフォルト傾向は逐次処理

**検証方法なし**:
- 実際に並列実行されたか確認する手段がない
- ログやメトリクスが存在しない

### 2.2 依存関係分析のヒューリスティック

**設計**:
```yaml
レイヤー依存検出（キーワードマッチ）:
  - Layer 1 (Database): database, schema, migration, model
  - Layer 2 (Backend): API, endpoint, service, controller
  - Layer 3 (Frontend): UI, component, page, view
  - Layer 4 (Testing): test, E2E, integration
```

**問題点**:

| 問題 | 例 |
|------|-----|
| 検出漏れ | "DBテーブル追加" → "database"キーワードなし |
| 誤検出 | "API documentを更新" → APIレイヤーと誤認 |
| 意味的依存の無理解 | Task AがTask Bの出力を使う関係は検出不能 |
| 言語依存 | 日本語タスク記述では英語キーワードがマッチしない |

### 2.3 Skills依存の不確実性

**参照されているSkills**:
- `issue-parser`
- `issue-todowrite-sync`
- `checkpoint-manager`
- `progress-tracker`

**問題**:
1. **実装品質不明**: テストスイートが存在しない
2. **エラーハンドリング不明**: Skill失敗時の挙動が未定義
3. **プロンプトベース**: Skill自体もプロンプトであり、同じ不確実性を持つ

### 2.4 Checkpoint競合リスク

**シナリオ**:
```
Session A: /gh:start 42
  → checkpoint読み込み
  → Task 1実行中...

Session B: /gh:start 42 (別マシン)
  → 同じcheckpoint読み込み
  → Task 2実行中...

Session A: checkpoint書き込み (Task 1完了)
Session B: checkpoint書き込み (Task 2完了) ← Session Aの変更を上書き！
```

**結果**: Task 1の完了状態が失われる

**原因**: Serena Memoryにロック機構がない

### 2.5 GitHub-Checkpoint SSOT矛盾

**設計の主張**:
```
GitHub Issue = SSOT（Single Source of Truth）
Checkpoint = 復旧用キャッシュ
```

**問題**:
- 両者の同期タイミングが不明確
- 「GitHubが勝つ」とあるが、実装で強制されていない
- 手動でGitHub Issueを編集した場合の挙動が未定義

---

## 3. 影響分析

### 3.1 信頼性への影響

| 問題 | 発生確率 | 影響度 | リスクスコア |
|------|---------|--------|-------------|
| Phase 1.5スキップ | 中 | 高（並列化失敗） | 高 |
| checkpoint保存漏れ | 中 | 高（復旧不能） | 高 |
| 並列実行の逐次化 | 高 | 中（時間増加） | 中 |
| 依存関係誤検出 | 中 | 中（実行順序エラー） | 中 |
| checkpoint競合 | 低 | 高（データ損失） | 中 |

### 3.2 保守性への影響

- **変更困難**: 926行の仕様変更は影響範囲が不明確
- **デバッグ困難**: 「なぜ動かないか」の原因特定が難しい
- **テスト困難**: 自動テストの仕組みがない

---

## 4. 改善提案

### 4.1 短期改善（プロンプト修正）

#### A. 簡素化
```yaml
現在: 5+フェーズ、926行
改善: 3フェーズ、300行以下

Core Flow:
  Phase 1: Issue Load (checkpoint復元 or 新規作成)
  Phase 2: Implementation (逐次実行をデフォルト)
  Phase 3: GitHub Sync (完了時に更新)
```

#### B. 明示的バリデーション追加
```yaml
# 各フェーズ終了時に確認
Phase 1完了後:
  - "checkpoint保存しました: issue_42_checkpoint"
  - "TodoWrite作成: 5タスク"
  → 明示的なログ出力で実行確認
```

#### C. 並列実行をオプトイン化
```yaml
# デフォルト: 逐次実行（確実）
/gh:start 42

# 明示的並列: ユーザーが選択時のみ
/gh:start 42 --parallel
```

### 4.2 中期改善（シェルスクリプト化）

重要なロジックをシェルスクリプトに移行:

```bash
# ~/.local/bin/gh-start-core
#!/bin/bash
# Issue取得、checkpoint管理、GitHub同期の核心ロジック

gh_start_load_issue() {
  local issue_number=$1
  gh issue view "$issue_number" --json body,state,title
}

gh_start_save_checkpoint() {
  local issue_number=$1
  local data=$2
  # Serena memory操作をラップ
}

gh_start_sync_github() {
  local issue_number=$1
  local task_number=$2
  # GitHub Issue更新
}
```

**メリット**:
- 決定論的動作
- テスト可能
- エラーハンドリング明確

### 4.3 長期改善（アーキテクチャ再設計）

```
現在:
  /gh:start (プロンプト) → Claude解釈 → 実行

改善案:
  /gh:start (プロンプト)
    ↓ 薄いラッパー
  gh-start-core (シェルスクリプト)
    ↓ 確実な制御
  Claude (実装のみ担当)
```

**責務分離**:
| 層 | 責務 | 実装 |
|----|------|------|
| UI層 | ユーザー対話 | スラッシュコマンド |
| 制御層 | フロー管理、状態管理 | シェルスクリプト |
| 実行層 | コード実装 | Claude + Task tool |

---

## 5. 優先度付きアクションプラン

### Phase 1: 即時対応（1-2日）

1. **簡素化版start.mdの作成**
   - 300行以下
   - 3フェーズのみ
   - 逐次実行デフォルト

2. **明示的ログ追加**
   - 各フェーズ開始/終了を出力
   - checkpoint操作を可視化

### Phase 2: 短期対応（1週間）

1. **Skills単体テスト**
   - 各Skillを個別に呼び出してテスト
   - エラーケースの確認

2. **checkpoint競合対策**
   - ファイルベースロックの検討
   - またはGitHub Issueのみに依存（checkpoint廃止）

### Phase 3: 中期対応（2-4週間）

1. **gh-start-coreスクリプト作成**
   - 制御ロジックをシェルスクリプト化
   - プロンプトは実装指示のみに限定

2. **テストスイート整備**
   - 各シナリオの自動テスト
   - CI/CD統合

---

## 6. 結論

`/gh:start` の設計は野心的であり、理想的なワークフローを描いている。しかし、**プロンプトベースの926行仕様書として実装されているため、実行の確実性に根本的な課題がある**。

**推奨アプローチ**:
1. 短期: 簡素化して信頼性向上
2. 中期: 制御ロジックをコード化
3. 長期: 責務分離によるアーキテクチャ改善

複雑な仕様をプロンプトで表現することの限界を認識し、**「確実に動く簡素なシステム」を目指すべき**。

---

## 付録: 関連ドキュメント

- `/gh:start` 仕様: `~/.claude/commands/gh/start.md`
- Skills定義: `~/.claude/skills/`
- README: `~/.claude/commands/gh/README.md`

---

**Document Version**: 1.0.0
**Author**: Claude Code Analysis
**Last Updated**: 2025-12-17
