---
name: coderabbit
description: "sc:analyzeベースにCodeRabbit観点を追加したコードレビュー。見落とされがちなリファクタリング指摘を拾い上げる"
---

# /gh:coderabbit - CodeRabbitスタイル コードレビュー

sc:analyzeをベースに、CodeRabbitが指摘するパターンを検出するコードレビューコマンド。
PRで採用されなかったリファクタリング等の指摘を改めて拾い上げる。

## Triggers
- PR作成前の事前レビュー
- リファクタリング対象の洗い出し
- コード品質改善の優先度付け
- CodeRabbitが指摘しそうな問題の事前検出

## Usage
```
/gh:coderabbit [target] [--focus quality|security|performance|architecture|refactor|all] [--depth quick|deep]
```

## Behavioral Flow

1. **Discover** [継承: sc:analyze]: ファイル発見・言語検出・プロジェクト構造分析
2. **Lint** [追加]: `ruff check --output-format=json` を実行してRuff検出結果を取得
3. **Scan** [継承+拡張]:
   - sc:analyze のドメイン別分析（quality/security/performance/architecture）
   - CodeRabbitパターン検出（後述のチェックリスト参照）
4. **Evaluate** [継承]: 重要度評価（High/Medium/Low）
5. **Recommend** [継承]: アクション提案
6. **Report** [継承]: 結果出力

## Tool Coordination

- **Bash**: `ruff check --output-format=json [target]` 実行
- **Glob**: ファイル発見とプロジェクト構造分析
- **Grep**: パターン検索（ゼロ除算候補、MIN_CELLS定義等）
- **Read**: ソースコード精査

## CodeRabbit パターンチェックリスト

### Ruff自動検出ルール
以下のルールは `ruff check` で自動検出する：

| ルール | 説明 | 頻度 |
|--------|------|------|
| FBT001, FBT002 | Boolean位置引数（キーワード専用化推奨） | 高 |
| ANN202, ANN204 | 戻り値型アノテーション欠落 | 高 |
| PIE790 | 不要な `pass` 文 | 高 |
| RUF022 | `__all__` ソート順 | 中 |
| RUF043 | 正規表現にraw文字列未使用 | 中 |
| RUF100 | 未使用 `noqa` ディレクティブ | 低 |
| G004 | f-string使用のログ文 | 中 |
| TRY003 | 例外メッセージの外部化 | 低 |

### 手動検出パターン

#### 1. 入力検証・エラーハンドリング
| パターン | 検出方法 | 説明 |
|---------|---------|------|
| ゼロ除算リスク | Grep: `/ (count\|total\|len\([^)]+\)\|original_\w+)` | count=0 のケースでエラー |
| Off-by-one | Grep: `MIN_CELLS\s*=\s*\d+` + 最大インデックス確認 | MIN_CELLS = max_index + 1 が必要 |
| 範囲検証欠落 | Read: 関数シグネチャ確認 | val_ratio: 0-1, 長さ一致チェック |
| フォールバック欠落 | Read: symlink_to, 外部API呼び出し | 失敗時の代替処理 |

#### 2. 型アノテーション改善
| パターン | 検出方法 | 説明 |
|---------|---------|------|
| `Path` vs `str \| Path` | Grep: `def \w+\([^)]*:\s*Path[^|]` | API一貫性のため `str \| Path` 推奨 |
| `__init__` 戻り値型 | Grep: `def __init__\([^)]*\):` (-> None なし) | ANN204違反 |

#### 3. テスト改善
| パターン | 検出方法 | 説明 |
|---------|---------|------|
| NaNエッジケース | Grep tests/: `np\.nan\|NaN` | NaN値のテストがあるか |
| KeyErrorエッジケース | Grep tests/: `KeyError\|存在しない` | 存在しないカラムのテスト |
| 空データエッジケース | Grep tests/: `empty\|空\|len\(.*\)\s*==\s*0` | 空リスト/DataFrame のテスト |
| shape検証 | Grep tests/: `\.shape\s*==` | ndimだけでなくshapeも検証 |

#### 4. 構造・パフォーマンス
| パターン | 検出方法 | 説明 |
|---------|---------|------|
| テスト内inline import | Grep tests/: `def test_.*:.*from \w+ import` | モジュールレベルに移動推奨 |
| コード重複 | Read: 類似コードブロック | 共通関数抽出 |
| 大規模データ対応 | Read: リスト内包表記で全件ロード | ジェネレータ/遅延読み込み推奨 |

#### 5. ドキュメント整合性
| パターン | 検出方法 | 説明 |
|---------|---------|------|
| API不整合 | Read: docsのコード例 vs 実装 | ドキュメントと実際のAPIの乖離 |
| `__getattr__` 不発火 | Read: 直接import + `__getattr__` 定義 | 非推奨警告が回避される |

## 出力フォーマット

```markdown
## /gh:coderabbit レビュー結果: [target]

### 概要
- 対象ファイル: X件
- Ruff検出: Y件
- 手動検出: Z件

### Ruff検出
| ファイル | 行 | ルール | 説明 |
|---------|---|--------|------|
| file.py | 42 | FBT001 | Boolean位置引数を使用 |

### CodeRabbitパターン検出

#### ゼロ除算リスク
- `batch.py:285` - `filtered_count / original_count` で original_count=0 の可能性

#### Off-by-one
- `types.py:212` - MIN_CELLS=20 だが最大index=20なので21が必要

#### 型ヒント改善
- `selector.py:41` - `Path` のみだが `str | Path` が望ましい

#### テスト改善候補
- `test_arrays.py` - NaN値のエッジケーステストがない

### 優先度
1. High: Off-by-one（実行時エラーの可能性）
2. Medium: ゼロ除算ガード
3. Low: 型ヒント改善（リファクタリング）
```

## Examples

### プロジェクト全体のレビュー
```
/gh:coderabbit
# プロジェクト全体をCodeRabbit観点でレビュー
# Ruff検出 + 手動パターン検出
```

### 特定ディレクトリのレビュー
```
/gh:coderabbit src/data
# src/data ディレクトリのみをレビュー
```

### リファクタリングフォーカス
```
/gh:coderabbit --focus refactor
# 型アノテーション、コード構造、パターン改善に特化
```

### クイックチェック
```
/gh:coderabbit --depth quick
# Ruff検出のみ、手動パターン検出はスキップ
```

## sc:analyze との関係

| 観点 | sc:analyze | /gh:coderabbit |
|------|-----------|----------------|
| Ruff連携 | 暗黙的 | 明示的に実行・結果統合 |
| パターン検出 | 一般的品質問題 | CodeRabbit固有パターン |
| 優先度基準 | セキュリティ > 品質 | 実行時エラー > リファクタリング |
| ユースケース | 定期的品質監査 | PR前事前レビュー |

## Boundaries

**Will:**
- `ruff check` を実行してRuffルール違反を検出
- CodeRabbitが指摘するパターンを手動で検出
- 重要度に基づいた優先度付け
- 具体的な修正箇所の提示

**Will Not:**
- コードの自動修正（提案のみ）
- 実行時テスト（静的解析のみ）
- 外部サービス連携（CodeRabbit APIは使用しない）
- セキュリティ脆弱性の深い分析（sc:analyze --focus security を使用）
