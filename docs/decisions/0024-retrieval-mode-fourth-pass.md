# 24. Choose the retrieval mode for the fourth pass by a rule fixed in advance

Status: proposed, 2026-11-26. The candidates and rule below were committed before the comparison ran.

## Context

The reranker was chosen in the first pass on 31 dev questions
([6](0006-cross-encoder-reranker.md)): `bge-reranker-base` led `ms-marco-MiniLM-L-6-v2` by 0.010
nDCG@10. On held-out v3 the order reversed: MiniLM scored nDCG@10 0.601 and bge 0.557, below plain
hybrid at 0.559 ([retrieval_heldout_v3.md](../../reports/pass3/retrieval_heldout_v3.md)). bge
also takes about 2.6 s per query on the CPU, against about 0.6 s for MiniLM.

This comparison was prompted by those held-out v3 numbers. Those 60 questions are now part of dev
([23](0023-fourth-pass-split.md)), so the comparison is a dev result. It is validated only on a
new held-out set.

## Candidates

Only models already in the local cache are compared:

- `hybrid`: RRF over the top 50 BM25 and dense candidates, no reranker;
- `hybrid-rerank` with `Xenova/ms-marco-MiniLM-L-6-v2` over the top 20;
- `hybrid-rerank` with `BAAI/bge-reranker-base` over the top 20 (current).

`top_k` stays 8.

## Selection rule

1. Run `eval-retrieval` for the three candidates on the 175 dev questions in one session.
2. Apply the retrieval rule of [8](0008-pre-registered-selection-rules.md): highest nDCG@10;
   candidates within 0.01 of it are decided by the lower p95 latency.
3. If the chosen mode is not the current one, its refusal gate is set by the recall-first rule of
   [15](0015-refusal-gate-second-pass.md) on the 175 dev questions: midway between the lowest gate
   score of an answerable question and the next lower observed score. The gate score is the top
   cross-encoder score for a reranker, and the best dense cosine for `hybrid`.

Answer-level effects are not used for the choice. They are measured on dev with the chosen mode
and reported on the next held-out set.

## Result

Filled in after the comparison.
