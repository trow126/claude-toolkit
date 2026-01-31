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

### Step 5: 完了報告

- 削除したメモリ数
- 新規作成されたメモリ
- onboarding結果サマリー

---

## 参考: 循環参照問題

CLAUDE.mdを退避する理由:

- onboardingがCLAUDE.mdを参照すると古い情報がmemoriesに混入
- コードのみから分析させることでクリーンな状態を構築
