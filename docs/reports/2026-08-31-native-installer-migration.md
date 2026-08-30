# Claude Code native installer 移行記録

GitHub Issue #5「`claude doctor` の auto-update warning を解消する」に対応し、Claude Code の正本を npm global 版から native installer 版へ移す。この判断の source は、2026-08-31 の `/gh-roadmap-drive 13` で行った Issue #5 judgment gate。repository 側では手順・診断・証跡欄を用意し、binary の導入と npm package の削除は owner が通常の shell で実施する。

## 移行前

2026-08-31 時点の `claude` は `$HOME/.npm-global/bin/claude` から解決され、npm global prefix は user-owned の `~/.npm-global`。PATH は `~/.npm-global/bin` が `~/.local/bin` より先にあるため、npm package を残すと native launcher が shadow される。

`claude doctor </dev/null` で確認済みの行は次のとおり。

```text
Config install method: global
Auto-updates: enabled
Last update attempt: success → 2.1.251 (2026-08-29)
No installation issues found
```

2026-08-30 audit の「npm global folder isn't writable」warning は現在は再現しない。

## 移行手順

実行中の Claude session 内ではなく、owner が通常の shell で実行する。

```bash
curl -fsSL https://claude.ai/install.sh | bash
npm uninstall -g @anthropic-ai/claude-code
hash -r
command -v claude                 # ~/.local/bin/claude
claude --version
claude doctor </dev/null          # auto-update warning がないこと
scripts/check-runtime.sh
```

native installer の launcher は `~/.local/bin/claude`。実体は `~/.local/share/claude/versions/` 配下にあり、background で auto-update する。即時更新は `claude update`、最後の更新試行は `claude doctor </dev/null` で確認できる。

## 移行後の evidence

owner が 2026-08-31 に通常の shell で移行を実施し、同日の Claude session から read-only で再確認した出力を記録する。

| 確認項目 | 出力 |
|---|---|
| `command -v claude` | `$HOME/.local/bin/claude`（symlink → `$HOME/.local/share/claude/versions/2.1.251`）。npm package `@anthropic-ai/claude-code` は `~/.npm-global` から削除済み |
| `claude --version` | `2.1.251 (Claude Code)` |
| `claude doctor </dev/null` | `Running: native (2.1.251)` / `Config install method: native` / `Auto-updates: enabled` / `Auto-update channel: latest` / `Last update attempt: success → 2.1.251 (2026-08-29)` / `No installation issues found.`（auto-update warning なし） |
| `scripts/check-runtime.sh` | `OK: Claude Code 2.1.251 (>= 2.1.219, stable)` / `NOTE: claude は native installer の launcher ($HOME/.local/bin/claude) から解決されています。`（exit 0） |

Issue #5 の acceptance criteria（auto-update warning なしの `claude doctor`、期待 version、bootstrap 規約への手順記録）は、上記4項目の記録をもって 2026-08-31 に検証済みとする。
