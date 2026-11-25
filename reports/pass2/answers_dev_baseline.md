# Answers: eval/questions.jsonl

- Answers: `reports/answers/pass2_dev_baseline`; billing tier for Gemini calls: free.
- Judge: `gemini-3.8-flash` via apils.in (OpenAI-compatible gateway), prompt `eval/prompts/judge.md` (sha256 `25f3f0c1e1a7`); judge cost of the calls made in this run at official prices $0.0739 (a gateway may bill differently).
- Prices: `eval/pricing.json`; Ollama models are $0.

| Model | Citations valid | Correct refusals | False refusals | Facts covered | Claims supported | Fully grounded | Invalid output | p50 s | p95 s | $ / 100 q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gemini:gemini-3.5-flash-lite` | 90% | 100% | 7% | 82% | 100% | 100% | 0% | 5.7 | 17.1 | $0.1375 |
| `ollama:qwen3.5:4b@nothink` | 79% | 100% | 25% | 74% | 99% | 96% | 0% | 2.3 | 8.9 | $0.0000 |
| `ollama:qwen3:4b@think` | 83% | 100% | 18% | 80% | 98% | 93% | 0% | 13.1 | 38.8 | $0.0000 |

Citations valid: of answers the model claimed, every quote appears in a retrieved chunk. Refusals count both the retrieval gate and the model. Facts covered and groundedness come from the judge and cover answered questions only. Latency is end to end (retrieval and generation).

| Model | Questions | Errors | Judge failures | Input tokens | Output tokens | Thinking tokens |
| --- | --- | --- | --- | --- | --- | --- |
| `gemini:gemini-3.5-flash-lite` | 55 | 0 | 0 | 171886 | 9629 | 0 |
| `ollama:qwen3.5:4b@nothink` | 55 | 0 | 0 | 164090 | 11924 | 0 |
| `ollama:qwen3:4b@think` | 55 | 0 | 0 | 163971 | 82125 | 0 |
