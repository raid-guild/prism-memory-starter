# Ingest Contracts

Memory inbox example:

```json
{
  "source": "discord-agent",
  "ts": "2026-03-23T18:00:00Z",
  "type": "summary",
  "content": "Key decisions from the guild ops sync...",
  "bucket_hint": "guildhq",
  "author": "ops-bot",
  "participants": ["alice", "bob"],
  "participant_count": 2
}
```

Knowledge inbox example:

```json
{
  "filename": "ops-playbook.md",
  "content": "# Ops Playbook\n\nBody...",
  "metadata": {
    "title": "Ops Playbook",
    "slug": "ops-playbook",
    "kind": "guide",
    "summary": "How to run core guild ops.",
    "tags": ["operations", "workflow"],
    "owners": ["ops-team"],
    "status": "draft",
    "audience": "internal",
    "stability": "evolving",
    "updated": "2026-03-23",
    "entities": [],
    "related_docs": [],
    "triaged_at": "2026-03-23T18:00:00Z"
  }
}
```
