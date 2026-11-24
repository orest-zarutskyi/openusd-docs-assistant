# Answers: eval/heldout.jsonl

- Answers: `reports/answers/heldout`; billing tier for Gemini calls: free.
- Judge: `gemini-3.8-flash` via apils.in (OpenAI-compatible gateway), prompt `eval/prompts/judge.md` (sha256 `25f3f0c1e1a7`); judge cost of the calls made in this run at official prices $0.1625 (a gateway may bill differently).
- Prices: `eval/pricing.json`; Ollama models are $0.

| Model | Citations valid | Correct refusals | False refusals | Facts covered | Claims supported | Fully grounded | Invalid output | p50 s | p95 s | $ / 100 q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gemini:gemini-3.5-flash-lite` | 94% | 100% | 11% | 80% | 100% | 100% | 0% | 3.3 | 4.4 | $0.1191 |
| `ollama:qwen3.5:4b@nothink` | 75% | 100% | 33% | 75% | 100% | 100% | 0% | 2.2 | 7.9 | $0.0000 |
| `ollama:qwen3:4b@think` | 79% | 100% | 22% | 59% | 100% | 100% | 0% | 10.7 | 23.7 | $0.0000 |

Citations valid: of answers the model claimed, every quote appears in a retrieved chunk. Refusals count both the retrieval gate and the model. Facts covered and groundedness come from the judge and cover answered questions only. Latency is end to end (retrieval and generation).

| Model | Questions | Errors | Judge failures | Input tokens | Output tokens | Thinking tokens |
| --- | --- | --- | --- | --- | --- | --- |
| `gemini:gemini-3.5-flash-lite` | 24 | 0 | 0 | 65699 | 3550 | 0 |
| `ollama:qwen3.5:4b@nothink` | 24 | 0 | 0 | 62671 | 4438 | 0 |
| `ollama:qwen3:4b@think` | 24 | 0 | 0 | 62621 | 29666 | 0 |
