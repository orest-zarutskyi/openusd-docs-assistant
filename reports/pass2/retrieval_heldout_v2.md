# Retrieval: eval/heldout_v2.jsonl

- Date: 2026-11-25; code commit `f19ef49`.
- Corpus: OpenUSD v26.08 `ee47c679abde`, 76 documents, 952 chunks.
- Questions: `eval/heldout_v2.jsonl`, 60 total: 8 comparison, 28 lookup, 12 paraphrase, 12 unanswerable.
- Dense: `nomic-embed-text:v1.5` (digest `0a109f422b47`) on Ollama 0.40.18, embedded Qdrant, cosine similarity.
- Hybrid: RRF k=60 over the top 50 BM25 and dense candidates; rerank rescores the top 20 fused candidates with fastembed (ONNX, CPU).
- Machine: Windows 11, 32 logical CPUs (AMD Ryzen 9 7950X 16-Core Processor), GPU NVIDIA GeForce RTX 4070 Ti. Latency is wall time per query in one warm process.

Relevance: a chunk is relevant if it shares a line with an expected source span. `hit@5 strict` uses the stage-1 rule (the chunk contains the whole span).

| Mode | hit@5 | MRR@5 | nDCG@10 | hit@5 strict | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- | --- |
| bm25 | 0.667 | 0.527 | 0.589 | 0.667 | 1 | 2 |
| dense | 0.604 | 0.411 | 0.491 | 0.604 | 13 | 15 |
| hybrid | 0.729 | 0.519 | 0.586 | 0.729 | 16 | 18 |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | 0.646 | 0.545 | 0.618 | 0.646 | 527 | 538 |
| hybrid-rerank (bge-reranker-base) **(deployed)** | 0.750 | 0.615 | 0.672 | 0.750 | 2505 | 2564 |

Held-out run: every setting was frozen on dev (`reports/retrieval_dev.md`) and nothing below was selected on these questions. **(deployed)** marks the mode `/ask` uses.

## Hit rate by cut-off

| Mode | hit@1 | hit@3 | hit@5 | hit@8 | hit@10 |
| --- | --- | --- | --- | --- | --- |
| bm25 | 0.438 | 0.583 | 0.667 | 0.750 | 0.792 |
| dense | 0.292 | 0.500 | 0.604 | 0.729 | 0.729 |
| hybrid | 0.396 | 0.625 | 0.729 | 0.792 | 0.792 |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | 0.458 | 0.646 | 0.646 | 0.771 | 0.812 |
| hybrid-rerank (bge-reranker-base) | 0.521 | 0.729 | 0.750 | 0.833 | 0.854 |

top_k for `/ask`: **8**, frozen on dev.

## Refusal gate

Thresholds are the dev settings `/ask` applies (`min_score` for dense and hybrid, `rerank_min_score` for the deployed reranker); a mode with no frozen threshold shows none. BM25 has no calibrated score, so it cannot refuse at retrieval time.

| Mode | Gate score | Threshold | Answerable kept | Unanswerable refused |
| --- | --- | --- | --- | --- |
| bm25 | none | — | 1.000 | 0.000 |
| dense | top cosine | 0.6891 | 0.750 | 0.583 |
| hybrid | best dense cosine | 0.6891 | 0.729 | 0.583 |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | top cross-encoder score | not frozen on dev | — | — |
| hybrid-rerank (bge-reranker-base) | top cross-encoder score | -6.2459 | 0.917 | 0.167 |

## Missed at 5

| Mode | Questions |
| --- | --- |
| bm25 | `v2-01`, `v2-03`, `v2-07`, `v2-11`, `v2-17`, `v2-18`, `v2-20`, `v2-22`, `v2-24`, `v2-30`, `v2-36`, `v2-38`, `v2-39`, `v2-45`, `v2-52`, `v2-53` |
| dense | `v2-03`, `v2-04`, `v2-05`, `v2-07`, `v2-11`, `v2-15`, `v2-17`, `v2-18`, `v2-20`, `v2-22`, `v2-24`, `v2-26`, `v2-30`, `v2-38`, `v2-42`, `v2-45`, `v2-47`, `v2-49`, `v2-57` |
| hybrid | `v2-03`, `v2-04`, `v2-05`, `v2-07`, `v2-11`, `v2-16`, `v2-17`, `v2-18`, `v2-20`, `v2-30`, `v2-38`, `v2-45`, `v2-57` |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | `v2-03`, `v2-05`, `v2-07`, `v2-11`, `v2-16`, `v2-17`, `v2-18`, `v2-20`, `v2-22`, `v2-24`, `v2-30`, `v2-38`, `v2-45`, `v2-49`, `v2-51`, `v2-52`, `v2-56` |
| hybrid-rerank (bge-reranker-base) | `v2-03`, `v2-05`, `v2-07`, `v2-11`, `v2-17`, `v2-18`, `v2-20`, `v2-22`, `v2-30`, `v2-38`, `v2-49`, `v2-58` |
