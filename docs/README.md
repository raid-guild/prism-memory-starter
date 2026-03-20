# Prism Memory API

A lightweight FastAPI service exposes memory and knowledge artifacts from `superprism_poc/raidguild/`.

## Paths & auth

All data endpoints require an API key header:

```
X-Prism-Api-Key: <your-key>
```

| Endpoint | Auth | Description |
| --- | --- | --- |
| `GET /health` | none | Service heartbeat |
| `GET /memory/latest` | required | Latest rolling memory JSON |
| `GET /memory/date/{yyyy-mm-dd}` | required | Rolling memory snapshot for a date |
| `GET /digests/date/{yyyy-mm-dd}` | required | Aggregated digests across buckets |
| `GET /digests/bucket/{bucket}/date/{yyyy-mm-dd}` | required | Single bucket digest |
| `GET /activity/recent?limit=100&type=...` | required | Activity log tail with optional filters |
| `GET /products/suggestions/latest` | required | Latest daily product suggestion JSON |
| `GET /products/suggestions/date/{yyyy-mm-dd}` | required | Daily product suggestion JSON for a date |
| `GET /products/suggestions/weekly/{yyyy-ww}` | required | Weekly product suggestion JSON |
| `GET /knowledge/docs/{slug}` | required | Fetch a knowledge doc (markdown + metadata) by slug or path |
| `GET /knowledge/search?q=...&kind=...` | required | Simple manifest search with optional filters (kind, tag, entity, limit) |
| `GET /knowledge/indexes/manifest` | required | Raw manifest index JSON |
| `GET /knowledge/indexes/tags` | required | Tag → docs lookup table |
| `GET /knowledge/indexes/entities` | required | Entity → docs lookup table |
| `POST /knowledge/inbox` | required | Drop a markdown + metadata pair into `knowledge/kb/triage/inbox/` |
| `POST /memory/inbox` | required | Drop a JSON payload into `inbox/memory/incoming/` for the inbox collector |

## Running locally

```bash
export OPENCLAW_MEMORY_API_KEY="replace-me"
export PYTHONPATH=superprism_poc/raidguild/code
python3 -m superprism_poc.raidguild.code.community_memory_api.server \
  --host 127.0.0.1 --port 8788 --base superprism_poc --space raidguild
```

Example request:

```bash
curl -H "X-Prism-Api-Key: replace-me" http://127.0.0.1:8788/memory/latest
```

Product suggestion example:

```bash
curl -H "X-Prism-Api-Key: replace-me" \
  http://127.0.0.1:8788/products/suggestions/latest
```

### POST /knowledge/inbox

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-Prism-Api-Key: replace-me" \
  http://127.0.0.1:8788/knowledge/inbox \
  -d '{
    "filename": "playbook.md",
    "content": "# Title\nBody...",
    "metadata": {
      "title": "Ops Playbook",
      "slug": "ops-playbook",
      "kind": "guide",
      "summary": "How to run ops",
      "tags": ["operations"],
      "owners": ["ops-team"],
      "status": "draft",
      "audience": "internal",
      "stability": "evolving",
      "updated": "2026-03-01",
      "entities": [],
      "related_docs": [],
      "triaged_at": "2026-03-08T19:25:00Z"
    }
  }'
```

### POST /memory/inbox

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-Prism-Api-Key: replace-me" \
  http://127.0.0.1:8788/memory/inbox \
  -d '{
    "source": "ops-digest",
    "ts": "2026-03-08T19:30:00Z",
    "type": "summary",
    "content": "Key decisions from the ops huddle...",
    "bucket": "knowledge",
    "author": "ops-lead",
    "url": "https://example.com/ops-notes"
  }'
```
