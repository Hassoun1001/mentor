#!/usr/bin/env bash
# mentor-autodeploy — the server's half of the autonomous-maintenance loop.
#
# Cron runs this every 10 minutes. The maintenance agent pushes to GitHub;
# this pulls, refuses anything that touches what only a human may change,
# deploys, proves the new build healthy, and rolls back on its own if it is
# not. Between deploys it is a watchdog: an app that stops answering is
# restarted. Every deploy, refusal, rollback and restart reaches the owner on
# Telegram.
#
# THE INSTALLED COPY IS THE ONE THAT RUNS. Cron calls
# /usr/local/bin/mentor-autodeploy, installed by hand from ops/autodeploy.sh.
# A bad push therefore cannot disable the thing that rolls bad pushes back.
#
# Usage:
#   mentor-autodeploy                     # what cron runs
#   mentor-autodeploy --allow-protected   # a human on SSH, deploying a change
#                                         # to protected files on purpose
set -euo pipefail

REPO=/opt/mentor
STATE=/var/lib/mentor-autodeploy
LOG=/var/log/mentor-autodeploy.log
COMPOSE=(docker compose -f docker-compose.caddy.yml)
HEALTH_WAIT_SECONDS=300   # a cold build boots, migrates, and loads models
SETTLE_SECONDS=75         # startup jobs kick at 45 s; let them run once
WATCHDOG_STRIKES=3        # consecutive failed checks (~30 min) before a restart
LOG_MAX_BYTES=5000000

# Only a human changes these. Infrastructure is the safety net itself; the
# constants are the honesty gates. An agent told to "improve" will otherwise
# find that lowering a bar makes the numbers look better — exactly the
# self-deception the system exists to prevent.
PROTECTED_PATHS='^(ops/|docker-compose[^/]*\.ya?ml$|Caddyfile$|Dockerfile$|backend/Dockerfile$|\.github/|backend/tests/test_honesty_gates_pinned\.py$)'
WRITABLE_EXCEPTIONS='^ops/autonomy/LOG\.md$'
PROTECTED_CONSTANTS='_PROMOTION_MARGIN|_COIN_FLIP_BRIER|_BASELINE_FLOOR|_MIN_COVERAGE|MIN_COVERAGE|_DEMOTION_AFTER|_SELECTION_FOLDS|_MIN_GAIN|_MIN_SENSIBLE_STOP_PIPS|_EXTREME_LEVERAGE|MIN_WINDOWS|_MAX_BREAKEVEN|_COIN_FLIP|_Z|MIN_SAMPLE_FOR_VERDICT|_PUBLICATION_LAG|spread_pips|slippage_pips'

ALLOW_PROTECTED=0
[[ "${1:-}" == "--allow-protected" ]] && ALLOW_PROTECTED=1

mkdir -p "$STATE"
exec 9>"$STATE/lock"
flock -n 9 || exit 0   # a deploy is already running
cd "$REPO"

if [[ -f "$LOG" && $(stat -c %s "$LOG") -gt $LOG_MAX_BYTES ]]; then
  tail -n 4000 "$LOG" >"$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi

log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" >>"$LOG"; }

notify() {
  # The bot credentials stay on this box: read from the app's .env and never
  # echoed. curl does not log the URL.
  local token chat
  token=$(sed -n 's/^TELEGRAM_BOT_TOKEN=//p' .env | tr -d '"' | head -n 1 || true)
  chat=$(sed -n 's/^TELEGRAM_CHAT_ID=//p' .env | tr -d '"' | head -n 1 || true)
  [[ -n "$token" && -n "$chat" ]] || return 0
  curl -s -m 20 -o /dev/null "https://api.telegram.org/bot${token}/sendMessage" \
    --data-urlencode "chat_id=${chat}" --data-urlencode "text=$1" || true
}

app_answers() {
  # $@: API paths that must answer 200 from inside the container. Content is
  # not judged — a stale weekend feed is not a broken build — only that the
  # code paths run.
  local paths=("$@")
  "${COMPOSE[@]}" exec -T app python - "${paths[@]}" >/dev/null 2>&1 <<'PY'
import sys
import urllib.request

for path in sys.argv[1:]:
    with urllib.request.urlopen("http://127.0.0.1:8000" + path, timeout=90) as r:
        if r.status != 200:
            sys.exit(1)
PY
}

watchdog() {
  # Liveness only: the cheap endpoint stays responsive even mid-retrain, so a
  # long training run can never look like a hang and get itself killed.
  if app_answers /api/v1/health; then
    rm -f "$STATE/strikes"
    return 0
  fi
  local n
  n=$(( $(cat "$STATE/strikes" 2>/dev/null || echo 0) + 1 ))
  echo "$n" >"$STATE/strikes"
  log "watchdog: app not answering ($n/$WATCHDOG_STRIKES)"
  if (( n >= WATCHDOG_STRIKES )); then
    "${COMPOSE[@]}" restart app >>"$LOG" 2>&1 || true
    rm -f "$STATE/strikes"
    log "watchdog: restarted app"
    notify "🔁 Mentor stopped answering for about $(( n * 10 )) minutes, so it was restarted automatically."
  fi
}

protected_violations() {
  # $1..$2: commit range. Prints a reason per violation; empty means clean.
  local from=$1 to=$2 files
  files=$(git diff --name-only "$from" "$to" | grep -Ev "$WRITABLE_EXCEPTIONS" || true)
  grep -E "$PROTECTED_PATHS" <<<"$files" | sed 's/^/protected file: /' || true
  git diff -U0 "$from" "$to" -- 'backend/src' \
    | grep -E "^[-+][[:space:]]*($PROTECTED_CONSTANTS)[[:space:]]*(:[^=]*)?=" \
    | grep -Ev '^(\+\+\+|---)' | sed 's/^/protected constant: /' || true
  git diff -U0 "$from" "$to" -- 'backend/tests' 'frontend/src' \
    | grep -E '^\+.*(pytest\.mark\.(skip|xfail)|pytest\.skip\(|\.skip\(|xit\(|xdescribe\()' \
    | sed 's/^/skipped test: /' || true
  git diff --name-only --diff-filter=D "$from" "$to" -- 'backend/tests' \
    | sed 's/^/deleted test file: /' || true
}

deploy_tree() {
  "${COMPOSE[@]}" build app >>"$LOG" 2>&1 && "${COMPOSE[@]}" up -d app >>"$LOG" 2>&1
}

healthy_after_deploy() {
  local since=$1 deadline=$(( SECONDS + HEALTH_WAIT_SECONDS ))
  until app_answers /api/v1/health /api/v1/health/report; do
    (( SECONDS < deadline )) || return 1
    sleep 10
  done
  sleep "$SETTLE_SECONDS"
  # Answering is not enough if it is crashing on the side.
  if "${COMPOSE[@]}" logs --since "$since" app 2>&1 | grep -q 'Traceback'; then
    log "traceback after deploy"
    return 1
  fi
  app_answers /api/v1/health /api/v1/health/report
}

if ! git fetch -q origin main 2>>"$LOG"; then
  log "fetch failed"
  watchdog
  exit 0
fi

local_sha=$(git rev-parse HEAD)
remote_sha=$(git rev-parse origin/main)

if [[ "$local_sha" == "$remote_sha" ]]; then
  watchdog
  exit 0
fi

# Already refused or rolled back: wait for a newer push.
if [[ "$(cat "$STATE/bad" 2>/dev/null || true)" == "$remote_sha" && $ALLOW_PROTECTED -eq 0 ]]; then
  watchdog
  exit 0
fi

if ! git merge-base --is-ancestor "$local_sha" "$remote_sha"; then
  log "refusing non-fast-forward ${local_sha:0:7} -> ${remote_sha:0:7}"
  echo "$remote_sha" >"$STATE/bad"
  notify "🛑 Mentor did not deploy ${remote_sha:0:7}: history was rewritten on GitHub (not a fast-forward). A human needs to look."
  watchdog
  exit 0
fi

subjects=$(git log --format='• %s' "$local_sha..$remote_sha" | head -n 8 || true)
violations=$(protected_violations "$local_sha" "$remote_sha")
if [[ -n "$violations" && $ALLOW_PROTECTED -eq 0 ]]; then
  log "refusing ${remote_sha:0:7}: $(tr '\n' ';' <<<"$violations")"
  echo "$remote_sha" >"$STATE/bad"
  notify "🛑 Mentor refused to deploy ${remote_sha:0:7} — it changes things only a human may change:
$(head -n 6 <<<"$violations")
Still running ${local_sha:0:7}."
  watchdog
  exit 0
fi

changed=$(git diff --name-only "$local_sha" "$remote_sha")
git merge -q --ff-only "$remote_sha"

if ! grep -qvE '(\.md$|^ops/autonomy/)' <<<"$changed"; then
  log "docs-only update to ${remote_sha:0:7}; no rebuild"
  exit 0
fi

if grep -q '^backend/alembic/versions/' <<<"$changed"; then
  log "schema change: backing up the database first"
  if ! /opt/mentor/backup.sh >>"$LOG" 2>&1; then
    git reset -q --hard "$local_sha"
    echo "$remote_sha" >"$STATE/bad"
    log "backup failed; not deploying ${remote_sha:0:7}"
    notify "🛑 Mentor did not deploy ${remote_sha:0:7}: it changes the database and the safety backup failed."
    exit 1
  fi
fi

started=$(date -u +%FT%TZ)
log "deploying ${local_sha:0:7} -> ${remote_sha:0:7}"
if deploy_tree && healthy_after_deploy "$started"; then
  rm -f "$STATE/bad" "$STATE/strikes"
  log "deployed ${remote_sha:0:7}"
  notify "🚀 Mentor updated itself to ${remote_sha:0:7}:
$subjects"
  exit 0
fi

log "${remote_sha:0:7} unhealthy; rolling back to ${local_sha:0:7}"
git reset -q --hard "$local_sha"
deploy_tree || true
echo "$remote_sha" >"$STATE/bad"
if app_answers /api/v1/health /api/v1/health/report; then
  notify "↩️ Mentor tried ${remote_sha:0:7}, it failed its health check, and it rolled itself back to ${local_sha:0:7}. Nothing is broken; the change waits for a fix:
$subjects"
else
  notify "🚨 Mentor rolled back ${remote_sha:0:7} but ${local_sha:0:7} is not answering either. This needs a human."
fi
exit 1
