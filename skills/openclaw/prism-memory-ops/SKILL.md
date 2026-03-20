---
name: prism-memory-ops
description: Operate and recover the Prism Memory pipeline in this repo. Use when asked to run collector/digest/memory/seeds/backup, diagnose stale state or long collector runs, reconcile branch drift between automation and canonical main, or validate activity/state outputs after refactors.
---

# Prism Memory Ops

Run and stabilize the Prism pipeline with minimal noise and strong auditability.

## Workflow
1. Confirm branch and drift before any run.
2. Run the narrowest command needed (`collect`, `digest`, `memory`, `seeds`, `backup`, then `run`).
3. Validate `activity.jsonl`, `collector_state.json`, and changed output files.
4. Report exact dates, run keys, and files touched.

## Operational Rules
- Prefer `collect` for ingestion checks; avoid full `run` unless schedule behavior is being tested.
- Use `--force` only when re-normalizing historical outputs or validating refactor effects.
- Keep collector cadence aligned in both:
  - `superprism_poc/raidguild/config/space.json`
  - `superprism_poc/raidguild/state/collector_state.json`
- Treat `activity/activity.jsonl` as append-only audit history; never drop events during conflict resolution.
- If branch divergence exists with automation, merge `origin/main` first, resolve state/activity conflicts deterministically, then push.

## Validation Checklist
- Collector:
  - `state.discord_latest.last_until` moved forward.
  - New raw files only for non-empty windows.
- Digest:
  - Generated only for buckets with raw data on target date.
  - `.md` and `.json` both present.
- Memory:
  - `memory/rolling/<date>.{md,json}` and `latest.{md,json}` updated together.
- Seeds:
  - Daily: `products/suggestions/<date>.md`
  - Weekly: `products/suggestions/weekly-YYYY-WW.md`
- Backup:
  - `github.backup.completed` event exists when backup runs.

## References
- Load [references/commands.md](references/commands.md) for command patterns.
- Load [references/conflicts.md](references/conflicts.md) for conflict resolution policy.
