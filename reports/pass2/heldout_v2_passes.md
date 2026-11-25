# First pass vs second pass on held-out v2

- Questions: `eval/heldout_v2.jsonl`; answers: `reports/answers/pass2_heldout_v2`, one run with the frozen second-pass settings (tag `pass-2-frozen`).
- First pass: gate -0.9831, `strict` citations. Second pass: gate -6.2459, `fragments` citations. Everything else is the same, so both rows come from the same model outputs (ADR 19).

| Settings | Model | Answered with valid citations | Refused at retrieval | Refused by model | Unanswerable refused | Facts covered | Fully grounded | p50 s | $ / 100 q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| first pass | `gemini:gemini-3.5-flash-lite` | 26 / 48 | 20 | 1 | 12 / 12 | 87% | 100% | 4.0 | $0.1504 |
| first pass | `ollama:qwen3.5:4b@nothink` | 12 / 48 | 20 | 14 | 12 / 12 | 82% | 100% | 1.2 | $0.0000 |
| first pass | `ollama:qwen3:4b@think` | 19 / 48 | 20 | 2 | 12 / 12 | 91% | 100% | 17.1 | $0.0000 |
| second pass | `gemini:gemini-3.5-flash-lite` | 37 / 48 | 4 | 5 | 12 / 12 | 86% | 100% | 4.0 | $0.1504 |
| second pass | `ollama:qwen3.5:4b@nothink` | 17 / 48 | 4 | 27 | 12 / 12 | 81% | 100% | 1.2 | $0.0000 |
| second pass | `ollama:qwen3:4b@think` | 31 / 48 | 4 | 6 | 11 / 12 | 78% | 90% | 17.1 | $0.0000 |

Facts covered and fully grounded come from the judge and cover the answers each setting accepts. Latency is that of the saved run for both rows: a replayed retrieval refusal keeps the generation time it had, so first-pass latency here is an upper bound.
