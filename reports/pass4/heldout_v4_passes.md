# First-pass settings vs frozen fourth-pass settings on held-out v4

- Questions: `eval/heldout_v4.jsonl`; answers: `reports/answers/pass4_heldout_v4`, one run with the frozen settings (tag `pass-4-frozen`).
- First pass: gate -0.9831, `strict` citations. Second pass: gate -6.2459, `fragments` citations. Everything else is the same, so both rows come from the same model outputs (ADR 19).

| Settings | Model | Answered with valid citations | Refused at retrieval | Refused by model | Unanswerable refused | Facts covered | Fully grounded | p50 s | $ / 100 q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| first pass | `gemini:gemini-3.5-flash-lite` | 22 / 28 | 2 | 2 | 18 / 18 | 62% | 95% | 5.1 | $0.1583 |
| first pass | `ollama:qwen3.5:4b@nothink` | 9 / 28 | 2 | 13 | 18 / 18 | 63% | 100% | 1.4 | $0.0000 |
| first pass | `ollama:qwen3.5:9b@think` | 14 / 28 | 2 | 1 | 17 / 18 | 40% | 73% | 17.5 | $0.0000 |
| first pass | `ollama:qwen3:4b@think` | 19 / 28 | 2 | 2 | 16 / 18 | 65% | 95% | 17.7 | $0.0000 |
| second pass | `gemini:gemini-3.5-flash-lite` | 23 / 28 | 0 | 3 | 18 / 18 | 64% | 96% | 5.1 | $0.1583 |
| second pass | `ollama:qwen3.5:4b@nothink` | 13 / 28 | 0 | 14 | 18 / 18 | 63% | 92% | 1.4 | $0.0000 |
| second pass | `ollama:qwen3.5:9b@think` | 17 / 28 | 0 | 2 | 17 / 18 | 42% | 72% | 17.5 | $0.0000 |
| second pass | `ollama:qwen3:4b@think` | 23 / 28 | 0 | 2 | 14 / 18 | 62% | 92% | 17.7 | $0.0000 |

Facts covered and fully grounded come from the judge and cover the answers each setting accepts. Latency is that of the saved run for both rows: a replayed retrieval refusal keeps the generation time it had, so first-pass latency here is an upper bound.
