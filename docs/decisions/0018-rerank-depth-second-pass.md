# 18. Choose the rerank depth for the second pass by a rule fixed in advance

Status: proposed, 2026-11-25. The candidates and rule below were committed before the comparison ran.

## Context

With the deployed retrieval (hybrid RRF, then `bge-reranker-base` over the top 20 fused
candidates), four answerable dev questions have no expected passage in the top 5. A stage-by-stage
trace shows why:

- `broadcast-edit` and `switchable-asset-root`: the expected passage sits at fused rank 34 and 43,
  so the reranker never sees it. Reranking the top 50 lifts them to rank 6 and 18.
- `working-set`: fused rank 4, reranked rank 8 at depth 20 and 6 at depth 50.
- `pre-post-visit`: reranked rank 6 at any depth.

Depth costs latency, because every extra candidate is one more cross-encoder pass on the CPU.

## Candidates

`rerank_depth` of 20 (current), 30 or 50. Everything else is unchanged: hybrid RRF over the top
50 BM25 and dense candidates, `bge-reranker-base`, `top_k` 8, gate −6.2459.

## Selection rule

1. Run `eval-retrieval --modes hybrid-rerank` with the bge reranker on the 55 dev questions at
   each depth.
2. Exclude a depth whose p95 latency exceeds twice the depth-20 p95 measured in the same session,
   so that `/ask` stays interactive.
3. Among the rest, apply the retrieval rule of [8](0008-pre-registered-selection-rules.md):
   highest nDCG@10; depths within 0.01 of it are decided by lower p95 latency.

Answer-level effects are not used for the choice. They are measured on held-out v2 with the frozen
second-pass settings.

## Consequences

Filled in after the comparison.
