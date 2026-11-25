# First-pass settings vs frozen third-pass settings on held-out v3

- Questions: `eval/heldout_v3.jsonl`; answers: `reports/answers/pass3_heldout_v3`, one run with the frozen settings (tag `pass-3-frozen`).
- First pass: gate -0.9831, `strict` citations. Second pass: gate -6.2459, `fragments` citations. Everything else is the same, so both rows come from the same model outputs (ADR 19).

| Settings | Model | Answered with valid citations | Refused at retrieval | Refused by model | Unanswerable refused | Facts covered | Fully grounded | p50 s | $ / 100 q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| first pass | `gemini:gemini-3.5-flash-lite` | 24 / 42 | 4 | 10 | 18 / 18 | 51% | 96% | 4.7 | $0.1702 |
| first pass | `ollama:qwen3.5:4b@nothink` | 7 / 42 | 4 | 28 | 18 / 18 | 50% | 100% | 0.9 | $0.0000 |
| first pass | `ollama:qwen3.5:9b@think` | 13 / 42 | 4 | 17 | 18 / 18 | 58% | 100% | 21.5 | $0.0000 |
| first pass | `ollama:qwen3:4b@think` | 18 / 42 | 4 | 10 | 15 / 18 | 33% | 72% | 27.1 | $0.0000 |
| second pass | `gemini:gemini-3.5-flash-lite` | 29 / 42 | 0 | 11 | 17 / 18 | 52% | 97% | 4.7 | $0.1702 |
| second pass | `ollama:qwen3.5:4b@nothink` | 8 / 42 | 0 | 31 | 18 / 18 | 56% | 100% | 0.9 | $0.0000 |
| second pass | `ollama:qwen3.5:9b@think` | 20 / 42 | 0 | 17 | 17 / 18 | 53% | 90% | 21.5 | $0.0000 |
| second pass | `ollama:qwen3:4b@think` | 28 / 42 | 0 | 10 | 13 / 18 | 38% | 72% | 27.1 | $0.0000 |

Facts covered and fully grounded come from the judge and cover the answers each setting accepts. Latency is that of the saved run for both rows: a replayed retrieval refusal keeps the generation time it had, so first-pass latency here is an upper bound.
