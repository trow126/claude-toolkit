# GitHub Issue駆動開発システム

壁打ち → Issue化 → タスク化 → 進捗管理を実現するClaude Code拡張機能

## 何ができるか

**3つの核心機能**:
1. **壁打ち → Issue化**: `/gh:brainstorm`で要件整理 → `/gh:issue create`でGitHub Issue作成
2. **Issue → TodoWrite変換**: `/gh:issue work <number>`でIssueタスクをTodoWriteに自動変換
3. **自動進捗同期**: TodoWrite完了 → GitHub自動更新 → 全完了でIssue自動クローズ

**なぜ使うか**:
- Issue駆動開発を自然な会話フローで実現
- TodoWriteで作業するだけでGitHub自動同期
- セッション間での作業継続性を確保
- 完了後の振り返りを自動記録

## クイックスタート

### 最小手順（3ステップ）

```bash
# 1. アイデアを整理（任意）
/gh:brainstorm "ユーザー認証機能"
# → 対話的に要件整理 → claudedocs/brainstorm/*.md に保存

# 2. Issue作成
/gh:issue create --from-file claudedocs/brainstorm/jwt_auth_requirements_20251031.md
# または
/gh:issue create "タイトル" "説明"
# → GitHub Issue #42 作成完了

# 3. 作業開始
/gh:issue work 42
# → TodoWriteタスク自動生成 → 進捗追跡有効化 → 実装開始
```

### 自動で起こること

**`/gh:issue work 42`実行時**:
1. Issue #42のタスクリスト解析（`- [ ]`抽出）
2. 未完了タスクのみTodoWriteに変換
3. 進捗追跡バックグラウンド起動

**TodoWriteでタスク完了時**:
1. 完了を自動検知
2. GitHub Issue #42にコメント投稿（進捗%）
3. 全タスク完了時 → Issue自動クローズ

## コマンド一覧

### Issue作成・表示

| コマンド | 用途 | 例 |
|---------|------|-----|
| `/gh:issue create` | Issue作成 | `create "タイトル"` |
| `/gh:issue create --from-file` | ファイルからIssue作成 | `--from-file claudedocs/brainstorm/feature.md` |
| `/gh:issue list` | Issue一覧表示 | `list --mine` |
| `/gh:issue view <N>` | Issue詳細表示 | `view 42` |

### Issue作業

| コマンド | 用途 | 例 |
|---------|------|-----|
| `/gh:issue work <N>` | 作業開始（TodoWrite変換） | `work 42` |
| `/gh:issue status <N>` | 進捗確認 | `status 42` |
| `/gh:issue sync <N>` | 手動同期 | `sync 42` |
| `/gh:issue close <N>` | Issue完了・振り返り | `close 42` |

### 壁打ち・企画

| コマンド | 用途 | 例 |
|---------|------|-----|
| `/gh:brainstorm` | 対話的要件整理 | `brainstorm "新機能"` |
| `/gh:guide` | ワークフロー完全ガイド | `guide` |
| `/gh:usage` | ユースケース集 | `usage` |

### ログ分析・検証

| コマンド | 用途 | 例 |
|---------|------|-----|
| `/gh:verify <path>` | ログ分析・検証 | `verify /var/log/app.log --mode verify` |
| `/gh:verify --mode detect` | 異常検出 | `verify /var/log/app.log --mode detect` |
| `/gh:verify --mode debug` | デバッグ支援 | `verify /var/log/error.log --issue 42` |

### 類似パターン検索

| コマンド | 用途 | 例 |
|---------|------|-----|
| `/gh:find-similar <target>` | 水平展開調査 | `find-similar src/auth/login.ts` |
| `/gh:find-similar --symbol` | シンボル検索 | `find-similar --symbol validateUser` |
| `/gh:find-similar --pattern` | パターン検索 | `find-similar --pattern "if.*==.*null"` |

## 詳細ドキュメント

**コマンド詳細**: 各コマンドの全オプションとフラグ
→ [issue.md](./.claude/commands/gh/issue.md)

**完全ワークフローガイド**: 壁打ちからクローズまでの詳細手順
→ `/gh:guide` コマンド実行

**ユースケース集**: 実践的な利用シーンと例
→ `/gh:usage` コマンド実行

**Skills詳細**:
- **issue-parser**: `.claude/skills/issue-parser/SKILL.md`
- **issue-todowrite-sync**: `.claude/skills/issue-todowrite-sync/SKILL.md`
- **progress-tracker**: `.claude/skills/progress-tracker/SKILL.md`
- **issue-retrospective**: `.claude/skills/issue-retrospective/SKILL.md`
- **log-verifier**: `.claude/skills/log-verifier/SKILL.md`

## アーキテクチャ概要

### v2.0 サブエージェント委譲パターン

**コンテキスト効率化**: 重い処理をサブエージェントに委譲し、メインコンテキストを軽量に保つ設計

```
┌─────────────────────────────────────────────────────┐
│  メインコンテキスト（軽量）                            │
│  ├─ ユーザー入力解析                                  │
│  ├─ サブエージェント起動                              │
│  └─ 結果サマリー受信                                  │
└─────────────────────────────────────────────────────┘
                        ↓ 委譲
┌─────────────────────────────────────────────────────┐
│  サブエージェント（独立コンテキスト）                   │
│  ├─ 大量データ読み込み                                │
│  ├─ 検索・分析処理                                    │
│  └─ JSONサマリー生成 → 返却                          │
└─────────────────────────────────────────────────────┘
```

**適用コマンド**:
- `/gh:find-similar` - 70-80%コンテキスト削減（~20K → ~1.5K tokens）
- `/gh:verify` - 90%コンテキスト削減（~50K → ~2.5K tokens）

### 基本構造

```
/gh:issue work 42 (ユーザー)
    ↓
Task Tool → Agent
    ↓
Skills順次実行:
├─ issue-parser (Issue解析)
├─ issue-todowrite-sync (TodoWrite変換)
└─ progress-tracker (進捗監視)
```

### コンポーネント役割

**スラッシュコマンド** (`.claude/commands/gh/issue.md`)
- ユーザーインターフェース
- Task toolによるagent委譲
- オプション・フラグ処理

**Skills** (`.claude/skills/`)
- `issue-parser`: Issueタスクリスト解析
- `issue-todowrite-sync`: Issue ⇄ TodoWrite双方向同期
- `progress-tracker`: 完了検知・GitHub更新
- `issue-retrospective`: 完了時振り返り記録

**自動化ポイント**:
- Skills実行は全自動（明示的起動不要）
- 進捗同期はバックグラウンド
- 全完了検知で自動クローズ

## セッション管理

### 推奨パターン（同一セッション完結）

```bash
/gh:issue work 42
(全タスク実装・完了)
# → 自動的にIssue更新・クローズ ✅
```

### セッション間作業

```bash
# セッション1
/gh:issue work 42
(2タスク完了、終了)

# セッション2（別日）
/gh:issue work 42  # 再実行で最新状態取得
# → 残りタスクがTodoWriteに復元
(残りタスク完了)
# → 自動クローズ ✅
```

**重要**: `work`コマンド再実行でGitHubから最新進捗を取得するため、セッション間の作業継続が安全。

## トラブルシューティング

### GitHub認証エラー
```bash
gh auth login
gh auth status  # 確認
```

### 進捗が同期されない
```bash
/gh:issue sync 42  # 手動同期
/gh:issue status 42 --refresh  # 強制更新
```

### Skillsが起動しない
- コマンド再実行: `/gh:issue work 42`
- 明示的言及: "use issue-parser skill"

### 完了タスクがTodoWriteに表示される
- `[x]`マークされたタスクは自動除外される
- GitHub Issue本文で`[x]`が正しくマークされているか確認

## Tips

**💡 Tip 1**: `/gh:issue work <number>` だけで全自動セットアップ

**💡 Tip 2**: TodoWriteで作業するだけでGitHub自動更新

**💡 Tip 3**: `/gh:brainstorm` → `--from-file` が最強の壁打ちフロー

**💡 Tip 4**: 同一セッション完結が最も効率的

**💡 Tip 5**: `work`コマンド再実行でセッション間継続可能

**💡 Tip 6**: 完了時の振り返りは自動記録（GitHub + `claudedocs/learnings.md`）

**💡 Tip 7**: Brainstormファイルは対応Issueクローズ時に自動削除

## 関連リソース

**公式ドキュメント**:
- コマンドリファレンス: `/gh:issue --help`
- ワークフローガイド: `/gh:guide`
- ユースケース集: `/gh:usage`

**ファイル構成**:
```
.claude/
├── commands/gh/
│   ├── README.md (このファイル)
│   ├── issue.md (コマンド実装)
│   ├── guide.md (詳細ガイド)
│   ├── usage.md (ユースケース)
│   ├── brainstorm.md (壁打ちコマンド)
│   ├── verify.md (ログ分析コマンド・v2.0)
│   └── find-similar.md (類似パターン検索・v2.0)
│
└── skills/
    ├── issue-parser/
    ├── issue-todowrite-sync/
    ├── progress-tracker/
    ├── issue-retrospective/
    └── log-verifier/
```

---

**バージョン**: 2.0.0
**最終更新**: 2025-11-28
