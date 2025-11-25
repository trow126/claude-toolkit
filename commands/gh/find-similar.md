---
name: gh:find-similar
description: "実装やバグ修正の水平展開が必要な箇所を自動調査。Serena MCPで類似パターン・シンボル・参照を検索し、影響範囲を可視化。"
category: analysis
complexity: basic
mcp-servers: [serena]
personas: []
---

# /gh:find-similar - 類似パターン検索と水平展開調査

**任意の実装やバグ修正について「他の箇所も同じ対応が必要か」を自動調査するコマンド。**

Serena MCPを内部で自動使用し、ユーザーは意識する必要がありません。

## Triggers
- 実装やバグ修正後に水平展開が必要か調査したいとき
- 特定のコード変更を他の箇所にも適用すべきか判断したいとき
- 類似のバグパターンがコードベース全体に存在するか確認したいとき
- リファクタリングの影響範囲を把握したいとき
- コードの一貫性を確認したいとき

## Usage

```bash
# ファイルベースの調査
/gh:find-similar src/auth/login.ts
→ login.ts内のパターンを分析し、類似箇所を検索

# パターン説明による調査
/gh:find-similar "getUserData関数にキャッシュ機能を追加した"
→ キャッシュパターンと類似のget*Data関数を検索

# シンボル名での調査
/gh:find-similar --symbol validateUser
→ validateUser関数とその参照を全プロジェクトで検索

# 正規表現パターン指定
/gh:find-similar --pattern "if.*==.*null" --scope project
→ nullチェック不足のパターンを全体検索

# スコープ指定
/gh:find-similar src/api/ --scope module
→ src/api/配下のみで調査
```

## Behavioral Flow

### Phase 1: Pattern Identification（パターン特定）

```yaml
1. 入力解析:
   - ファイルパス指定 → ファイル内のパターンを抽出
   - 自然言語説明 → キーワードとパターン抽出
   - --symbol指定 → シンボル名を直接使用
   - --pattern指定 → 正規表現を直接使用

2. 自動Serena分析（ユーザーは意識不要）:

   a. ファイルパス指定時:
      - get_symbols_overview: ファイル構造を把握
      - find_symbol: 主要シンボルを抽出
      - パターン自動生成

   b. 自然言語説明時:
      - キーワード抽出（例: "getUserData", "キャッシュ"）
      - シンボル名/パターン候補生成
      - 検索戦略決定

   c. シンボル/パターン指定時:
      - 直接検索実行
```

### Phase 2: Multi-Strategy Search（多角的検索）

```yaml
3. 自動Serena検索（並列実行）:

   戦略1: シンボル検索
     - find_symbol(substring_matching=True)
     - 類似関数名/クラス名を検出
     - 例: "getUserData" → "getUserProfile", "getAccountData"

   戦略2: パターン検索
     - search_for_pattern(正規表現)
     - コード構造の類似性を検出
     - 例: "cache.*get.*" → キャッシュパターン

   戦略3: 参照追跡
     - find_referencing_symbols
     - 影響範囲の完全マップ
     - 例: validateUser → 全呼び出し箇所

4. 検索スコープ制御:
   - file: 単一ファイル内
   - module: ディレクトリ配下
   - project: プロジェクト全体（デフォルト）
```

### Phase 3: Impact Analysis（影響分析）

```yaml
5. 検出箇所の評価:

   優先度スコアリング:
     - 🔴 高優先度（即座対応）:
       * セキュリティ関連（auth, validation, permission）
       * データ整合性（database, transaction, migration）
       * パフォーマンス重要箇所（API endpoint, hot path）

     - 🟡 中優先度（検討対象）:
       * ビジネスロジック（service, controller）
       * 一般的なユーティリティ

     - 🟢 低優先度（任意）:
       * テストコード
       * デバッグ用コード
       * 一時的な実装

6. 影響範囲マッピング:
   - ファイル単位の影響度
   - モジュール間依存関係
   - テストカバレッジ確認
```

### Phase 4: Reporting（報告）

```yaml
7. 結果レポート生成:

   フォーマット:
   ## 🔍 類似パターン検索結果

   ### 📊 概要
   - 検索対象: [ファイル/パターン/シンボル]
   - 検出箇所: N件
   - 推奨アクション: [即座展開/要検討/影響なし]

   ### 🎯 水平展開が必要な箇所

   #### 🔴 高優先度（即座対応推奨）
   1. `src/auth/register.ts:45` - getUserDataと同一パターン
      - 検出理由: 認証系コンポーネント、キャッシュ未実装
      - 影響: パフォーマンス劣化、データベース負荷
      - 推奨: 同様のキャッシュ実装を適用
      - 参照数: 12箇所から呼び出し

   #### 🟡 中優先度（検討対象）
   2. `src/api/profile.ts:102` - 類似のデータ取得ロジック
      - 検出理由: データ取得パターンの類似性
      - 影響: 中程度のパフォーマンス改善見込み
      - 推奨: キャッシュ戦略を検討

   ### ℹ️ 参考情報（展開不要）
   - `src/utils/cache.ts:20` - 既にキャッシュ実装済み
   - `tests/unit/user.test.ts:55` - テストコード（対応不要）

   ### 📈 Next Steps
   1. 高優先度2箇所を即座対応
   2. 中優先度はパフォーマンステスト後に判断
   3. 実装後に /gh:find-similar で再検証

8. GitHub Issue連携（オプション）:
   - --create-issue: 検出箇所から新規Issue作成
   - --add-to-issue: 既存Issueにタスク追加
```

## Tool Coordination

### 自動Serena MCP使用（ユーザーは意識不要）

```yaml
Phase 1 - Pattern Identification:
  - get_symbols_overview: ファイル構造把握
  - read_file: コンテキスト理解
  - find_symbol: シンボル抽出

Phase 2 - Multi-Strategy Search（並列実行）:
  - find_symbol: シンボル名検索
  - search_for_pattern: パターン検索
  - find_referencing_symbols: 参照追跡

Phase 3 - Impact Analysis:
  - find_symbol (depth=1): 周辺コンテキスト取得
  - find_referencing_symbols: 呼び出し箇所確認

補完ツール:
  - Grep: Serena検索の補完
  - Read: 詳細コンテキスト確認
```

## Key Patterns

### Pattern 1: 実装の水平展開

```
新機能実装 → 類似コンポーネント検索 → 展開候補リスト → 優先度評価
```

**Example**:
```bash
/gh:find-similar "getUserData関数にキャッシュロジック追加"

→ 自動実行される処理:
  1. find_symbol("getUserData") → 定義箇所特定
  2. find_symbol("get*Data", substring=true) → 類似関数検索
  3. search_for_pattern("cache") → キャッシュパターン検索
  4. 差分分析: キャッシュあり vs なし
  5. 優先度評価 → レポート生成
```

### Pattern 2: バグ修正の伝播

```
バグ修正 → 同一パターン検索 → 潜在的バグ箇所特定 → 影響範囲評価
```

**Example**:
```bash
/gh:find-similar "login.tsでsessionのnullチェック追加した"

→ 自動実行される処理:
  1. read_file("src/auth/login.ts") → 修正内容把握
  2. search_for_pattern("session.*==.*null") → nullチェック検索
  3. find_symbol("session") → session関連シンボル
  4. find_referencing_symbols → 全参照箇所追跡
  5. 修正済み vs 未修正の判定
  6. 優先度評価（セキュリティ重視）
```

### Pattern 3: リファクタリング影響

```
コード改善 → 参照追跡 → 影響範囲マップ → 変更計画
```

**Example**:
```bash
/gh:find-similar --symbol validateInput --scope project

→ 自動実行される処理:
  1. find_symbol("validateInput") → 全定義箇所
  2. find_referencing_symbols → 全呼び出し箇所
  3. get_symbols_overview(各ファイル) → コンテキスト把握
  4. 影響範囲マップ生成
  5. 変更リスク評価
```

### Pattern 4: 命名規則統一

```
シンボル検索 → 命名パターン分析 → 不統一箇所特定 → 統一計画
```

**Example**:
```bash
/gh:find-similar --symbol "get*" --pattern "get[A-Z].*Data"

→ 自動実行される処理:
  1. find_symbol("get*", substring=true) → 全getter検索
  2. search_for_pattern("get[A-Z].*Data") → 命名パターン
  3. 命名規則分析（camelCase, snake_case混在チェック）
  4. 不統一箇所リスト化
  5. リネーム計画提案
```

## Examples

### Example 1: 機能実装後の横展開調査

```bash
# キャッシュ機能を実装した後

/gh:find-similar "getUserDataにキャッシュ追加"

→ 出力:
## 🔍 類似パターン検索結果

### 📊 概要
- 検索対象: getUserData関数のキャッシュパターン
- 検出箇所: 8件（実装必要: 3件）
- 推奨アクション: 高優先度3箇所を即座対応

### 🎯 水平展開が必要な箇所

#### 🔴 高優先度
1. `src/auth/register.ts:45` - getAccountData関数
2. `src/api/profile.ts:102` - getUserProfile関数
3. `src/admin/users.ts:78` - getAdminUserData関数
```

### Example 2: バグ修正の伝播確認

```bash
# nullチェックを追加した後

/gh:find-similar "sessionのnullチェック追加"

→ 出力:
## 🔍 類似パターン検索結果

### 📊 概要
- 検索対象: sessionのnullチェックパターン
- 検出箇所: 12件（要修正: 5件）
- 推奨アクション: 🔴高優先度5箇所を即座修正

### 🎯 潜在的バグ箇所

#### 🔴 高優先度（同一バグの可能性）
1. `src/auth/logout.ts:32` - session.user未チェック
2. `src/auth/refresh.ts:18` - session.token未チェック
3. `src/api/protected.ts:55` - session未チェック
```

### Example 3: リファクタリング前の影響調査

```bash
# エラーハンドリング変更前に影響範囲を調査

/gh:find-similar --pattern "try.*catch.*Error" --scope project

→ 出力:
## 🔍 類似パターン検索結果

### 📊 概要
- 検索対象: try-catchエラーハンドリング
- 検出箇所: 47件
- 推奨アクション: 段階的移行計画を策定

### 📊 影響範囲マップ

#### モジュール別集計
- src/auth/: 8箇所（高優先度）
- src/api/: 15箇所（中優先度）
- src/utils/: 12箇所（低優先度）
- tests/: 12箇所（対応不要）

#### 段階的移行プラン提案
Phase 1: src/auth/ (1週間)
Phase 2: src/api/ (2週間)
Phase 3: src/utils/ (1週間)
```

### Example 4: コード規約チェック

```bash
# 命名規則の一貫性確認

/gh:find-similar --symbol "validate*" --scope project

→ 出力:
## 🔍 類似パターン検索結果

### 📊 概要
- 検索対象: validate*関数群
- 検出箇所: 23件
- 推奨アクション: 命名規則を統一

### 🔍 命名パターン分析

#### パターン1: validateUser (18件) ✅ 推奨
- `src/auth/validator.ts:validateUser`
- `src/api/users.ts:validateUserInput`

#### パターン2: user_validate (3件) ⚠️ 非推奨
- `src/legacy/auth.ts:user_validate`

#### パターン3: checkUser (2件) ⚠️ 一貫性なし
- `src/middleware/auth.ts:checkUser`

→ リファクタリング提案:
  1. user_validate → validateUser
  2. checkUser → validateUser
  3. 統一後に全テスト実行
```

## Options

```bash
--symbol <name>        # シンボル名で検索（例: validateUser）
--pattern <regex>      # 正規表現パターン指定
--scope <level>        # file|module|project（デフォルト: project）
--priority <level>     # high|medium|low（フィルタ）
--format <type>        # text|json|markdown（デフォルト: markdown）
--create-issue         # 検出結果から新規Issue自動作成（オプション）
--add-to-issue <num>   # 既存Issueにタスク追加（オプション）
```

## Integration Points

### GitHub Issue連携（オプション）

```yaml
オプション使用時のみ:
  --create-issue:
    - 検出箇所から新規Issue自動作成
    - チェックボックス形式でタスクリスト化

  --add-to-issue <num>:
    - 既存IssueにタスクをMarkdownチェックボックスで追加
```

### Serena Memory連携

```yaml
水平展開パターン学習:
  - 頻繁に水平展開が発生するパターンを記録
  - 次回から自動提案
  - プロジェクト固有のパターン認識
```

## Error Handling

```bash
# Serenaプロジェクト未アクティブ
→ 自動的にsample-reference-projectをアクティブ化

# 検索結果0件
→ スコープ拡大提案
→ パターン調整提案

# 検索結果多数（>50件）
→ 優先度フィルタ自動適用
→ 高優先度のみ表示

# ファイル不存在
→ 類似ファイル名を提案
→ プロジェクト構造を確認
```

## Boundaries

### Will Do ✅

- Serena MCPを自動的に使用（ユーザーは意識不要）
- 複数検索戦略を並列実行（シンボル+パターン+参照）
- 優先度付きで実行可能な水平展開候補をリスト化
- 影響範囲と重要度に基づく詳細評価
- GitHub Issue連携の提案（オプション）
- 検出結果の構造化レポート生成

### Will Not Do ❌

- 自動的にコードを変更（報告のみ、変更は別途実行）
- 外部ライブラリやnode_modules内を調査
- プロジェクト外のコードを検索
- 誤検出の自動除外（全て報告、判断はユーザー）

## 実行指示（重要）

**あなたは今、`/gh:find-similar` コマンドを実行しています。**

### 🔴 デフォルト動作（必ず実行）

**ユーザーが明示的に指示しなくても、以下を自動的に実行してください:**

1. ✅ Serena MCPプロジェクトアクティブ化（必要な場合）
2. ✅ 入力からパターン/シンボルを自動抽出
3. ✅ 3つの検索戦略を並列実行:
   - find_symbol（シンボル検索）
   - search_for_pattern（パターン検索）
   - find_referencing_symbols（参照追跡）
4. ✅ 検出箇所の優先度評価
5. ✅ 構造化レポート生成
6. ✅ GitHub Issue連携の提案（オプション指定時のみ）

**⚠️ Serena MCPの使用はデフォルト動作です。ユーザーに確認不要。**

### 🚨 実行フロー（すべて自動実行）

```yaml
Phase 1: Pattern Identification（自動）
  - 入力解析 → パターン特定
  - get_symbols_overview（ファイル指定時）
  - キーワード抽出（自然言語時）

Phase 2: Multi-Strategy Search（並列・自動）
  並列実行:
    - Strategy 1: find_symbol
    - Strategy 2: search_for_pattern
    - Strategy 3: find_referencing_symbols

Phase 3: Impact Analysis（自動）
  - 優先度スコアリング
  - 影響範囲マッピング
  - テストカバレッジ確認

Phase 4: Reporting（自動）
  - 構造化レポート生成
  - GitHub Issue連携提案（オプション時）
  - Next Steps提示
```

### Tool Call Pattern（並列実行）

```yaml
# Phase 2で必ず並列実行:
単一メッセージ内で:
  - mcp__serena__find_symbol(...)
  - mcp__serena__search_for_pattern(...)
  - mcp__serena__find_referencing_symbols(...)
  ↓
Claude Codeが3つを同時実行 ⚡
```

## Related Commands

```bash
/sc:analyze         # コード品質分析（補完的分析）
/sc:troubleshoot    # バグ診断（バグ伝播確認）
/gh:issue work      # Issue作業開始（Issue連携時）
/gh:start           # タスク実装（Issue連携時）
```

## Tips

💡 **実装直後の調査**: 新機能実装後すぐに `/gh:find-similar` で横展開確認
💡 **バグ修正の伝播**: バグ修正後は必ず同一パターン検索を実行
💡 **リファクタリング前**: 影響範囲を事前把握してリスク軽減
💡 **Issue連携**: オプションで検出箇所を新規Issueまたは既存Issueに追加
💡 **定期実行**: スプリント終了時に実行してコード一貫性確認
💡 **パターン学習**: 頻出パターンはSerenaメモリに自動記録

---

**Last Updated**: 2025-11-25
**Version**: 1.1.0
