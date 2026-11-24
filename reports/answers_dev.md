# Answers: eval/questions.jsonl

- Answers: `reports/answers/dev`; billing tier for Gemini calls: free.
- Judge: `gemini-3.8-flash` via apils.in (OpenAI-compatible gateway), prompt `eval/prompts/judge.md` (sha256 `25f3f0c1e1a7`); judge cost of the calls made in this run at official prices $0.0504 (a gateway may bill differently).
- Prices: `eval/pricing.json`; Ollama models are $0.

| Model | Citations valid | Correct refusals | False refusals | Facts covered | Claims supported | Fully grounded | Invalid output | p50 s | p95 s | $ / 100 q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gemini:gemini-3.5-flash-lite` | 88% | 100% | 4% | 88% | 100% | 100% | 0% | 2.0 | 7.3 | $0.1541 |
| `ollama:qwen3.5:4b@nothink` | 90% | 100% | 23% | 75% | 98% | 94% | 0% | 2.4 | 5.9 | $0.0000 |
| `ollama:qwen3:4b@think` | 88% | 100% | 4% | 85% | 99% | 95% | 0% | 13.1 | 32.2 | $0.0000 |

Citations valid: of answers the model claimed, every quote appears in a retrieved chunk. Refusals count both the retrieval gate and the model. Facts covered and groundedness come from the judge and cover answered questions only. Latency is end to end (retrieval and generation).

| Model | Questions | Errors | Judge failures | Input tokens | Output tokens | Thinking tokens |
| --- | --- | --- | --- | --- | --- | --- |
| `gemini:gemini-3.5-flash-lite` | 31 | 0 | 0 | 106187 | 6372 | 0 |
| `ollama:qwen3.5:4b@nothink` | 31 | 0 | 0 | 101419 | 6403 | 0 |
| `ollama:qwen3:4b@think` | 31 | 0 | 0 | 101350 | 46647 | 0 |
