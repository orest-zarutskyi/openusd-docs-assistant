# Answer prompt comparison: second pass, dev

- Questions: `eval/questions.jsonl`; gate -6.2459; citation check `fragments`.
- v1: saved second-pass answers replayed from `reports/answers/pass2_dev_baseline` and `reports/answers/pass2_dev_nogate`. v2: a new run in `reports/answers/pass2_dev_prompt_v2`.

Rule (ADR 17, committed before the runs): exclude prompts with which any model answers an unanswerable question; higher mean score over the models; within half an answerable question of the best, keep v1.

| Prompt | Model | Answered (valid) | Refused by model | Invalid citation | Unanswerable answered | Score |
| --- | --- | --- | --- | --- | --- | --- |
| v1 | `gemini:gemini-3.5-flash-lite` | 41 | 0 | 3 | 0 | 0.966 |
| v1 | `ollama:qwen3.5:4b@nothink` | 32 | 10 | 2 | 0 | 0.864 |
| v1 | `ollama:qwen3:4b@think` | 37 | 5 | 2 | 0 | 0.920 |
| v2 | `gemini:gemini-3.5-flash-lite` | 40 | 0 | 3 | 0 | 0.955 |
| v2 | `ollama:qwen3.5:4b@nothink` | 25 | 13 | 3 | 0 | 0.784 |
| v2 | `ollama:qwen3:4b@think` | 37 | 0 | 4 | 0 | 0.920 |

| Prompt | Mean score | Unanswerable answered | Chosen |
| --- | --- | --- | --- |
| v1 | 0.917 | 0 | yes |
| v2 | 0.886 | 0 |  |

## qwen3.5:4b reasoning variant under the chosen prompt (v1)

Rule of ADR 8: highest score; within one answerable question, lower p50 latency. thinking off is replayed from the second-pass answers. thinking on is a new run in `reports/answers/pass2_dev_qwen35_think/`.

| Variant | Answered (valid) | Refused by model | Invalid citation | Unanswerable answered | Score | p50 s | Chosen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ollama:qwen3.5:4b@nothink` | 32 | 10 | 2 | 0 | 0.864 | 2.7 | yes |
| `ollama:qwen3.5:4b@think` | 36 | 0 | 8 | 0 | 0.818 | 30.4 |  |

With thinking on, two unanswerable questions (`docker-usdview`, `nucleus-live-sync`) ended in invalid output after about 65 s instead of a refusal, which lowers the correct-refusal rate.
