# 7. Refuse at retrieval time with a per-mode score threshold

Status: accepted, 2026-11-23.

## Context

A small model given unrelated excerpts may still answer. Refusing before generation, when
nothing in the corpus is close to the question, is cheaper and safer than relying on the
model alone.

## Decision

Each mode has its own gate score: the top cosine for dense, the best dense cosine among the
fused candidates for hybrid, and the top cross-encoder score for rerank. BM25 has no
calibrated score and never refuses. The threshold is chosen on dev to maximise balanced
accuracy (answerable kept, unanswerable refused), placed midway between neighbouring
observed scores; ties go to the lower threshold, because the model can still refuse later.
`/ask` uses `rerank_min_score = -0.9831`.

## Consequences

- On dev the deployed gate kept 96% of answerable questions and refused all unanswerable ones.
- On held-out the frozen gate kept 16 of 18 answerable questions and refused 5 of 6
  unanswerable ones. The model refused the sixth itself.
- The gate is a corpus-coverage check, not a correctness check.
