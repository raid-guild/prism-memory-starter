#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
export PYTHONPATH=superprism_poc/raidguild/code

bash scripts/agent_unpause_sync.sh memory

TODAY=$(TZ=America/Denver date +%F)
LOCAL_TIME=$(TZ=America/Denver date +%H:%M)
LOCK_RESOURCE="repo_write"
LOCK_HOLDER="memory-agent"

python3 -m tools.agent_coord acquire \
  --resource "${LOCK_RESOURCE}" \
  --holder "${LOCK_HOLDER}" \
  --ttl-minutes 120 \
  --note "heartbeat-memory-run"

cleanup() {
  python3 -m tools.agent_coord release \
    --resource "${LOCK_RESOURCE}" \
    --holder "${LOCK_HOLDER}" || true
}
trap cleanup EXIT

python3 -m community_memory.pipeline collect --base superprism_poc --space raidguild

if [[ "${LOCAL_TIME}" > "17:29" ]]; then
  python3 -m community_memory.pipeline digest --base superprism_poc --space raidguild --date "${TODAY}"
fi

if [[ "${LOCAL_TIME}" > "17:44" ]]; then
  python3 -m community_memory.pipeline memory --base superprism_poc --space raidguild --date "${TODAY}"
  python3 -m community_memory.pipeline seeds --base superprism_poc --space raidguild --date "${TODAY}"
fi

if [[ "${LOCAL_TIME}" > "18:04" ]]; then
  python3 -m community_memory.pipeline backup --base superprism_poc --space raidguild
fi

echo "[memory-start] recent activity:"
tail -n 8 superprism_poc/raidguild/activity/activity.jsonl

GIT_SYNC_PATHS=(
  "superprism_poc/raidguild/activity"
  "superprism_poc/raidguild/buckets"
  "superprism_poc/raidguild/memory"
  "superprism_poc/raidguild/products"
  "superprism_poc/raidguild/state"
)

git add "${GIT_SYNC_PATHS[@]}" || true
if git diff --cached --quiet -- "${GIT_SYNC_PATHS[@]}"; then
  echo "[memory-start] no repo changes to commit"
  git restore --staged "${GIT_SYNC_PATHS[@]}" 2>/dev/null || true
else
  RUN_TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  git commit -m "[memory] Sync ${RUN_TS}" -- "${GIT_SYNC_PATHS[@]}"
  git push origin main
fi

