# Local model comparison: third pass, dev

- Questions: `eval/questions.jsonl`, 115 total; gate -6.2459; citation check `fragments`; prompt `v1`.
- Current variants: replayed from `reports/answers/pass2_dev_baseline`, `reports/answers/pass2_dev_nogate` and `reports/answers/pass2_heldout_v2`. New variants: `reports/answers/pass3_dev_models`.

Rule (ADR 21, committed before the runs): exclude variants that answer an unanswerable question or whose p95 latency exceeds 60 s; highest score = (answerable answered with valid citations + correct refusals) / 2; within half an answerable question, lower p50.

| Variant | Answered (valid) | Refused by model | Invalid citation | Invalid output | Unanswerable refused | Score | p50 s | p95 s | Chosen |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ollama:qwen3.5:9b@think` | 74 / 92 | 6 | 8 | 0 | 23 / 23 | 0.902 | 15.7 | 54.7 | yes |
| `ollama:qwen3:4b@think` | 68 / 92 | 11 | 3 | 7 | 22 / 23 | 0.848 | 15.7 | 61.2 |  |
| `ollama:qwen3:8b@think` | 62 / 92 | 9 | 16 | 1 | 23 / 23 | 0.837 | 41.4 | 149.2 |  |
| `ollama:qwen3.5:4b@nothink` | 49 / 92 | 37 | 2 | 0 | 23 / 23 | 0.766 | 2.0 | 8.7 |  |
| `ollama:qwen3:8b@nothink` | 22 / 92 | 61 | 3 | 2 | 23 / 23 | 0.620 | 4.7 | 16.2 |  |
| `ollama:qwen3.5:9b@nothink` | 7 / 92 | 79 | 1 | 1 | 23 / 23 | 0.538 | 6.1 | 11.6 |  |
