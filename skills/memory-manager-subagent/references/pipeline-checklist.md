# Maester Raida Pipeline Checklist

Use this as a quick reference when the Memory Manager sub-agent needs to operate the collector -> digest -> memory -> seeds -> backup workflow in this repo.

## Canonical docs
- `docs/assistants/memory-manager/IDENTITY.md`
- `docs/assistants/memory-manager/HEARTBEAT.md`
- `README.md`

## Operational steps
1. **Pre-flight**
   - work from repo root
   - Ensure the repo is clean and up to date (`git status`, `git pull`).
   - Confirm required env vars (notably `MEETINGS_LATEST_URL`) point to the live endpoint before running `scripts/memory_start.sh`.
2. **Resume / unpause**
   - `bash scripts/agent_unpause_sync.sh memory`
   - `bash scripts/memory_start.sh`
   - Capture the commit SHA and note first-run output for the orchestrator.
3. **Pause**
   - `bash scripts/agent_pause.sh memory`
   - Verify paused state via the script output.
4. **Collector failures**
   - Inspect `superprism_poc/raidguild/memory/logs/` for the broken collector.
   - Re-run only the failing stage (e.g., `scripts/memory_collect.sh`) to avoid stomping healthy steps.
5. **Hand-off to knowledge lane**
   - Only drop knowledge-ready artifacts into `superprism_poc/raidguild/knowledge/kb/triage/inbox/`.
   - Never touch the Archivist’s canonical knowledge paths directly.

## Reporting back to the orchestrator
- Always summarize: current commit, which stages ran, success/failure per stage, and any artifacts/handoffs.
- Flag blockers immediately (missing env vars, auth failures, corrupt inbox items, etc.).
