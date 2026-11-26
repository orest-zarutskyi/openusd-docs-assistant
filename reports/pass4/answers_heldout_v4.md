# Answers: eval/heldout_v4.jsonl

- Answers: `reports/answers/pass4_heldout_v4`; billing tier for Gemini calls: free.
- Judge: `gemini-3.8-flash` via apils.in (OpenAI-compatible gateway), prompt `eval/prompts/judge.md` (sha256 `25f3f0c1e1a7`); judge cost of the calls made in this run at official prices $0.3859 (a gateway may bill differently).
- Prices: `eval/pricing.json`; Ollama models are $0.

| Model | Citations valid | Correct refusals | False refusals | Facts covered | Claims supported | Fully grounded | Invalid output | p50 s | p95 s | $ / 100 q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gemini:gemini-3.5-flash-lite` | 92% | 100% | 11% | 64% | 98% | 96% | 0% | 5.1 | 7.0 | $0.1583 |
| `ollama:qwen3.5:4b@nothink` | 100% | 100% | 50% | 63% | 95% | 92% | 2% | 1.4 | 6.1 | $0.0000 |
| `ollama:qwen3.5:9b@think` | 75% | 94% | 7% | 42% | 86% | 72% | 7% | 17.5 | 84.5 | $0.0000 |
| `ollama:qwen3:4b@think` | 96% | 78% | 7% | 62% | 95% | 92% | 11% | 17.7 | 57.5 | $0.0000 |

Citations valid: of answers the model claimed, every quote appears in a retrieved chunk. Refusals count both the retrieval gate and the model. Facts covered and groundedness come from the judge and cover answered questions only. Latency is end to end (retrieval and generation).

| Model | Questions | Errors | Judge failures | Input tokens | Output tokens | Thinking tokens |
| --- | --- | --- | --- | --- | --- | --- |
| `gemini:gemini-3.5-flash-lite` | 46 | 0 | 0 | 190038 | 6326 | 0 |
| `ollama:qwen3.5:4b@nothink` | 46 | 0 | 0 | 182032 | 7931 | 0 |
| `ollama:qwen3.5:9b@think` | 46 | 0 | 0 | 181942 | 93633 | 0 |
| `ollama:qwen3:4b@think` | 46 | 0 | 0 | 181935 | 132630 | 0 |
