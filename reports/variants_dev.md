# Reasoning variants: eval/questions.jsonl

Rule, fixed before the runs: per model, the highest score = (answerable questions answered with valid citations + correct refusals) / 2; variants within one answerable question of the best are decided by lower p50 latency. No judge output is used.

| Variant | Answered (valid citations) | Correct refusals | False refusals | Invalid output | Citations valid | Score | p50 s | p95 s | Chosen |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gemini:gemini-3.5-flash-lite` | 85% | 100% | 4% | 0% | 88% | 0.923 | 2.0 | 7.3 | yes |
| `gemini:gemini-3.5-flash-lite@level=high` | 85% | 100% | 4% | 0% | 100% | 0.923 | 5.7 | 37.9 |  |
| `gemini:gemini-3.5-flash-lite@level=low` | 88% | 100% | 4% | 0% | 92% | 0.942 | 2.3 | 5.5 |  |
| `gemini:gemini-3.5-flash-lite@level=medium` | 88% | 100% | 4% | 0% | 92% | 0.942 | 3.1 | 16.4 |  |
| `gemini:gemini-3.5-flash-lite@level=minimal` | 88% | 100% | 4% | 0% | 92% | 0.942 | 3.3 | 16.7 |  |
| `ollama:qwen3.5:4b@nothink` | 69% | 100% | 23% | 0% | 90% | 0.846 | 2.4 | 5.9 | yes |
| `ollama:qwen3.5:4b@think` | 65% | 100% | 4% | 0% | 68% | 0.827 | 21.5 | 39.1 |  |
| `ollama:qwen3:4b@nothink` | 0% | 100% | 100% | 0% | — | 0.500 | 10.2 | 11.9 |  |
| `ollama:qwen3:4b@think` | 85% | 100% | 4% | 0% | 88% | 0.923 | 13.1 | 32.2 | yes |

## Why citations fail

An answer counts only if every quote is verbatim in its chunk, as the API requires. Quote validity counts quotes one by one.

| Variant | Claimed answers | Quotes verbatim | Answers without quotes | Unanswerable reaching the model | Refused by the model |
| --- | --- | --- | --- | --- | --- |
| `gemini:gemini-3.5-flash-lite` | 25 | 94% | 0 | 0 | 0 |
| `gemini:gemini-3.5-flash-lite@level=high` | 22 | 100% | 0 | 0 | 0 |
| `gemini:gemini-3.5-flash-lite@level=low` | 25 | 96% | 0 | 0 | 0 |
| `gemini:gemini-3.5-flash-lite@level=medium` | 25 | 96% | 0 | 0 | 0 |
| `gemini:gemini-3.5-flash-lite@level=minimal` | 25 | 93% | 0 | 0 | 0 |
| `ollama:qwen3.5:4b@nothink` | 20 | 90% | 0 | 0 | 0 |
| `ollama:qwen3.5:4b@think` | 25 | 74% | 0 | 0 | 0 |
| `ollama:qwen3:4b@nothink` | 0 | — | 0 | 0 | 0 |
| `ollama:qwen3:4b@think` | 25 | 86% | 0 | 0 | 0 |
