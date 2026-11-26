# Retrieval: eval/heldout_v4.jsonl

- Date: 2026-11-26; code commit `e60e40a`.
- Corpus: OpenUSD v26.08 `ee47c679abde`, 76 documents, 952 chunks.
- Questions: `eval/heldout_v4.jsonl`, 46 total: 8 lookup, 20 paraphrase, 18 unanswerable.
- Dense: `nomic-embed-text:v1.5` (digest `0a109f422b47`) on Ollama 0.40.18, embedded Qdrant, cosine similarity.
- Hybrid: RRF k=60 over the top 50 BM25 and dense candidates; rerank rescores the top 20 fused candidates with fastembed (ONNX, CPU).
- Machine: Windows 11, 32 logical CPUs (AMD Ryzen 9 7950X 16-Core Processor), GPU NVIDIA GeForce RTX 4070 Ti. Latency is wall time per query in one warm process.

Relevance: a chunk is relevant if it shares a line with an expected source span. `hit@5 strict` uses the stage-1 rule (the chunk contains the whole span).

| Mode | hit@5 | MRR@5 | nDCG@10 | hit@5 strict | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- | --- |
| bm25 | 0.821 | 0.601 | 0.627 | 0.821 | 2 | 3 |
| dense | 0.643 | 0.498 | 0.539 | 0.643 | 12 | 13 |
| hybrid | 0.786 | 0.535 | 0.600 | 0.786 | 13 | 15 |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | 0.821 | 0.562 | 0.602 | 0.786 | 500 | 527 |
| hybrid-rerank (bge-reranker-base) **(deployed)** | 0.857 | 0.683 | 0.695 | 0.821 | 2297 | 2379 |

Held-out run: every setting was frozen on dev (`reports/retrieval_dev.md`) and nothing below was selected on these questions. **(deployed)** marks the mode `/ask` uses.

## Hit rate by cut-off

| Mode | hit@1 | hit@3 | hit@5 | hit@8 | hit@10 |
| --- | --- | --- | --- | --- | --- |
| bm25 | 0.464 | 0.714 | 0.821 | 0.821 | 0.821 |
| dense | 0.393 | 0.571 | 0.643 | 0.750 | 0.786 |
| hybrid | 0.393 | 0.607 | 0.786 | 0.821 | 0.857 |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | 0.429 | 0.679 | 0.821 | 0.857 | 0.857 |
| hybrid-rerank (bge-reranker-base) | 0.571 | 0.786 | 0.857 | 0.857 | 0.857 |

top_k for `/ask`: **8**, frozen on dev.

## Refusal gate

Thresholds are the dev settings `/ask` applies (`min_score` for dense and hybrid, `rerank_min_score` for the deployed reranker); a mode with no frozen threshold shows none. BM25 has no calibrated score, so it cannot refuse at retrieval time.

| Mode | Gate score | Threshold | Answerable kept | Unanswerable refused |
| --- | --- | --- | --- | --- |
| bm25 | none | — | 1.000 | 0.000 |
| dense | top cosine | 0.6891 | 0.929 | 0.278 |
| hybrid | best dense cosine | 0.6891 | 0.929 | 0.333 |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | top cross-encoder score | not frozen on dev | — | — |
| hybrid-rerank (bge-reranker-base) | top cross-encoder score | -6.2459 | 1.000 | 0.056 |

## Missed at 5

| Mode | Questions |
| --- | --- |
| bm25 | `v4-c016`, `v4-c069`, `v4-c076`, `v4-c083`, `v4-c084` |
| dense | `v4-c006`, `v4-c016`, `v4-c022`, `v4-c037`, `v4-c043`, `v4-c045`, `v4-c055`, `v4-c056`, `v4-c069`, `v4-c084` |
| hybrid | `v4-c016`, `v4-c022`, `v4-c069`, `v4-c076`, `v4-c083`, `v4-c084` |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | `v4-c022`, `v4-c043`, `v4-c069`, `v4-c083`, `v4-c084` |
| hybrid-rerank (bge-reranker-base) | `v4-c022`, `v4-c069`, `v4-c083`, `v4-c084` |
