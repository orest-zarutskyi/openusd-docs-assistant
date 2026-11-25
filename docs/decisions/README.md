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
| [17](0017-answer-prompt-second-pass.md) | Relax the refusal wording of the answer prompt, if a fixed rule supports it |
| [18](0018-rerank-depth-second-pass.md) | Choose the rerank depth for the second pass by a rule fixed in advance |
| [19](0019-pass-2-freeze-and-heldout-v2.md) | Freeze the second-pass settings and run held-out v2 once |
| [20](0020-third-pass-split.md) | Fold held-out v2 into dev and hold out v3 for the third pass |
| [21](0021-local-model-third-pass.md) | Choose the local model for the third pass by a rule fixed in advance |
| [22](0022-pass-3-freeze-and-heldout-v3.md) | Freeze the third-pass settings and run held-out v3 once |
| [23](0023-fourth-pass-split.md) | Fold held-out v3 into dev for the fourth pass |
| [24](0024-retrieval-mode-fourth-pass.md) | Choose the retrieval mode for the fourth pass by a rule fixed in advance |
