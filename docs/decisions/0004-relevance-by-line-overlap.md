# 4. Count a retrieved chunk as relevant when it overlaps an expected span

Status: accepted, 2026-11-23.

## Context

Expected sources are line spans, and chunk boundaries do not line up with them. Requiring a
chunk to contain the whole span penalises a retriever for how the chunker happened to cut a
long passage.

## Decision

A chunk is relevant if it shares at least one line with any expected or alternative span of
the question. The stricter rule (the chunk contains the whole span) is still reported as
`hit@5 strict`. nDCG@10 uses binary gains, normalised by the number of relevant chunks in the
corpus.

## Consequences

- Metrics reward finding the right passage, not the exact chunking.
- A very large chunk that touches a span counts as a hit even if the answer is elsewhere in
  it; the strict column shows how often that matters.
- Evidence: `reports/retrieval_dev.md`, `reports/retrieval_heldout.md`.
