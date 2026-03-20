#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
export PYTHONPATH=superprism_poc/raidguild/code

bash scripts/agent_unpause_sync.sh knowledge

LOCK_RESOURCE="repo_write"
LOCK_HOLDER="knowledge-agent"

python3 -m tools.agent_coord acquire \
  --resource "${LOCK_RESOURCE}" \
  --holder "${LOCK_HOLDER}" \
  --ttl-minutes 120 \
  --note "heartbeat-knowledge-run"

cleanup() {
  python3 -m tools.agent_coord release \
    --resource "${LOCK_RESOURCE}" \
    --holder "${LOCK_HOLDER}" || true
}
trap cleanup EXIT

python3 scripts/knowledge_promote_inbox.py

python3 -m community_knowledge validate --base superprism_poc --space raidguild
python3 -m community_knowledge index --base superprism_poc --space raidguild

echo "[knowledge-start] recent activity:"
tail -n 12 superprism_poc/raidguild/knowledge/kb/activity/kb_activity.jsonl || true

GIT_SYNC_PATHS=(
  "superprism_poc/raidguild/knowledge/kb/activity"
  "superprism_poc/raidguild/knowledge/kb/indexes"
  "superprism_poc/raidguild/knowledge/kb/state"
  "superprism_poc/raidguild/knowledge/kb/triage"
)

git add "${GIT_SYNC_PATHS[@]}" || true
if git diff --cached --quiet -- "${GIT_SYNC_PATHS[@]}"; then
  echo "[knowledge-start] no repo changes to commit"
  git restore --staged "${GIT_SYNC_PATHS[@]}" 2>/dev/null || true
else
  RUN_TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  git commit -m "[knowledge] Sync ${RUN_TS}" -- "${GIT_SYNC_PATHS[@]}"
  git push origin main
fi

