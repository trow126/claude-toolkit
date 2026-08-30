# PostToolUse lint 型フィードバック hook 実装結果

GitHub Issue #2 の初期対象 H-001〜H-003 を `post-edit-lint-hook.sh` に移した。Edit / Write 後の対象ファイルだけを検査し、確定した違反は exit 2 で同じ turn の編集 agent へ返す。入力不正、依存欠落、削除済みファイル、内部例外は無出力の exit 0 とした。

## 検査内容と境界

1. Markdown は ATX 見出し、行頭 `|` が連続するテーブル、backtick / tilde の fenced code block の前後を検査する。YAML front matter と fenced code block 内部は対象外。ファイル先頭・末尾と除外領域の境界は空行として扱う。
2. Python は `ast.parse` が返す `SyntaxError` だけを報告する。ruff / mypy の指摘、意味上の誤り、実行時例外は扱わない。
3. `.claude/` 配下、または本 repository の `claude/` 直下にある3種の settings JSON を検査する。`Tool:*` は allow / ask / deny、no-space wildcard は allow だけが対象。`Bash(git:*)` は legacy-equivalent、`Bash(git *)` は canonical 表記として許可する。

JSON parse error も lint 違反にはしない。hook 自体の異常で編集を止めないための fail-open 境界であり、settings の構造検証は既存の managed policy gate が担う。

## Rule byte 数

`wc -c` の実測。Python rule は変更していない。

| file | before | after |
|---|---:|---:|
| `shared/rules/markdown-rules.md` | 104 | 142 |
| `claude/rules/markdown.md` | 343 | 381 |
| `claude/rules/settings-syntax.md` | 4009 | 4054 |

## Metrics

after は `scripts/measure-metrics.sh --repo .` の実測値。

| metric | before | after |
|---|---:|---:|
| `claude_always_on_total` | 4413 | 4413 |
| `combined_always_on_total` | 7839 | 7839 |
| `shared_rules_on_demand_bytes` | 10407 | 10445 |

独立した Python helper も inventory に登録したため、`inventory_audited_elements` の実測値は 162。`hook_scripts` は 8、`hook_registrations` は 10 になった。

## 手動 acceptance

`mktemp -d` 内に前後の空行がない見出しを作り、hand-built PostToolUse JSON を stdin へ渡した。exit code は 2、stdout は 0 bytes。stderr は次のとおり。

```text
post-edit-lint: /tmp/tmp.YX7f7CMc8v/broken.md:2: Markdown 見出しの前に空行がありません — 見出しの直前に空行を追加する
post-edit-lint: /tmp/tmp.YX7f7CMc8v/broken.md:2: Markdown 見出しの後に空行がありません — 見出しの直後に空行を追加する
意図的な場合はレポートにその理由を書くこと。
```
