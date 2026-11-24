# 5. Fuse BM25 and dense retrieval with reciprocal rank fusion

Status: accepted, 2026-11-23.

## Context

BM25 (SQLite FTS5) finds exact API names such as `SetVariantSelection`; dense retrieval
(`nomic-embed-text:v1.5` in embedded Qdrant) finds paraphrases. Their scores are on
unrelated scales, so they cannot simply be added.

## Decision

Hybrid search takes the top 50 candidates from each retriever and combines them with
reciprocal rank fusion, `score = Σ 1 / (60 + rank)`. Only ranks are used, so neither score
needs calibrating against the other.

## Consequences

- On dev, hybrid reached hit@5 1.000 against 0.885 (BM25) and 0.923 (dense); on held-out it
  matched both at 0.833 and had the best nDCG@10 of the three (0.781).
- RRF removes the dense cosine from the fused score, so the refusal gate needs its own
  signal ([7](0007-refusal-gates.md)).
- Latency stays low (p95 under 20 ms on dev) because both retrievers run locally.
