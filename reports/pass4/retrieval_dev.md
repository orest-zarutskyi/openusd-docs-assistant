# Retrieval: eval/questions.jsonl

- Date: 2026-11-26; code commit `404e2ef`.
- Corpus: OpenUSD v26.08 `ee47c679abde`, 76 documents, 952 chunks.
- Questions: `eval/questions.jsonl`, 175 total: 18 comparison, 77 lookup, 39 paraphrase, 41 unanswerable.
- Dense: `nomic-embed-text:v1.5` (digest `0a109f422b47`) on Ollama 0.40.18, embedded Qdrant, cosine similarity.
- Hybrid: RRF k=60 over the top 50 BM25 and dense candidates; rerank rescores the top 20 fused candidates with fastembed (ONNX, CPU).
- Machine: Windows 11, 32 logical CPUs (AMD Ryzen 9 7950X 16-Core Processor), GPU NVIDIA GeForce RTX 4070 Ti. Latency is wall time per query in one warm process.

Relevance: a chunk is relevant if it shares a line with an expected source span. `hit@5 strict` uses the stage-1 rule (the chunk contains the whole span).

| Mode | hit@5 | MRR@5 | nDCG@10 | hit@5 strict | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- | --- |
| bm25 | 0.746 | 0.607 | 0.616 | 0.739 | 1 | 2 |
| dense | 0.731 | 0.566 | 0.585 | 0.724 | 11 | 13 |
| hybrid | 0.821 | 0.633 | 0.651 | 0.813 | 14 | 16 |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | 0.784 | 0.675 | 0.680 | 0.776 | 547 | 560 |
| hybrid-rerank (bge-reranker-base) **(winner)** | 0.799 | 0.673 | 0.691 | 0.791 | 2621 | 2669 |

Winner rule, fixed before the run: highest nDCG@10; modes within 0.01 of it are decided by the lower p95 latency.

## Hit rate by cut-off

| Mode | hit@1 | hit@3 | hit@5 | hit@8 | hit@10 |
| --- | --- | --- | --- | --- | --- |
| bm25 | 0.522 | 0.679 | 0.746 | 0.799 | 0.836 |
| dense | 0.470 | 0.642 | 0.731 | 0.799 | 0.806 |
| hybrid | 0.522 | 0.724 | 0.821 | 0.858 | 0.881 |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | 0.597 | 0.746 | 0.784 | 0.843 | 0.866 |
| hybrid-rerank (bge-reranker-base) | 0.590 | 0.754 | 0.799 | 0.858 | 0.881 |

top_k for `/ask`: **8**, the smallest of 3, 5, 8 whose hit rate for the winner is within one question of its hit@10.

## Refusal gate

The threshold maximizes balanced accuracy over dev questions: answerable questions must pass, unanswerable ones must be refused. BM25 has no calibrated score, so it cannot refuse at retrieval time.

| Mode | Gate score | Threshold | Answerable kept | Unanswerable refused |
| --- | --- | --- | --- | --- |
| bm25 | none | — | 1.000 | 0.000 |
| dense | top cosine | 0.7406 | 0.604 | 0.756 |
| hybrid | best dense cosine | 0.7385 | 0.619 | 0.756 |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | top cross-encoder score | 1.4787 | 0.642 | 0.902 |
| hybrid-rerank (bge-reranker-base) | top cross-encoder score | 0.6184 | 0.687 | 0.951 |

## Missed at 5

| Mode | Questions |
| --- | --- |
| bm25 | `stage`, `pre-post-visit`, `working-set`, `broadcast-edit`, `switchable-asset-root`, `usda-vs-usdc`, `v2-01`, `v2-03`, `v2-07`, `v2-11`, `v2-17`, `v2-18`, `v2-20`, `v2-22`, `v2-24`, `v2-30`, `v2-36`, `v2-38`, `v2-39`, `v2-45`, `v2-52`, `v2-53`, `v3-c007`, `v3-c011`, `v3-c036`, `v3-c047`, `v3-c054`, `v3-c060`, `v3-c062`, `v3-c079`, `v3-c080`, `v3-c098`, `v3-c107`, `v3-c110` |
| dense | `layer-offset-compose`, `working-set`, `broadcast-edit`, `helper-geometry-in-renders`, `switchable-asset-root`, `v2-03`, `v2-04`, `v2-05`, `v2-07`, `v2-11`, `v2-15`, `v2-17`, `v2-18`, `v2-20`, `v2-22`, `v2-24`, `v2-26`, `v2-30`, `v2-38`, `v2-42`, `v2-45`, `v2-47`, `v2-49`, `v2-57`, `v3-c003`, `v3-c011`, `v3-c027`, `v3-c034`, `v3-c036`, `v3-c047`, `v3-c053`, `v3-c062`, `v3-c085`, `v3-c096`, `v3-c107`, `v3-c110` |
| hybrid | `broadcast-edit`, `helper-geometry-in-renders`, `switchable-asset-root`, `v2-03`, `v2-04`, `v2-05`, `v2-07`, `v2-11`, `v2-16`, `v2-17`, `v2-18`, `v2-20`, `v2-30`, `v2-38`, `v2-45`, `v2-57`, `v3-c011`, `v3-c034`, `v3-c036`, `v3-c047`, `v3-c062`, `v3-c085`, `v3-c107`, `v3-c110` |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | `working-set`, `broadcast-edit`, `switchable-asset-root`, `v2-03`, `v2-05`, `v2-07`, `v2-11`, `v2-16`, `v2-17`, `v2-18`, `v2-20`, `v2-22`, `v2-24`, `v2-30`, `v2-38`, `v2-45`, `v2-49`, `v2-51`, `v2-52`, `v2-56`, `v3-c007`, `v3-c034`, `v3-c036`, `v3-c047`, `v3-c054`, `v3-c062`, `v3-c079`, `v3-c080`, `v3-c107` |
| hybrid-rerank (bge-reranker-base) | `pre-post-visit`, `working-set`, `broadcast-edit`, `switchable-asset-root`, `v2-03`, `v2-05`, `v2-07`, `v2-11`, `v2-17`, `v2-18`, `v2-20`, `v2-22`, `v2-30`, `v2-38`, `v2-49`, `v2-58`, `v3-c005`, `v3-c011`, `v3-c034`, `v3-c036`, `v3-c047`, `v3-c062`, `v3-c079`, `v3-c085`, `v3-c098`, `v3-c107`, `v3-c110` |
