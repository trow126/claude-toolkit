---
name: serena:reset
description: "Serenaメモリの管理・削除・再オンボーディングガイド"
---

# /serena:reset - Serenaメモリ管理ガイド

## Serena MCP ツール一覧

| ツール | 機能 | 用途 |
|--------|------|------|
| `list_memories` | メモリ一覧取得 | 現状確認 |
| `read_memory` | メモリ読み込み | 内容確認 |
| `write_memory` | メモリ書き込み | 知識保存 |
| `delete_memory` | メモリ削除 | クリーンアップ |
| `edit_memory` | メモリ編集 | 部分更新 |
| `check_onboarding_performed` | オンボーディング状態確認 | 初期化チェック |
| `onboarding` | 再オンボーディング実行 | プロジェクト再分析 |

---

## 🔄 完全リセット手順（推奨）

**重要**: CLAUDE.mdを一時退避してからonboardingを実行。古いCLAUDE.mdの情報がmemoriesを汚染するのを防ぐ。

### ステップ1: CLAUDE.md退避（循環参照防止）

```bash
# CLAUDE.mdを一時退避（Serenaがコードのみから分析するため）
mv CLAUDE.md CLAUDE.md.bak
```

### ステップ2: 全メモリ削除

```
mcp__serena__list_memories()

# 各メモリに対して実行
mcp__serena__delete_memory("project_overview")
mcp__serena__delete_memory("code_style")
mcp__serena__delete_memory("suggested_commands")
mcp__serena__delete_memory("task_completion_checklist")
# ... 他のメモリも同様
```

### ステップ3: 再オンボーディング（コードのみから分析）

```
mcp__serena__onboarding()
```

これでSerenaが**コードのみ**から分析し、以下を自動生成:
- `project_overview` - プロジェクト概要
- `code_style` - コードスタイル規約
- `suggested_commands` - 推奨コマンド

### ステップ4: CLAUDE.md復元

```bash
# CLAUDE.mdを復元
mv CLAUDE.md.bak CLAUDE.md
```

### ステップ5: CLAUDE.md最新化（オプション）

```bash
# 最新のSerena memoriesを参照してCLAUDE.mdを更新
claude init
```

---

## ⚠️ 循環参照問題について

**問題**:
```
CLAUDE.md (古い)
    ↓ Serena onboarding参照
Serena memories (汚染)
    ↓ claude init参照
CLAUDE.md (汚染)
```

**解決**:
```
CLAUDE.md退避
    ↓
Serena memories削除
    ↓
onboarding（コードのみ分析）
    ↓
CLAUDE.md復元
    ↓
claude init（最新memories参照）
```

---

## 📋 メモリ確認

### 一覧表示

```
mcp__serena__list_memories()
```

### 内容確認

```
mcp__serena__read_memory("project_overview")
```

### オンボーディング状態確認

```
mcp__serena__check_onboarding_performed()
```

---

## 🗑️ 選択的削除

### 個別削除

```
mcp__serena__delete_memory("task_completion_checklist")
```

### 削除推奨対象

- ❌ `task_completion_checklist` - タスク状態
- ❌ 日付付きメモリ - 一時的な調査結果
- ❌ `checkpoint_*` - セッション状態

### 保持推奨対象

- ✅ `project_overview` - プロジェクト概要
- ✅ `code_style` - コードスタイル
- ✅ `suggested_commands` - 推奨コマンド

---

## 💡 ユースケース別手順

### 1. プロジェクト最新化（コード変更後）

```bash
# CLAUDE.md退避
mv CLAUDE.md CLAUDE.md.bak
```

```
# 古いメモリを削除
mcp__serena__delete_memory("project_overview")
mcp__serena__delete_memory("code_style")

# 再オンボーディング
mcp__serena__onboarding()
```

```bash
# CLAUDE.md復元
mv CLAUDE.md.bak CLAUDE.md
```

### 2. タスク状態のみクリア

```
mcp__serena__delete_memory("task_completion_checklist")
# project_overview等は保持、CLAUDE.md退避不要
```

### 3. 完全リセット（新規開始）

```bash
mv CLAUDE.md CLAUDE.md.bak
```

```
# 全メモリ削除後
mcp__serena__onboarding()
```

```bash
mv CLAUDE.md.bak CLAUDE.md
claude init  # CLAUDE.mdを最新化
```

---

## 🔧 自然言語でのリクエスト

MCPツールを直接呼ばない場合の表現:

| やりたいこと | 自然言語リクエスト |
|--------------|-------------------|
| メモリ一覧 | "Serenaメモリを一覧表示して" |
| メモリ読み込み | "project_overviewメモリを見せて" |
| メモリ削除 | "task_completion_checklistメモリを削除して" |
| 全削除 | "全Serenaメモリを削除して" |
| 再オンボーディング | "CLAUDE.mdを退避してSerenaのonboardingを実行して" |

---

## ⚠️ 注意事項

### 復元不可

削除したメモリは復元できません。重要な情報は:
- `claudedocs/` にMarkdownで保存
- Git commitメッセージに記録

### メモリの保存場所

```
.serena/memories/
├── project_overview.md
├── code_style.md
├── suggested_commands.md
└── task_completion_checklist.md
```

### gtr-startとの連携

`gtr-start` 実行時、masterの `.serena/memories/` がworktreeにコピーされます。
masterのmemoriesを最新化すると、以降のworktreeも最新状態で開始できます。

---


## 🎯 クイックリファレンス

```bash
# 完全リセット（推奨手順）
mv CLAUDE.md CLAUDE.md.bak
```

```
mcp__serena__list_memories()
mcp__serena__delete_memory("project_overview")
mcp__serena__delete_memory("code_style")
mcp__serena__delete_memory("suggested_commands")
mcp__serena__delete_memory("task_completion_checklist")
mcp__serena__onboarding()
```

```bash
mv CLAUDE.md.bak CLAUDE.md
claude init  # オプション: CLAUDE.md最新化
```

```
# 部分クリア（CLAUDE.md退避不要）
mcp__serena__delete_memory("task_completion_checklist")
```
