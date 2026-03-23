---
name: prism-api-reader
description: Read from the Prism Memory API using a read-only API key. Use when an agent needs rolling memory, digests, participant activity, knowledge search, knowledge docs, or product suggestion outputs without writing to inboxes or triggering ops endpoints.
---

# Prism API Reader

Use this skill for read-only retrieval against a deployed Prism API.

## Required auth

Send:

```text
X-Prism-Api-Key: <read-only-key>
```

Do not use write or ops endpoints with a read-only key.

## Base workflow

1. Start from the narrowest endpoint that can answer the question.
2. For knowledge questions, query indexes/search first, then fetch specific docs.
3. For recent community activity, prefer digests and participant queries over scanning raw memory.
4. Cite specific docs, dates, buckets, and endpoints used.

## Endpoint selection

- Latest memory snapshot:
  `GET /memory/latest`
- Memory for a day:
  `GET /memory/date/{yyyy-mm-dd}`
- Digest for a day:
  `GET /digests/date/{yyyy-mm-dd}`
- Digest for one bucket/day:
  `GET /digests/bucket/{bucket}/date/{yyyy-mm-dd}`
- Active participants in a time window:
  `GET /memory/participants?start=...&end=...&bucket=...`
- Knowledge manifest:
  `GET /knowledge/indexes/manifest`
- Knowledge search:
  `GET /knowledge/search?q=...&kind=...&tag=...&entity=...&limit=...`
- Knowledge doc:
  `GET /knowledge/docs/{slug}`
- Product suggestions:
  `GET /products/suggestions/latest`
  `GET /products/suggestions/date/{yyyy-mm-dd}`
  `GET /products/suggestions/weekly/{yyyy-ww}`

## Retrieval rules

- For knowledge:
  - use `/knowledge/search` first
  - then fetch the top matching docs with `/knowledge/docs/{slug}`
  - cite the returned `path`, `meta_path`, `title`, `kind`, and `updated` fields when relevant
- For participation questions:
  - use `/memory/participants`
  - report the exact `start` and `end` used
  - mention optional `bucket` scope explicitly
- For trend or summary questions:
  - compare multiple dates with `/digests/date/...` or `/memory/date/...`
  - do not infer cross-day changes from a single snapshot

## Safety

- Treat the API as the source of truth for current deployed state.
- If a route returns empty results, say so directly instead of inventing context.
- Do not call:
  - `/memory/inbox`
  - `/knowledge/inbox`
  - `/ops/*`

## References

- Load [references/endpoints.md](references/endpoints.md) for request patterns.
- Load [references/retrieval.md](references/retrieval.md) for answer construction rules.
