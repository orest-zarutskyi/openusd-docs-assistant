# Answers: eval/heldout_v3.jsonl

- Answers: `reports/answers/pass3_heldout_v3`; billing tier for Gemini calls: free.
- Judge: `gemini-3.8-flash` via apils.in (OpenAI-compatible gateway), prompt `eval/prompts/judge.md` (sha256 `25f3f0c1e1a7`); judge cost of the calls made in this run at official prices $0.6450 (a gateway may bill differently).
- Prices: `eval/pricing.json`; Ollama models are $0.

| Model | Citations valid | Correct refusals | False refusals | Facts covered | Claims supported | Fully grounded | Invalid output | p50 s | p95 s | $ / 100 q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gemini:gemini-3.5-flash-lite` | 94% | 94% | 26% | 52% | 99% | 97% | 0% | 4.7 | 11.0 | $0.1702 |
| `ollama:qwen3.5:4b@nothink` | 73% | 100% | 74% | 56% | 100% | 100% | 0% | 0.9 | 5.2 | $0.0000 |
| `ollama:qwen3.5:9b@think` | 83% | 94% | 40% | 53% | 98% | 90% | 3% | 21.5 | 70.6 | $0.0000 |
| `ollama:qwen3:4b@think` | 91% | 72% | 24% | 38% | 89% | 72% | 8% | 27.1 | 67.3 | $0.0000 |

Citations valid: of answers the model claimed, every quote appears in a retrieved chunk. Refusals count both the retrieval gate and the model. Facts covered and groundedness come from the judge and cover answered questions only. Latency is end to end (retrieval and generation).

| Model | Questions | Errors | Judge failures | Input tokens | Output tokens | Thinking tokens |
| --- | --- | --- | --- | --- | --- | --- |
| `gemini:gemini-3.5-flash-lite` | 60 | 0 | 0 | 255499 | 10192 | 0 |
| `ollama:qwen3.5:4b@nothink` | 60 | 0 | 0 | 244708 | 6169 | 0 |
| `ollama:qwen3.5:9b@think` | 60 | 0 | 0 | 244588 | 109848 | 0 |
| `ollama:qwen3:4b@think` | 60 | 0 | 0 | 244540 | 183334 | 0 |
