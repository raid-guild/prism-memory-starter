# Retrieval Rules

For knowledge answers:

1. Search first.
2. Read the top matching docs.
3. Answer from returned document content and metadata.
4. Include the exact document slug or path used.

For memory answers:

1. Prefer digests for day-scoped activity.
2. Use rolling memory for compact narrative state.
3. Use participant queries for who-was-active questions.

When confidence is limited:

- name the empty or missing endpoint result
- state the exact date window or filters used
- avoid implying data exists when the API returned none
