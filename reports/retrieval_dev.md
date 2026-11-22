# Retrieval: eval/questions.jsonl

- Date: 2026-11-23; code commit `99c963f`.
- Corpus: OpenUSD v26.08 `ee47c679abde`, 76 documents, 952 chunks.
- Questions: `eval/questions.jsonl`, 31 total: 3 comparison, 19 lookup, 4 paraphrase, 5 unanswerable.
- Dense: `nomic-embed-text:v1.5` (digest `0a109f422b47`) on Ollama 0.40.16, embedded Qdrant, cosine similarity.
- Hybrid: RRF k=60 over the top 50 BM25 and dense candidates; rerank rescores the top 20 fused candidates with fastembed (ONNX, CPU).
- Machine: Windows 11, 32 logical CPUs (AMD Ryzen 9 7950X 16-Core Processor), GPU NVIDIA GeForce RTX 4070 Ti. Latency is wall time per query in one warm process.

Relevance: a chunk is relevant if it shares a line with an expected source span. `hit@5 strict` uses the stage-1 rule (the chunk contains the whole span).

| Mode | hit@5 | MRR@5 | nDCG@10 | hit@5 strict | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- | --- |
| bm25 | 0.885 | 0.817 | 0.754 | 0.846 | 1 | 2 |
| dense | 0.923 | 0.835 | 0.795 | 0.885 | 14 | 16 |
| hybrid | 1.000 | 0.885 | 0.829 | 0.962 | 16 | 19 |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | 0.962 | 0.886 | 0.833 | 0.923 | 570 | 609 |
| hybrid-rerank (bge-reranker-base) **(winner)** | 0.923 | 0.865 | 0.843 | 0.885 | 2589 | 2657 |

Winner rule, fixed before the run: highest nDCG@10; modes within 0.01 of it are decided by the lower p95 latency.

## Hit rate by cut-off

| Mode | hit@1 | hit@3 | hit@5 | hit@8 | hit@10 |
| --- | --- | --- | --- | --- | --- |
| bm25 | 0.769 | 0.846 | 0.885 | 0.885 | 0.923 |
| dense | 0.769 | 0.885 | 0.923 | 0.923 | 0.962 |
| hybrid | 0.808 | 0.923 | 1.000 | 1.000 | 1.000 |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | 0.846 | 0.923 | 0.962 | 0.962 | 0.962 |
| hybrid-rerank (bge-reranker-base) | 0.808 | 0.923 | 0.923 | 1.000 | 1.000 |

top_k for `/ask`: **8**, the smallest of 3, 5, 8 whose hit rate for the winner is within one question of its hit@10.

## Refusal gate

The threshold maximizes balanced accuracy over dev questions: answerable questions must pass, unanswerable ones must be refused. BM25 has no calibrated score, so it cannot refuse at retrieval time.

| Mode | Gate score | Threshold | Answerable kept | Unanswerable refused |
| --- | --- | --- | --- | --- |
| bm25 | none | — | 1.000 | 0.000 |
| dense | top cosine | 0.6891 | 0.962 | 0.800 |
| hybrid | best dense cosine | 0.6752 | 0.962 | 0.800 |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | top cross-encoder score | -0.9931 | 0.962 | 1.000 |
| hybrid-rerank (bge-reranker-base) | top cross-encoder score | -0.9831 | 0.962 | 1.000 |

## Missed at 5

| Mode | Questions |
| --- | --- |
| bm25 | `stage`, `pre-post-visit`, `working-set` |
| dense | `layer-offset-compose`, `working-set` |
| hybrid | none |
| hybrid-rerank (ms-marco-MiniLM-L-6-v2) | `working-set` |
| hybrid-rerank (bge-reranker-base) | `pre-post-visit`, `working-set` |
