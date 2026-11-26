# Run comparison

- Questions: `eval/questions.jsonl`, 175 total; gate -6.2459; citation check `fragments`.
- v1: `reports/answers/pass3_dev_models`, `reports/answers/pass3_heldout_v3`.
- v2: `reports/answers/pass4_dev_prompt_v2`.

| Variant | Answered (valid) | Refused by model | Invalid citation | Invalid output | Unanswerable refused | Claimed on unanswerable | Score | p50 s | p95 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v1 `ollama:qwen3.5:9b@think` | 94 / 134 | 23 | 12 | 2 | 40 / 41 | 0 | 0.839 | 17.8 | 62.2 |
| v2 `ollama:qwen3.5:9b@think` | 72 / 134 | 39 | 16 | 4 | 40 / 41 | 0 | 0.756 | 26.4 | 79.6 |
