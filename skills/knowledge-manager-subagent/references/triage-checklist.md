# Archivist of the Keep Checklist

Reference this whenever the knowledge-manager sub-agent needs to triage, validate, and index evergreen knowledge in this repo.

## Canonical docs
- `docs/assistants/knowledge-manager/IDENTITY.md`
- `docs/assistants/knowledge-manager/HEARTBEAT.md`
- `docs/knowledge-source-of-truth.md`

## Workflow summary
1. **Repo prep**
   - work from repo root
   - `git status`, `git pull`
   - Confirm the knowledge inbox path: `superprism_poc/raidguild/knowledge/kb/triage/inbox/`
2. **Triage queue**
   - Sort incoming capsules by freshness/priority.
   - Reject items that lack metadata or fail validation; leave reviewer notes in-place.
3. **Metadata + validation**
   - Normalize authors, dates, tags per `docs/knowledge-source-of-truth.md` schemas.
   - Run automated validation scripts when available; otherwise note what was manually checked.
4. **Index/update**
   - Apply changes only to the knowledge-owned directories (evergreen KB + search indexes).
   - Keep memory-pipeline artifacts read-only (never modify Maester’s outputs in-place).
5. **Publish + logging**
   - Record which capsules advanced, which were rejected, and any schema migrations performed.
   - Provide diffs/paths back to the orchestrator for visibility.

## Common commands
- `bash scripts/knowledge_start.sh` – run the full knowledge workflow.
- `bash scripts/agent_unpause_sync.sh knowledge` – resume after a pause.
- `bash scripts/agent_pause.sh knowledge` – halt gracefully.

## Reporting template
- Commit SHA + branch
- Inbox volume processed
- Accepted vs rejected counts (with reasons)
- Index files touched
- Follow-ups needed (schema tweaks, missing context, requests to Maester)
