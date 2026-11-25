# Architecture decision records

Each record states the context, the decision, and its consequences, with the report that
supports it.

| # | Decision |
| --- | --- |
| [1](0001-pinned-corpus.md) | Pin the corpus to one OpenUSD commit with SHA-256 digests |
| [2](0002-line-preserving-rst-chunking.md) | Chunk RST by structure while keeping exact line ranges |
| [3](0003-question-sets-and-split.md) | Separate dev and held-out question sets with a fixed split |
| [4](0004-relevance-by-line-overlap.md) | Count a retrieved chunk as relevant when it overlaps an expected span |
| [5](0005-hybrid-retrieval-rrf.md) | Fuse BM25 and dense retrieval with reciprocal rank fusion |
| [6](0006-cross-encoder-reranker.md) | Rerank the fused candidates with bge-reranker-base |
| [7](0007-refusal-gates.md) | Refuse at retrieval time with a per-mode score threshold |
| [8](0008-pre-registered-selection-rules.md) | Fix the selection rules before running the comparisons |
| [9](0009-verbatim-quotes-with-rst-normalization.md) | Accept a citation only if its quote appears in the chunk, ignoring RST markup |
| [10](0010-required-answer-schema.md) | Require status, answer and evidence in the model's JSON output |
| [11](0011-local-model-configuration.md) | Choose reasoning per local model and raise Ollama's context window |
| [12](0012-gemini-adapter-and-cost.md) | Add a Gemini API adapter and price runs at official rates |
| [13](0013-llm-judge-and-calibration.md) | Grade answers with a separate LLM judge and calibrate it against reference labels |
| [14](0014-second-pass-split.md) | Fold the spent held-out set into dev and add held-out v2 for the second pass |
| [15](0015-refusal-gate-second-pass.md) | Choose the refusal gate for the second pass by a rule fixed in advance |
| [16](0016-citation-check-second-pass.md) | Choose how strictly citations are checked, by a rule fixed in advance |
