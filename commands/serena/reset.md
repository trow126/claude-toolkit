---
name: serena:reset
description: "Serenaメモリの完全リセットと再オンボーディングを実行"
---

# /serena:reset - 完全リセット実行

このコマンドは以下を自動実行する。確認は不要。

## 実行手順

### Step 1: CLAUDE.md退避（循環参照防止）

```bash
mv CLAUDE.md CLAUDE.md.bak
```

### Step 2: 全メモリ削除

Call MCP tool: `mcp__serena__list_memories`
→ 返されたメモリ全てに対して:
Call MCP tool: `mcp__serena__delete_memory`
Parameters: memory_file_name (各メモリ名)

### Step 3: 再オンボーディング

Call MCP tool: `mcp__serena__onboarding`
→ 指示に従ってプロジェクト分析を完了

### Step 4: CLAUDE.md復元

```bash
mv CLAUDE.md.bak CLAUDE.md
```

### Step 5: .coderabbit.yaml 検証・更新

`.coderabbit.yaml` がプロジェクト構造と同期しているか検証し、必要に応じて更新する。

#### 5-1: 前提チェック

```bash
git remote -v
```

→ リモートがなければスキップ（CodeRabbit不要）

#### 5-2: 存在確認と分岐

```bash
ls .coderabbit.yaml
```

→ 存在する → 5-3（検証）へ
→ 存在しない → 5-4（新規生成）へ

#### 5-3: 検証（既存ファイル）

以下を並列で実行:

1. **path_instructions検証**: 各エントリのpathパターンに対して `Glob` でファイル存在確認
   - マッチ0件 → 古いパス（削除候補）
2. **path_filters検証**: 以下のベンダーディレクトリをスキャン
   - `.venv/`, `node_modules/`, `vendor/`, `contracts/lib/`, `contracts/out/`, `contracts/cache/`, `dist/`, `build/`
   - 存在するのにpath_filtersに未登録 → フィルタ追加候補
3. **コードディレクトリ網羅性**: トップレベルで `.py`, `.sol`, `.ts`, `.js` を含むディレクトリを検出
   - path_instructionsに未登録のコードディレクトリ → 追加候補

差分がなければ「変更不要」で完了。差分があれば更新を適用。

#### 5-4: 新規生成（ファイル未存在時）

共通ベーステンプレートで生成:

```yaml
# yaml-language-server: $schema=https://coderabbit.ai/integrations/schema.v2.json
language: ja
reviews:
  profile: assertive
  high_level_summary: true
  poem: false
  auto_review:
    enabled: true
    drafts: false
    base_branches: []
  path_instructions:
    # ← プロジェクト分析結果から言語別に生成
  path_filters:
    - "!**/*.lock"
    - "!**/__pycache__/**"
    - "!.git/**"
    # ← 検出されたベンダーディレクトリを追加
early_access: false
chat:
  auto_reply: true
issues:
  enabled: false
issue_enrichment:
  auto_enrich:
    enabled: false
```

`path_instructions` は検出言語に応じて生成:

| 言語 | 指示内容 |
|------|---------|
| Python (`*.py`) | 型ヒント推奨、ロギング%sフォーマット、エラーハンドリング |
| Solidity (`*.sol`) | リエントランシー、ガス効率、アクセス制御 |
| TypeScript/JavaScript | 型安全性、async/awaitパターン |
| YAML configs | 設定値妥当性、セキュリティ確認 |

### Step 6: CLAUDE.md最新化（オプション）

```bash
claude init
```

最新のSerena memoriesを参照してCLAUDE.mdを更新。

### Step 7: 完了報告

- 削除したメモリ数
- 新規作成されたメモリ
- onboarding結果サマリー
- .coderabbit.yaml: 変更なし / 更新済み（差分概要） / 新規生成 / スキップ（リモートなし）

---

## 参考: 循環参照問題

CLAUDE.mdを退避する理由:

- onboardingがCLAUDE.mdを参照すると古い情報がmemoriesに混入
- コードのみから分析させることでクリーンな状態を構築
