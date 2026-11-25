# Refusal gate comparison: second pass, dev

- Questions: `eval/questions.jsonl`, 55 total, 44 answerable.
- Answers behind the current gate: `reports/answers/pass2_dev_baseline`; gate-off answers for the questions it refused: `reports/answers/pass2_dev_nogate`.
- Gate score: top `BAAI/bge-reranker-base` score over hybrid candidates; the replayed current gate reproduces the saved run's refusals exactly.

Rule (ADR 15, committed before this run): exclude variants that let any model answer an unanswerable question; highest mean score over the models, where score = (answerable answered with valid citations + correct refusals) / 2; within half an answerable question of the best, fewer model calls.

| Variant | Threshold | Mean score | Unanswerable answered | Model calls | `gemini:gemini-3.5-flash-lite` answered | `ollama:qwen3.5:4b@nothink` answered | `ollama:qwen3:4b@think` answered | Chosen |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G0 no gate | none | 0.867 | 0 | 55 | 39 | 26 | 32 |  |
| G1 current | -0.9831 | 0.852 | 0 | 42 | 37 | 26 | 30 |  |
| G2 refit | 0.4724 | 0.852 | 0 | 41 | 37 | 26 | 30 |  |
| G3 recall-first | -6.2459 | 0.867 | 0 | 54 | 39 | 26 | 32 | yes |
