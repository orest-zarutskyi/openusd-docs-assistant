# Answers: eval/heldout_v2.jsonl

- Answers: `reports/answers/pass2_heldout_v2`; billing tier for Gemini calls: free.
- Judge: `gemini-3.8-flash` via apils.in (OpenAI-compatible gateway), prompt `eval/prompts/judge.md` (sha256 `25f3f0c1e1a7`); judge cost of the calls made in this run at official prices $0.0383 (a gateway may bill differently).
- Prices: `eval/pricing.json`; Ollama models are $0.

| Model | Citations valid | Correct refusals | False refusals | Facts covered | Claims supported | Fully grounded | Invalid output | p50 s | p95 s | $ / 100 q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `gemini:gemini-3.5-flash-lite` | 95% | 100% | 19% | 86% | 100% | 100% | 0% | 4.0 | 16.6 | $0.1504 |
| `ollama:qwen3.5:4b@nothink` | 100% | 100% | 65% | 81% | 100% | 100% | 0% | 1.2 | 4.3 | $0.0000 |
| `ollama:qwen3:4b@think` | 97% | 92% | 21% | 78% | 95% | 90% | 13% | 17.1 | 62.9 | $0.0000 |

Citations valid: of answers the model claimed, every quote appears in a retrieved chunk. Refusals count both the retrieval gate and the model. Facts covered and groundedness come from the judge and cover answered questions only. Latency is end to end (retrieval and generation).

| Model | Questions | Errors | Judge failures | Input tokens | Output tokens | Thinking tokens |
| --- | --- | --- | --- | --- | --- | --- |
| `gemini:gemini-3.5-flash-lite` | 60 | 0 | 0 | 228601 | 8674 | 0 |
| `ollama:qwen3.5:4b@nothink` | 60 | 0 | 0 | 219408 | 6855 | 0 |
| `ollama:qwen3:4b@think` | 60 | 0 | 0 | 219254 | 144416 | 0 |
