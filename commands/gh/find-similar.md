---
name: gh:find-similar
description: "実装やバグ修正の水平展開が必要な箇所を自動調査。サブエージェント委譲でコンテキスト効率化。Serena MCPで類似パターン・シンボル・参照を検索し、影響範囲を可視化。"
category: analysis
complexity: standard
mcp-servers: [serena]
personas: []
---

# /gh:find-similar - 類似パターン検索と水平展開調査

**任意の実装やバグ修正について「他の箇所も同じ対応が必要か」を自動調査するコマンド。**

**🚀 v2.0: サブエージェント委譲によるコンテキスト効率化**
- 検索処理をExploreサブエージェントに委譲
- メインコンテキストは結果サマリーのみ受信
- 70-80%のコンテキスト削減を実現

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

## Architecture（v2.0 サブエージェント委譲）

### コンテキスト効率化の原理

```
┌─────────────────────────────────────────────────────────────┐
│  メインコンテキスト（軽量）                                    │
│  ├─ Phase 1: パターン抽出（~500 tokens）                     │
│  ├─ サブエージェント起動指示のみ                              │
│  └─ 結果サマリー受信（~1000 tokens）                         │
│                                                             │
│  Total: ~1500 tokens (以前: ~20000 tokens)                  │
└─────────────────────────────────────────────────────────────┘
                            ↓ 委譲
┌─────────────────────────────────────────────────────────────┐
│  Exploreサブエージェント（独立コンテキスト）                    │
│  ├─ Serena find_symbol → 全結果を内部処理                    │
│  ├─ Serena search_for_pattern → 全結果を内部処理             │
│  ├─ Serena find_referencing_symbols → 全結果を内部処理       │
│  └─ 優先度評価・レポート生成                                  │
│                                                             │
│  → メインには JSON サマリーのみ返却                           │
└─────────────────────────────────────────────────────────────┘
```

### 従来 vs v2.0 比較

| 項目 | 従来（v1.1） | v2.0（サブエージェント委譲） |
|------|-------------|---------------------------|
| メインコンテキスト消費 | 20K+ tokens | ~1.5K tokens |
| 50ファイル検索時 | コンテキスト圧迫 | 問題なし |
| 検索結果 | 全結果がメインに蓄積 | サマリーのみ受信 |
| 並列検索 | メインで並列実行 | サブエージェント内で実行 |

## Behavioral Flow

### Phase 1: Pattern Identification（パターン特定・メインコンテキスト）

```yaml
1. 入力解析（軽量処理のみ）:
   - ファイルパス指定 → パス文字列を抽出
   - 自然言語説明 → キーワードを抽出
   - --symbol指定 → シンボル名を抽出
   - --pattern指定 → 正規表現を抽出

2. 検索パラメータ生成:
   search_params = {
     "type": "symbol" | "pattern" | "file",
     "query": "...",
     "scope": "file" | "module" | "project"
   }
```

### Phase 2: Subagent Delegation（サブエージェント委譲・🚀新規）

```yaml
3. Exploreサブエージェントを起動:

   Task(
     subagent_type: "Explore",
     prompt: |
       ## 類似パターン検索タスク

       **検索パラメータ**:
       - Type: {type}
       - Query: "{query}"
       - Scope: {scope}

       **実行手順**:
       1. Serena MCPをアクティブ化
       2. 以下の3検索を並列実行:
          - find_symbol("{query}", substring_matching=True)
          - search_for_pattern("{regex_pattern}")
          - find_referencing_symbols("{symbol}")

       3. 検出箇所を優先度評価:
          - 🔴高: auth, validation, security, database
          - 🟡中: service, controller, business
          - 🟢低: test, debug, utils

       **⚠️ 返却形式（厳守）**:
       JSON形式のみ返却。全検索結果は含めない。

       {
         "summary": {
           "total_matches": N,
           "high_priority": N,
           "medium_priority": N,
           "low_priority": N,
           "recommendation": "即座展開 | 要検討 | 影響なし"
         },
         "high_priority": [
           {
             "path": "src/auth/login.ts",
             "line": 45,
             "snippet": "function getUserData()...",
             "reason": "認証系コンポーネント",
             "ref_count": 12
           }
         ],
         "medium_priority": [...],
         "low_priority_count": N,
         "patterns_found": ["pattern1", "pattern2"]
       }
   )

4. サブエージェント内部処理（独立コンテキスト）:
   - Serena検索実行（全結果を内部保持）
   - 結果フィルタリング・重複除去
   - 優先度スコアリング
   - JSONサマリー生成
   → メインにサマリーのみ返却
```

### Phase 3: Report Generation（レポート生成・メインコンテキスト）

```yaml
5. サブエージェント結果を受信:
   - JSONサマリー（~1000 tokens）のみ
   - 全検索結果は含まれない（コンテキスト節約）

6. 構造化レポートに変換:
   - Markdown形式で整形
   - 優先度別にセクション分け
   - Next Steps提案
   - GitHub Issue連携オプション
```

### Phase 4: Optional Actions（オプション処理）

```yaml
7. --create-issue 指定時:
   - 検出箇所からIssue本文生成
   - gh issue create 実行

8. --add-to-issue 指定時:
   - 既存Issueにタスク追加
   - Markdownチェックボックス形式
```

## Impact Analysis（影響分析）

```yaml
優先度スコアリング（サブエージェント内で実行）:

   🔴 高優先度（即座対応）:
     - セキュリティ関連: auth, validation, permission, security
     - データ整合性: database, transaction, migration, model
     - パフォーマンス: API endpoint, hot path, cache

   🟡 中優先度（検討対象）:
     - ビジネスロジック: service, controller, handler
     - 一般的なユーティリティ: utils, helpers

   🟢 低優先度（任意）:
     - テストコード: test, spec, mock
     - デバッグ: debug, log
     - 一時的: temp, tmp, draft

影響範囲マッピング（サブエージェント内）:
   - ファイル単位の影響度集計
   - モジュール間依存関係の検出
   - 参照カウントの計算
```

## Output Format（出力形式）

```markdown
## 🔍 類似パターン検索結果

### 📊 概要
- 検索対象: [ファイル/パターン/シンボル]
- 検出箇所: N件
- 推奨アクション: [即座展開/要検討/影響なし]
- 🚀 コンテキスト効率: サブエージェント委譲で処理

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
- 低優先度: N件（テストコード、デバッグ用など）

### 📈 Next Steps
1. 高優先度N箇所を即座対応
2. 中優先度はパフォーマンステスト後に判断
3. 実装後に /gh:find-similar で再検証
```

## Tool Coordination

### v2.0 サブエージェント委譲パターン

```yaml
メインコンテキスト（軽量）:
  Phase 1:
    - 入力解析（パターン/シンボル抽出）
    - 検索パラメータ生成
    - Task tool起動準備

  Phase 2:
    - Task(subagent_type="Explore") 起動
    - サブエージェント完了を待機

  Phase 3:
    - JSONサマリー受信
    - Markdown整形
    - ユーザー表示

Exploreサブエージェント（独立コンテキスト）:
  - Serena MCPアクティブ化
  - find_symbol: シンボル名検索
  - search_for_pattern: パターン検索
  - find_referencing_symbols: 参照追跡
  - 優先度スコアリング
  - JSONサマリー生成 → 返却

補完ツール（必要時のみ）:
  - Grep: Serena検索の補完
  - Read: 詳細コンテキスト確認（サブエージェント内）
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

## 実行指示（重要）- v2.0 サブエージェント委譲パターン

**あなたは今、`/gh:find-similar` コマンドを実行しています。**

### 🚀 v2.0 実行フロー（コンテキスト効率化）

**v2.0では検索処理をExploreサブエージェントに委譲し、メインコンテキストを軽量に保ちます。**

### Step 1: パターン抽出（メインコンテキスト・軽量）

```yaml
入力から検索パラメータを抽出:
  - ファイルパス → パス文字列
  - 自然言語 → キーワード
  - --symbol → シンボル名
  - --pattern → 正規表現

結果:
  search_params = {
    "type": "symbol" | "pattern" | "file",
    "query": "抽出したクエリ",
    "scope": "file" | "module" | "project"
  }
```

### Step 2: Exploreサブエージェント起動（🔴 必須）

```yaml
Task(
  subagent_type: "Explore",
  model: "sonnet",  # 高速処理
  prompt: |
    ## 類似パターン検索タスク

    **検索パラメータ**:
    - Type: {type}
    - Query: "{query}"
    - Scope: {scope}

    **実行手順**:
    1. Serena MCPをアクティブ化（mcp__serena__activate_project）
    2. 以下の検索を実行（独立なら並列）:
       - mcp__serena__find_symbol("{query}", substring_matching=True)
       - mcp__serena__search_for_pattern("{regex_pattern}")
       - mcp__serena__find_referencing_symbols（シンボル発見時）

    3. 検出箇所を優先度評価:
       - 🔴高: auth, validation, security, database
       - 🟡中: service, controller, business
       - 🟢低: test, debug, utils

    4. 結果をJSON形式で返却（⚠️厳守）

    **返却形式（これ以外は返さない）**:
    ```json
    {
      "summary": {
        "total_matches": N,
        "high_priority": N,
        "medium_priority": N,
        "low_priority": N,
        "recommendation": "即座展開" | "要検討" | "影響なし"
      },
      "high_priority": [
        {
          "path": "src/auth/login.ts",
          "line": 45,
          "snippet": "function getUserData()...",
          "reason": "認証系コンポーネント",
          "ref_count": 12
        }
      ],
      "medium_priority": [...],
      "low_priority_count": N,
      "patterns_found": ["pattern1", "pattern2"]
    }
    ```
)
```

### Step 3: 結果受信とレポート生成（メインコンテキスト）

```yaml
サブエージェントからJSONサマリーを受信:
  - 全検索結果は含まれない（コンテキスト節約）
  - サマリーのみ（~1000 tokens）

Markdown形式でレポート整形:
  - 優先度別セクション
  - Next Steps提案
  - GitHub Issue連携オプション
```

### 🔴 重要: 並列実行の指示

```yaml
サブエージェント内での並列実行:
  - find_symbol と search_for_pattern は独立 → 並列実行可能
  - find_referencing_symbols はシンボル発見後 → 順次実行

メインでの並列実行:
  - 複数パターンを調査する場合、複数のExploreサブエージェントを並列起動可能
```

### ⚠️ コンテキスト効率の維持

```yaml
やること:
  ✅ Task(subagent_type="Explore") でSerena検索を委譲
  ✅ サブエージェントにJSON形式での返却を指示
  ✅ メインではサマリーのみ処理

やらないこと:
  ❌ メインコンテキストでSerena検索を直接実行
  ❌ 全検索結果をメインに返却させる
  ❌ サブエージェントに冗長なテキストを返却させる
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

**Last Updated**: 2025-11-28
**Version**: 2.0.0
