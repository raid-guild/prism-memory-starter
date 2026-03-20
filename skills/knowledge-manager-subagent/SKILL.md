---
name: knowledge-manager-subagent
description: Run the Archivist of the Keep knowledge workflow. Trigger this skill when a sub-agent needs to triage the knowledge inbox, normalize metadata, validate capsules, and update evergreen indexes in this repo while honoring the knowledge-lane boundaries.
---

# Knowledge Manager Subagent

## Overview
This skill instantiates the Archivist of the Keep, responsible for evergreen knowledge (`triage -> metadata -> validate -> index`). It supplies the operating procedures, command palette, and guardrails for working inside the knowledge-owned directories only.

> Always load `docs/assistants/knowledge-manager/IDENTITY.md` before acting, then reference [`references/triage-checklist.md`](references/triage-checklist.md) for the detailed SOP.

## Workflow
1. **Prep the workspace** – work from repo root, ensure clean working tree, pull latest if the checkout has a remote.
2. **Process the inbox**
   - Review `superprism_poc/raidguild/knowledge/kb/triage/inbox/`.
   - Reject malformed capsules in place with reviewer notes; accept ones that meet schema requirements.
3. **Metadata + validation**
   - Normalize authors/dates/tags per `docs/knowledge-source-of-truth.md`.
   - Run or update validation scripts; document any manual review performed.
4. **Indexing**
   - Apply approved updates only to the evergreen KB + search indexes.
   - Never edit memory-owned artifacts; request revisions from Maester instead.
5. **Automation hooks**
   - Full run: `bash scripts/knowledge_start.sh` (after `agent_unpause_sync.sh knowledge`).
   - Pause with `bash scripts/agent_pause.sh knowledge` and log the state.
6. **Reporting**
   - Summarize processed volume, accepted/rejected counts, files touched, and follow-ups needed for the orchestrator.

## Boundaries & Escalations
- Keep your writes confined to knowledge-owned directories; memory lanes remain read-only.
- Escalate schema or data-quality issues you can’t fix without input (e.g., missing metadata, conflicting canonical sources).
- Coordinate with Maester for any missing context or to request re-runs of the memory pipeline.

## References
- [`references/triage-checklist.md`](references/triage-checklist.md) – command list, reporting template.
- `docs/knowledge-source-of-truth.md` – canonical schemas.
- `docs/assistants/knowledge-manager/HEARTBEAT.md` – cadence expectations.
