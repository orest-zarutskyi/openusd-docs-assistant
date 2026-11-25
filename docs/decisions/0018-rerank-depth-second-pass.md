# 18. Choose the rerank depth for the second pass by a rule fixed in advance

Status: accepted, 2026-11-25: keep depth 20. The candidates and rule below were committed before the comparison ran (commit `61c7654`).

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

## Result

`reports/pass2/rerank_depth_{20,30,50}.md`, run one after another in the same session on the 55 dev
questions.

| Depth | hit@5 | MRR@5 | nDCG@10 | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- |
| **20** | 0.909 | 0.864 | 0.839 | 2525 | 2593 |
| 30 | 0.909 | 0.864 | 0.836 | 3838 | 3995 |
| 50 | 0.909 | 0.860 | 0.848 | 6279 | 6718 |

Depth 50 exceeds the latency cap (p95 6,718 ms against 2 × 2,593 ms). Even without the cap it is
within 0.01 nDCG@10 of depth 20, so the lower p95 would decide. The rule keeps **depth 20**.

## Consequences

- Deeper reranking moves individual expected passages up but does not change hit@5, and its nDCG
  gain is within noise at roughly 2.5 times the latency on a CPU.
- The four misses remain: two expected passages are outside the reranked set, and the others rank
  6 or 8, inside the context the model receives (`top_k` 8). On dev, Flash-Lite and qwen3:4b still
  answer `broadcast-edit` and `working-set` with valid citations from other retrieved passages.
- Retrieval changes that might help (query rewriting, a GPU reranker that makes depth 50 cheap,
  re-chunking very large chunks) are left for a later pass.
