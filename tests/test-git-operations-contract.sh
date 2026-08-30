#!/usr/bin/env bash
# test-git-operations-contract.sh — git-operations の context consumer と authority 契約を検証する。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONSUMERS="$REPO_ROOT/docs/contracts/context-consumers.tsv"
AUTHORITY="$REPO_ROOT/docs/contracts/skill-authority.tsv"
SKILL="$REPO_ROOT/shared/skills/git-operations/SKILL.md"

SANDBOX="$(mktemp -d)"
cleanup() { rm -rf "$SANDBOX"; }
trap cleanup EXIT

FAILURES=0
ok() { echo "ok: $1"; }
ng() {
  echo "FAIL: $1" >&2
  FAILURES=$((FAILURES + 1))
}

read_condition_for() {
  local skill_file="$1"
  awk '
    /git-workflow\.md/ { count++; condition = $0 }
    END {
      if (count != 1) exit 1
      print condition
    }
  ' "$skill_file"
}

check_skill_read_condition() {
  local skill_file="$1" mutating_modes="$2"
  local condition lower mode

  condition="$(read_condition_for "$skill_file")" || return 1
  [[ "$condition" == *"mutating Git operation"* ]] || return 1
  lower="$(tr '[:upper:]' '[:lower:]' <<< "$condition")"

  # Authority上の全mutating modeを一括で覆い、default/inspectionを非読込として明示する。
  [[ "$lower" == *'any mode other than `default`'* ]] || return 1
  if [[ ! "$lower" =~ (default|inspect(ion)?).*(does[[:space:]]+not|do[[:space:]]+not|must[[:space:]]+not|never).*load ]]; then
    return 1
  fi

  # 特定のmutating modeだけに限定された条件を許可しない。
  for mode in $mutating_modes; do
    if grep -Eq "(^|[^[:alnum:]_-])${mode}([^[:alnum:]_-]|$)" <<< "$lower"; then
      return 1
    fi
  done
}

# =========================================================================
# 1. context consumer contract
# =========================================================================
mapfile -t consumer_rows < <(
  awk -F '\t' '$1 == "git-workflow" && $3 == "skill:git-operations" { print $2 "\t" $4 }' "$CONSUMERS"
)
if [[ "${#consumer_rows[@]}" -eq 1 ]]; then
  ok "git-workflow / skill:git-operations のconsumer行が一意に存在する"
  IFS=$'\t' read -r load_mode trigger <<< "${consumer_rows[0]}"
  if [[ "$load_mode" == "on-demand" ]]; then
    ok "git-workflow はon-demandで読み込まれる"
  else
    ng "git-workflow のload_modeがon-demandではない: $load_mode"
  fi
  if [[ "$trigger" == "mutating git operation" ]]; then
    ok "git-workflow triggerがmutating git operationに限定されている"
  else
    ng "git-workflow triggerが不正: $trigger"
  fi
else
  ng "git-workflow / skill:git-operations のconsumer行が一意ではない: ${#consumer_rows[@]}件"
fi

# =========================================================================
# 2. SKILL.md read condition
# =========================================================================
if grep -Fq 'git-workflow.md' "$SKILL"; then
  ok "git-operations SKILL.mdがgit-workflow.mdを参照する"
else
  ng "git-operations SKILL.mdにgit-workflow.md参照がない"
fi

read_condition=""
if read_condition="$(read_condition_for "$SKILL")"; then
  if [[ "$read_condition" == *"mutating Git operation"* ]]; then
    ok "read conditionがmutating Git operationを明記する"
  else
    ng "read conditionがmutating Git operationを明記していない: $read_condition"
  fi
else
  ng "git-workflow.mdのread conditionを一意に取得できない"
fi

# =========================================================================
# 3. authorityからmutating / read-only modeを導出する
# =========================================================================
mode_classifications=""
if mode_classifications="$(awk -F '\t' '
  NR == 1 {
    for (i = 1; i <= NF; i++) {
      if ($i == "repo_write" || $i == "state_write" || $i == "commit" ||
          $i == "push" || $i == "github_write" || $i == "delete") {
        write_column[i] = 1
        write_column_count++
      }
    }
    if (write_column_count != 6) exit 2
    next
  }
  $1 == "git-operations" {
    allows_write = 0
    for (i in write_column) {
      if ($i == "allow") allows_write = 1
    }
    print (allows_write ? "mutating" : "read-only") "\t" $2
    mode_count++
  }
  END { if (mode_count == 0) exit 3 }
' "$AUTHORITY")"; then
  ok "authority headerから6つのwrite列を解決した"
else
  ng "authorityからgit-operations modeを導出できない"
fi

mutating_modes="$(awk -F '\t' '$1 == "mutating" { print $2 }' <<< "$mode_classifications" | sort | paste -sd ' ' -)"
read_only_modes="$(awk -F '\t' '$1 == "read-only" { print $2 }' <<< "$mode_classifications" | sort | paste -sd ' ' -)"

if [[ "$mutating_modes" == "branch commit merge push stage" ]]; then
  ok "write許可mode集合がbranch commit merge push stageである"
else
  ng "write許可mode集合が不正: $mutating_modes"
fi
if [[ "$read_only_modes" == "default" ]]; then
  ok "write非許可mode集合がdefaultだけである"
else
  ng "write非許可mode集合が不正: $read_only_modes"
fi

if check_skill_read_condition "$SKILL" "$mutating_modes"; then
  ok "read conditionが全mutating modeを覆いdefault/inspectionを除外する"
else
  ng "read conditionがauthority由来のmutating/read-only境界と一致しない"
fi

# =========================================================================
# 4. positive / negative fixtureでfail-closedを検証する
# =========================================================================
mutating_fixture="$SANDBOX/mutating-SKILL.md"
read_only_fixture="$SANDBOX/read-only-SKILL.md"
cp "$SKILL" "$mutating_fixture"
sed 's|^Read .*|Read `~/.agents/rules/git-workflow.md` before any Git operation.|' \
  "$SKILL" > "$read_only_fixture"

if check_skill_read_condition "$mutating_fixture" "$mutating_modes"; then
  ok "実SKILL.mdのmutating fixtureが契約検査を通る"
else
  ng "実SKILL.mdのmutating fixtureが契約検査に失敗する"
fi
if check_skill_read_condition "$read_only_fixture" "$mutating_modes"; then
  ng "any Git operationかつdefault除外なしのfixtureが契約検査を通過した"
else
  ok "any Git operationかつdefault除外なしのfixtureを拒否する"
fi

echo
if [[ "$FAILURES" -eq 0 ]]; then
  echo "PASS: all assertions succeeded"
  exit 0
else
  echo "FAIL: $FAILURES assertion(s) failed" >&2
  exit 1
fi
