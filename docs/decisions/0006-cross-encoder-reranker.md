# 6. Rerank the fused candidates with bge-reranker-base

Status: accepted, 2026-11-23.

## Context

Hybrid search puts the right passage in the top five but often not at rank one. A
cross-encoder reads the question and passage together and orders candidates better, at a
latency cost. Two CPU-friendly models were compared through fastembed (ONNX):
`Xenova/ms-marco-MiniLM-L-6-v2` (upstream model Apache-2.0; the Xenova conversion card lists
no license) and `BAAI/bge-reranker-base` (MIT).

## Decision

The top 20 fused candidates are rescored by `BAAI/bge-reranker-base`. It was chosen by the
pre-registered rule ([8](0008-pre-registered-selection-rules.md)): on dev its nDCG@10 was
0.843 against MiniLM's 0.833, just past the 0.01 tie margin, so p95 latency did not decide.

## Consequences

- p95 search latency is about 2.7 s on CPU against 0.6 s for MiniLM.
- On held-out bge again led: nDCG@10 0.834 against 0.811 for MiniLM, MRR@5 0.861 against 0.833.
- Changing the reranker requires re-tuning the rerank gate on dev.
- Evidence: `reports/retrieval_dev.md`, `reports/retrieval_heldout.md`.
