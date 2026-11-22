# Reasoning variants: eval/questions.jsonl

Rule, fixed before the runs: per model, the highest score = (answerable questions answered with valid citations + correct refusals) / 2; variants within one answerable question of the best are decided by lower p50 latency. No judge output is used.

| Variant | Answered (valid citations) | Correct refusals | False refusals | Invalid output | Citations valid | Score | p50 s | p95 s | Chosen |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ollama:qwen3.5:4b@nothink` | 62% | 100% | 27% | 0% | 84% | 0.808 | 1.8 | 6.2 |  |
| `ollama:qwen3.5:4b@think` | 69% | 100% | 4% | 0% | 72% | 0.846 | 19.4 | 37.9 | yes |
| `ollama:qwen3:4b@nothink` | 0% | 100% | 100% | 0% | — | 0.500 | 7.5 | 8.6 |  |
| `ollama:qwen3:4b@think` | 73% | 100% | 8% | 0% | 79% | 0.865 | 11.0 | 22.6 | yes |

## Why citations fail

An answer counts only if every quote is verbatim in its chunk, as the API requires. Quote validity counts quotes one by one.

| Variant | Claimed answers | Quotes verbatim | Answers without quotes | Unanswerable reaching the model | Refused by the model |
| --- | --- | --- | --- | --- | --- |
| `ollama:qwen3.5:4b@nothink` | 19 | 95% | 1 | 0 | 0 |
| `ollama:qwen3.5:4b@think` | 25 | 73% | 0 | 0 | 0 |
| `ollama:qwen3:4b@nothink` | 0 | — | 0 | 0 | 0 |
| `ollama:qwen3:4b@think` | 24 | 88% | 0 | 0 | 0 |
