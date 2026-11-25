# Retrieval: eval/heldout_v3.jsonl

- Date: 2026-11-25; code commit `1f83471`.
- Corpus: OpenUSD v26.08 `ee47c679abde`, 76 documents, 952 chunks.
- Questions: `eval/heldout_v3.jsonl`, 60 total: 4 comparison, 19 lookup, 19 paraphrase, 18 unanswerable.
- Dense: `nomic-embed-text:v1.5` (digest `0a109f422b47`) on Ollama 0.40.18, embedded Qdrant, cosine similarity.
- Hybrid: RRF k=60 over the top 50 BM25 and dense candidates; rerank rescores the top 20 fused candidates with fastembed (ONNX, CPU).
- Machine: Windows 11, 32 logical CPUs (AMD Ryzen 9 7950X 16-Core Processor), GPU NVIDIA GeForce RTX 4070 Ti. Latency is wall time per query in one warm process.

Relevance: a chunk is relevant if it shares a line with an expected source span. `hit@5 strict` uses the stage-1 rule (the chunk contains the whole span).

| Mode | hit@5 | MRR@5 | nDCG@10 | hit@5 strict | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- | --- |
| bm25 | 0.714 | 0.500 | 0.502 | 0.714 | 2 | 3 |
| dense | 0.714 | 0.492 | 0.491 | 0.714 | 13 | 14 |
| hybrid | 0.810 | 0.546 | 0.559 | 0.810 | 16 | 18 |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | 0.786 | 0.623 | 0.601 | 0.786 | 562 | 574 |
| hybrid-rerank (bge-reranker-base) **(deployed)** | 0.738 | 0.540 | 0.557 | 0.738 | 2606 | 2641 |

Held-out run: every setting was frozen on dev (`reports/retrieval_dev.md`) and nothing below was selected on these questions. **(deployed)** marks the mode `/ask` uses.

## Hit rate by cut-off

| Mode | hit@1 | hit@3 | hit@5 | hit@8 | hit@10 |
| --- | --- | --- | --- | --- | --- |
| bm25 | 0.381 | 0.619 | 0.714 | 0.762 | 0.810 |
| dense | 0.381 | 0.595 | 0.714 | 0.786 | 0.786 |
| hybrid | 0.405 | 0.667 | 0.810 | 0.857 | 0.905 |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | 0.524 | 0.690 | 0.786 | 0.833 | 0.857 |
| hybrid-rerank (bge-reranker-base) | 0.429 | 0.619 | 0.738 | 0.786 | 0.833 |

top_k for `/ask`: **8**, frozen on dev.

## Refusal gate

Thresholds are the dev settings `/ask` applies (`min_score` for dense and hybrid, `rerank_min_score` for the deployed reranker); a mode with no frozen threshold shows none. BM25 has no calibrated score, so it cannot refuse at retrieval time.

| Mode | Gate score | Threshold | Answerable kept | Unanswerable refused |
| --- | --- | --- | --- | --- |
| bm25 | none | — | 1.000 | 0.000 |
| dense | top cosine | 0.6891 | 0.929 | 0.111 |
| hybrid | best dense cosine | 0.6891 | 0.929 | 0.167 |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | top cross-encoder score | not frozen on dev | — | — |
| hybrid-rerank (bge-reranker-base) | top cross-encoder score | -6.2459 | 1.000 | 0.000 |

## Missed at 5

| Mode | Questions |
| --- | --- |
| bm25 | `v3-c007`, `v3-c011`, `v3-c036`, `v3-c047`, `v3-c054`, `v3-c060`, `v3-c062`, `v3-c079`, `v3-c080`, `v3-c098`, `v3-c107`, `v3-c110` |
| dense | `v3-c003`, `v3-c011`, `v3-c027`, `v3-c034`, `v3-c036`, `v3-c047`, `v3-c053`, `v3-c062`, `v3-c085`, `v3-c096`, `v3-c107`, `v3-c110` |
| hybrid | `v3-c011`, `v3-c034`, `v3-c036`, `v3-c047`, `v3-c062`, `v3-c085`, `v3-c107`, `v3-c110` |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | `v3-c007`, `v3-c034`, `v3-c036`, `v3-c047`, `v3-c054`, `v3-c062`, `v3-c079`, `v3-c080`, `v3-c107` |
| hybrid-rerank (bge-reranker-base) | `v3-c005`, `v3-c011`, `v3-c034`, `v3-c036`, `v3-c047`, `v3-c062`, `v3-c079`, `v3-c085`, `v3-c098`, `v3-c107`, `v3-c110` |
