# UserPromptSubmit 進め方 reminder の実装結果

GitHub Issue #3 と tracking Issue #13 に従い、`prompt-submit-hook.sh` を managed policy の UserPromptSubmit に登録した。hook が返す plain text は次の2文だけである。

> 着手前に成功条件を決め、単一ownerで探索・実装・検証まで完遂する。
> 完了判定は一次情報・diff・test結果で自己監査し、未検証項目は明示する。

## H-015〜H-018 との対応

1文目の「成功条件」は H-015、「単一ownerで探索・実装・検証まで完遂」は H-017 と H-016 を圧縮している。2文目の一次情報・diff・test結果による自己監査は H-018、未検証項目の明示は H-016 に対応する。文面は tracking Issue #13 が H-015〜H-018 の入力として確定したものを、そのまま採用した。

内容は `shared/rules/core-contract.md` の6行目と10行目、`claude/CLAUDE.md` の19行目に重なる。これらの always-on copy が引き続き正本であり、UserPromptSubmit 層はルールを置き換えない。各発話から作業へ移る時点で、成功条件と完了根拠を短く思い出させるための action-time reminder である。

## 出力境界と測定値

`scripts/measure-hook-injection.py .` の fixture 実測では、`user_prompt_submit_injection_typical_bytes` は末尾改行込み198 bytes。script 内の `MAX_INJECTION_BYTES=256` を上限とし、全文が超えた場合は切り詰めずに出力全体を破棄する。hook は stdin の内容に依存せず、入力不正や空入力でも exit 0 で同じ文面を返す delivery 用 fail-open とした。

出力は76文字で、日本語と短い英字を含むため概算では約60〜80 tokens。tokenizer による厳密値ではなく、per-prompt 負荷の目安である。

## live 確認

repository 内の source と fixture だけでは、実行中 session の transcript に managed hook が反映されたかまでは確認できない。owner が `sudo scripts/install-managed-policy.sh --apply` で managed policy を再導入した後、新しい Claude Code session の log で各 prompt への注入を確認する必要がある。
