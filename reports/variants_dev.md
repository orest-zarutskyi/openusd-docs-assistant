# Reasoning variants: eval/questions.jsonl

Rule, fixed before the runs: per model, the highest score = (answerable questions answered with valid citations + correct refusals) / 2; variants within one answerable question of the best are decided by lower p50 latency. No judge output is used.

| Variant | Answered (valid citations) | Correct refusals | False refusals | Invalid output | Citations valid | Score | p50 s | p95 s | Chosen |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ollama:qwen3.5:4b@nothink` | 0% | 100% | 27% | 0% | 0% | 0.500 | 1.6 | 7.3 |  |
| `ollama:qwen3.5:4b@think` | 19% | 100% | 4% | 0% | 20% | 0.596 | 18.5 | 33.3 | yes |
| `ollama:qwen3:4b@nothink` | 0% | 100% | 100% | 0% | — | 0.500 | 1.5 | 7.1 |  |
| `ollama:qwen3:4b@think` | 42% | 100% | 8% | 0% | 46% | 0.712 | 10.1 | 21.4 | yes |

## Why citations fail

An answer counts only if every quote is verbatim in its chunk, as the API requires. Quote validity counts quotes one by one.

| Variant | Claimed answers | Quotes verbatim | Answers without quotes | Unanswerable reaching the model | Refused by the model |
| --- | --- | --- | --- | --- | --- |
| `ollama:qwen3.5:4b@nothink` | 19 | 85% | 0 | 0 | 0 |
| `ollama:qwen3.5:4b@think` | 25 | 80% | 1 | 0 | 0 |
| `ollama:qwen3:4b@nothink` | 0 | — | 0 | 0 | 0 |
| `ollama:qwen3:4b@think` | 24 | 75% | 7 | 0 | 0 |
