# Prism Memory Conflict Policy

## `activity/activity.jsonl`

- Treat as append-only event history.
- During merge conflicts, preserve records from both sides.
- De-duplicate exact duplicate JSON events only.
- Keep chronological ordering by `ts` after merge.

## `state/collector_state.json`

- Keep the newest trustworthy `last_until`.
- Keep configured `window_minutes` from canonical ops decision.
- Do not roll cursor backward unless explicitly performing controlled replay.

## Branch Cutover

1. Pause external automation writers.
2. Merge `origin/main` into working branch.
3. Resolve `activity` and `state` per rules above.
4. Push working branch to `main`.
5. Resume automation after confirming new `main` SHA.
