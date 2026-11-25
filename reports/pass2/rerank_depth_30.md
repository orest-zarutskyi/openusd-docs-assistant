# Retrieval: eval/questions.jsonl

- Date: 2026-11-25; code commit `61c7654` (with uncommitted changes).
- Corpus: OpenUSD v26.08 `ee47c679abde`, 76 documents, 952 chunks.
- Questions: `eval/questions.jsonl`, 55 total: 6 comparison, 30 lookup, 8 paraphrase, 11 unanswerable.
- Dense: `nomic-embed-text:v1.5` (digest `0a109f422b47`) on Ollama 0.40.18, embedded Qdrant, cosine similarity.
- Hybrid: RRF k=60 over the top 50 BM25 and dense candidates; rerank rescores the top 30 fused candidates with fastembed (ONNX, CPU).
- Machine: Windows 11, 32 logical CPUs (AMD Ryzen 9 7950X 16-Core Processor), GPU NVIDIA GeForce RTX 4070 Ti. Latency is wall time per query in one warm process.

Relevance: a chunk is relevant if it shares a line with an expected source span. `hit@5 strict` uses the stage-1 rule (the chunk contains the whole span).

| Mode | hit@5 | MRR@5 | nDCG@10 | hit@5 strict | p50 ms | p95 ms |
| --- | --- | --- | --- | --- | --- | --- |
| hybrid-rerank (bge-reranker-base) **(winner)** | 0.909 | 0.864 | 0.836 | 0.886 | 3838 | 3995 |

Winner rule, fixed before the run: highest nDCG@10; modes within 0.01 of it are decided by the lower p95 latency.

## Hit rate by cut-off

| Mode | hit@1 | hit@3 | hit@5 | hit@8 | hit@10 |
| --- | --- | --- | --- | --- | --- |
| hybrid-rerank (bge-reranker-base) | 0.818 | 0.909 | 0.909 | 0.955 | 0.955 |

top_k for `/ask`: **8**, the smallest of 3, 5, 8 whose hit rate for the winner is within one question of its hit@10.

## Refusal gate

The threshold maximizes balanced accuracy over dev questions: answerable questions must pass, unanswerable ones must be refused. BM25 has no calibrated score, so it cannot refuse at retrieval time.

| Mode | Gate score | Threshold | Answerable kept | Unanswerable refused |
| --- | --- | --- | --- | --- |
| hybrid-rerank (bge-reranker-base) | top cross-encoder score | 0.6082 | 0.932 | 1.000 |

## Missed at 5

| Mode | Questions |
| --- | --- |
| hybrid-rerank (bge-reranker-base) | `pre-post-visit`, `working-set`, `broadcast-edit`, `switchable-asset-root` |
