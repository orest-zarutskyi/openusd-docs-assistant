# 8. Fix the selection rules before running the comparisons

Status: accepted, 2026-11-23.

## Context

With small question sets, it is easy to pick whichever configuration looks best and then
explain the choice afterwards. Writing the rule first makes the choice reproducible from the
report alone.

## Decision

- **Retrieval mode.** Highest dev nDCG@10. Modes within 0.01 of the best are decided by the
  lower p95 latency.
- **`top_k`.** The smallest of 3, 5 and 8 whose dev hit rate for the chosen mode is within one
  question of its hit@10. The result was 8.
- **Reasoning variant per model.** Score = (answerable questions answered with valid
  citations + correct refusals) / 2. Variants within one answerable question of the best are
  decided by lower p50 latency. The judge is deliberately not used, so the judge cannot
  influence which answers it later grades.
- **Held-out.** `--final` applies the frozen dev settings and selects nothing. The retrieval
  report marks the deployed mode instead of a winner and fits no thresholds.

## Consequences

- The rule picked bge over MiniLM despite its higher latency
  ([6](0006-cross-encoder-reranker.md)). It also picked Flash-Lite's default thinking over
  `level=low`: they were within one question, and the default was faster.
- Evidence: `reports/retrieval_dev.md`, `reports/variants_dev.md`.
