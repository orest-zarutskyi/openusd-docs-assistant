# Retrieval: eval/heldout.jsonl

- Date: 2026-11-24; code commit `fc2c8f3`.
- Corpus: OpenUSD v26.08 `ee47c679abde`, 76 documents, 952 chunks.
- Questions: `eval/heldout.jsonl`, 24 total: 3 comparison, 11 lookup, 4 paraphrase, 6 unanswerable.
- Dense: `nomic-embed-text:v1.5` (digest `0a109f422b47`) on Ollama 0.40.17, embedded Qdrant, cosine similarity.
- Hybrid: RRF k=60 over the top 50 BM25 and dense candidates; rerank rescores the top 20 fused candidates with fastembed (ONNX, CPU).
- Machine: Windows 11, 32 logical CPUs (AMD Ryzen 9 7950X 16-Core Processor), GPU NVIDIA GeForce RTX 4070 Ti. Latency is wall time per query in one warm process.

Relevance: a chunk is relevant if it shares a line with an expected source span. `hit@5 strict` uses the stage-1 rule (the chunk contains the whole span).

| Mode | hit@5 | MRR@5 | nDCG@10 | hit@5 strict | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- | --- |
| bm25 | 0.833 | 0.769 | 0.756 | 0.833 | 1 | 2 |
| dense | 0.833 | 0.761 | 0.749 | 0.833 | 12 | 38 |
| hybrid | 0.833 | 0.778 | 0.781 | 0.833 | 14 | 16 |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | 0.889 | 0.833 | 0.811 | 0.889 | 521 | 555 |
| hybrid-rerank (bge-reranker-base) **(deployed)** | 0.889 | 0.861 | 0.834 | 0.889 | 2302 | 2406 |

Held-out run: every setting was frozen on dev (`reports/retrieval_dev.md`) and nothing below was selected on these questions. **(deployed)** marks the mode `/ask` uses.

## Hit rate by cut-off

| Mode | hit@1 | hit@3 | hit@5 | hit@8 | hit@10 |
| --- | --- | --- | --- | --- | --- |
| bm25 | 0.722 | 0.833 | 0.833 | 0.889 | 0.889 |
| dense | 0.722 | 0.778 | 0.833 | 0.833 | 0.833 |
| hybrid | 0.722 | 0.833 | 0.833 | 0.833 | 0.889 |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | 0.778 | 0.889 | 0.889 | 0.889 | 0.889 |
| hybrid-rerank (bge-reranker-base) | 0.833 | 0.889 | 0.889 | 0.889 | 0.889 |

top_k for `/ask`: **8**, frozen on dev.

## Refusal gate

Thresholds are the dev settings `/ask` applies (`min_score` for dense and hybrid, `rerank_min_score` for the deployed reranker); a mode with no frozen threshold shows none. BM25 has no calibrated score, so it cannot refuse at retrieval time.

| Mode | Gate score | Threshold | Answerable kept | Unanswerable refused |
| --- | --- | --- | --- | --- |
| bm25 | none | — | 1.000 | 0.000 |
| dense | top cosine | 0.6891 | 0.889 | 0.333 |
| hybrid | best dense cosine | 0.6891 | 0.889 | 0.333 |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | top cross-encoder score | not frozen on dev | — | — |
| hybrid-rerank (bge-reranker-base) | top cross-encoder score | -0.9831 | 0.889 | 0.833 |

## Missed at 5

| Mode | Questions |
| --- | --- |
| bm25 | `broadcast-edit`, `switchable-asset-root`, `usda-vs-usdc` |
| dense | `broadcast-edit`, `helper-geometry-in-renders`, `switchable-asset-root` |
| hybrid | `broadcast-edit`, `helper-geometry-in-renders`, `switchable-asset-root` |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | `broadcast-edit`, `switchable-asset-root` |
| hybrid-rerank (bge-reranker-base) | `broadcast-edit`, `switchable-asset-root` |
