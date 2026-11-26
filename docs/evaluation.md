# Evaluation

How the assistant was evaluated, pass by pass. Every setting was chosen on a dev set by a rule
committed before its comparison ran, then frozen and run once on a held-out set that the system
had not seen. Each held-out set was folded into dev afterwards, and the next pass used a new one.
The rules and results are in the [decision records](decisions/README.md).

## Results by pass

### Fourth pass: held-out v4

Held-out v3 was folded into dev, giving 175 questions ([ADR 23](decisions/0023-fourth-pass-split.md)).
Two changes were tested on it by rules committed in advance, and neither was kept: the faster
MiniLM reranker lost to bge by 0.0103 nDCG@10, just past the tie margin
([ADR 24](decisions/0024-retrieval-mode-fourth-pass.md)), and the relaxed prompt made qwen3.5:9b
refuse more ([ADR 25](decisions/0025-answer-prompt-fourth-pass.md)). The settings were frozen at tag
[`pass-4-frozen`](https://github.com/orest-zarutskyi/openusd-docs-assistant/tree/pass-4-frozen) and
held-out v4 was run once ([ADR 26](decisions/0026-pass-4-freeze-and-heldout-v4.md)).

Held-out v4 has 46 real forum questions, 28 answerable and 18 unanswerable
([eval/heldout_v4.jsonl](../eval/heldout_v4.jsonl)), collected and checked like v3.

| Model | Answered with valid citations | Refused by model | Unanswerable refused | Claimed on unanswerable | Facts covered | Fully grounded | p50 s | p95 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemini 3.5 Flash-Lite | 23 / 28 | 3 | 18 / 18 | 0 | 64% | 96% | 5.1 | 7.0 |
| qwen3:4b, thinking | 23 / 28 | 2 | 14 / 18 | 2 | 62% | 92% | 17.7 | 57.5 |
| qwen3.5:9b, thinking (default local) | 17 / 28 | 2 | 17 / 18 | 1 | 42% | 72% | 17.5 | 84.5 |
| qwen3.5:4b, no thinking | 13 / 28 | 14 | 18 / 18 | 0 | 63% | 92% | 1.4 | 6.1 |

- Flash-Lite is the best configuration on both forum sets.
- The local model chosen on dev answered fewer questions than qwen3:4b on both v3 and v4, and on
  v4 it also claimed an answer to one unanswerable question.
- Retrieval: nDCG@10 0.695 and hit@5 0.857 ([retrieval_heldout_v4.md](../reports/pass4/retrieval_heldout_v4.md)).

### Third pass: held-out v3

The third pass changed only the default local model. Four larger candidates were compared with the
two current local variants on 115 dev questions, by a rule committed before the runs: no answer to
an unanswerable question, p95 latency within 60 s, then the best variant score. It chose qwen3.5:9b
with thinking ([ADR 21](decisions/0021-local-model-third-pass.md),
[models_dev.md](../reports/pass3/models_dev.md)). The settings were then frozen at tag
[`pass-3-frozen`](https://github.com/orest-zarutskyi/openusd-docs-assistant/tree/pass-3-frozen)
([ADR 22](decisions/0022-pass-3-freeze-and-heldout-v3.md)).

Held-out v3 has 60 real questions from public forums: 42 answerable, 18 unanswerable
([eval/heldout_v3.jsonl](../eval/heldout_v3.jsonl)). They were collected without looking at the
documentation and checked against it by reading. An LLM drafted their wording, expected facts and
source spans, and the author approved the selection. It was run once.

| Model | Answered with valid citations | Refused by model | Unanswerable refused | Facts covered | Fully grounded | p50 s | p95 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Gemini 3.5 Flash-Lite | 29 / 42 | 11 | 17 / 18 | 52% | 97% | 4.7 | 11.0 |
| qwen3:4b, thinking | 28 / 42 | 10 | 13 / 18 | 38% | 72% | 27.1 | 67.3 |
| qwen3.5:9b, thinking (new default) | 20 / 42 | 17 | 17 / 18 | 53% | 90% | 21.5 | 70.6 |
| qwen3.5:4b, no thinking | 8 / 42 | 31 | 18 / 18 | 56% | 100% | 0.9 | 5.2 |

- **The new local default is safer, but it answers fewer questions than qwen3:4b.** On dev it led
  qwen3:4b by 6 valid answers; on held-out v3 it trails by 8. qwen3:4b claimed answers to 2
  unanswerable questions, and only 72% of its judged answers are fully grounded.
- **Real questions are harder.** Expected facts covered fall to 38–56%, against 78–86% on held-out
  v2, and retrieval nDCG@10 is 0.557 ([retrieval_heldout_v3.md](../reports/pass3/retrieval_heldout_v3.md)).
  The questions come from a different source than v2's, so these numbers are not a like-for-like
  comparison with v2.
- **The refusal gate refused none of the 60 questions.** Every correct refusal came from the models.
- **Both local thinking models exceed 60 s at p95 here**, so local `/ask` is slow for long
  answers.

### Second pass: held-out v2

The second pass changed two settings, each chosen on 55 dev questions by a rule committed before its comparison ran. The settings were then frozen at tag [`pass-2-frozen`](https://github.com/orest-zarutskyi/openusd-docs-assistant/tree/pass-2-frozen) ([ADR 19](decisions/0019-pass-2-freeze-and-heldout-v2.md)).

- **Refusal gate.** A recall-first safety net, rerank score −6.2459 instead of −0.9831. The models refuse unanswerable questions themselves, and the gate stops only questions far from the corpus ([ADR 15](decisions/0015-refusal-gate-second-pass.md)).
- **Citation check.** It now also accepts quotes that differ from the source only in case, quote marks or punctuation, quotes that name the wrong retrieved chunk, and quotes stitched from verbatim sentences of one chunk. Every word must still be in the source ([ADR 16](decisions/0016-citation-check-second-pass.md)).

A relaxed refusal wording in the prompt, a thinking variant for qwen3.5:4b and deeper reranking were tested the same way and rejected ([ADR 17](decisions/0017-answer-prompt-second-pass.md), [ADR 18](decisions/0018-rerank-depth-second-pass.md)).

Held-out v2 has 60 new questions written by the author: 48 answerable, 12 unanswerable ([eval/heldout_v2.jsonl](../eval/heldout_v2.jsonl)). It was run once. The first-pass settings differ only in the gate and the citation check, so they are replayed exactly on the same model outputs. That gives a like-for-like comparison ([heldout_v2_passes.md](../reports/pass2/heldout_v2_passes.md)).

| Model | Settings | Answered with valid citations | Refused at retrieval | Refused by model | Unanswerable refused | Facts covered | Fully grounded | p50 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemini 3.5 Flash-Lite | first pass | 26 / 48 | 20 | 1 | 12 / 12 | 87% | 100% | 4.0 |
| Gemini 3.5 Flash-Lite | **second pass** | **37 / 48** | 4 | 5 | 12 / 12 | 86% | 100% | 4.0 |
| qwen3:4b, thinking | first pass | 19 / 48 | 20 | 2 | 12 / 12 | 91% | 100% | 17.1 |
| qwen3:4b, thinking | **second pass** | **31 / 48** | 4 | 6 | 11 / 12 | 78% | 90% | 17.1 |
| qwen3.5:4b, no thinking | first pass | 12 / 48 | 20 | 14 | 12 / 12 | 82% | 100% | 1.2 |
| qwen3.5:4b, no thinking | **second pass** | **17 / 48** | 4 | 27 | 12 / 12 | 81% | 100% | 1.2 |

Facts covered and fully grounded are scored by the judge, on the answers each setting accepts. Gemini costs $0.15 per 100 questions at list price.

- **Each model answers more questions correctly with the second-pass settings,** by 11, 12 and 5 questions out of 48. No model answered an unanswerable question. One qwen3:4b answer to an unanswerable question ended in invalid output instead of a refusal, so 11 of 12 are counted as refused.
- **Held-out v2 is harder than dev.** Retrieval nDCG@10 is 0.672, against 0.839 on dev, and hit@5 is 0.750 ([retrieval_heldout_v2.md](../reports/pass2/retrieval_heldout_v2.md)). The bge reranker is still the best of the five modes.
- **The new gate's margin was thin, as ADR 15 warned.** It refuses 4 of 48 answerable held-out questions at retrieval, against 20 for the first-pass gate.
- **The extra answers cost some quality for qwen3:4b.** Facts covered fall from 91% to 78%, and 3 of its answers have an unsupported claim. Flash-Lite's and qwen3.5:4b's answers stay fully grounded.
- **qwen3.5:4b refuses 27 answerable questions that reach it.** Its false refusals stay the largest open gap, as on dev ([ADR 17](decisions/0017-answer-prompt-second-pass.md)).

### First pass (tag `pass-1`)

All numbers in the rest of this section are from the first pass (git tag [`pass-1`](https://github.com/orest-zarutskyi/openusd-docs-assistant/tree/pass-1)) and come from the reports in [`reports/`](../reports). Every setting was chosen on the dev set (31 questions). The held-out set (24 questions) was run once at the end with those settings frozen. The selection rules were fixed before the runs ([ADR 8](decisions/0008-pre-registered-selection-rules.md)).

#### Retrieval

A chunk counts as relevant if it shares a line with an expected source span. Latency is wall time per query on a Ryzen 9 7950X CPU. The reranker runs on CPU through ONNX.

| Mode | dev hit@5 | dev MRR@5 | dev nDCG@10 | held-out hit@5 | held-out MRR@5 | held-out nDCG@10 | dev p95 ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BM25 (SQLite FTS5) | 0.885 | 0.817 | 0.754 | 0.833 | 0.769 | 0.756 | 2 |
| Dense (`nomic-embed-text:v1.5`) | 0.923 | 0.835 | 0.795 | 0.833 | 0.761 | 0.749 | 16 |
| Hybrid (RRF) | 1.000 | 0.885 | 0.829 | 0.833 | 0.778 | 0.781 | 19 |
| Hybrid + `ms-marco-MiniLM-L-6-v2` | 0.962 | 0.886 | 0.833 | 0.889 | 0.833 | 0.811 | 609 |
| **Hybrid + `bge-reranker-base`** (used by `/ask`) | 0.923 | 0.865 | 0.843 | 0.889 | 0.861 | 0.834 | 2657 |

`/ask` passes the top 8 chunks to the model. The refusal gate on the reranker score was fitted on dev. On held-out, unchanged, it kept 16 of 18 answerable questions and refused 5 of 6 unanswerable ones. Sources: [retrieval_dev.md](../reports/retrieval_dev.md), [retrieval_heldout.md](../reports/retrieval_heldout.md).

#### Answers

Each model answers from the same retrieved context. Its reasoning setting was chosen on dev ([variants_dev.md](../reports/variants_dev.md)). An answer is accepted only if every quote appears in the cited chunk ([ADR 9](decisions/0009-verbatim-quotes-with-rst-normalization.md)).

Two columns come from the LLM judge, and it scores only answered questions:
- **Facts covered** is the share of a question's expected facts the answer states.
- **Fully grounded** is the share of answers in which every claim is supported by the excerpts.

Cost per 100 questions uses official paid Gemini prices ([pricing.json](../eval/pricing.json)); local models are $0.

| Model | Set | Valid citations | Correct refusals | False refusals | Facts covered | Fully grounded | p50 s | $ / 100 q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemini 3.5 Flash-Lite | dev | 88% | 100% | 4% | 88% | 100% | 2.0 | 0.15 |
| Gemini 3.5 Flash-Lite | held-out | 94% | 100% | 11% | 80% | 100% | 3.3 | 0.12 |
| qwen3:4b, thinking (Ollama) | dev | 88% | 100% | 4% | 85% | 95% | 13.1 | 0 |
| qwen3:4b, thinking (Ollama) | held-out | 79% | 100% | 22% | 59% | 100% | 10.7 | 0 |
| qwen3.5:4b, no thinking (Ollama) | dev | 90% | 100% | 23% | 75% | 94% | 2.4 | 0 |
| qwen3.5:4b, no thinking (Ollama) | held-out | 75% | 100% | 33% | 75% | 100% | 2.2 | 0 |

No model answered an unanswerable question on either set. Sources: [answers_dev.md](../reports/answers_dev.md), [answers_heldout.md](../reports/answers_heldout.md). Every answer is shown side by side with its quotes and the judge's notes in [answers_dev.html](../reports/answers_dev.html) and [answers_heldout.html](../reports/answers_heldout.html); download and open them locally, because GitHub shows HTML as source.

**Without the retrieval gate.** The six dev questions the gate refused were answered again with the gate off ([refusals_nogate_dev.md](../reports/refusals_nogate_dev.md)). All three models refused all five unanswerable ones on their own. On the answerable `working-set` question, qwen3:4b gave a valid answer, Flash-Lite an invalid citation and qwen3.5:4b a refusal. On dev, the gate therefore saves model calls rather than preventing wrong answers, and it costs one answerable question. The gate was fitted on these same five questions, so this is a dev observation, not a held-out result.

#### Judge calibration

The judge is `gemini-3.8-flash`, which is not one of the compared models. Its prompt is in [eval/prompts/judge.md](../eval/prompts/judge.md). It was compared with reference labels on 20 dev answers ([judge_calibration_dev.md](../reports/judge_calibration_dev.md)):

| Decision | n | Agreement | Cohen's kappa |
| --- | --- | --- | --- |
| Expected fact covered | 44 | 95% | 0.85 |
| Answer fully grounded | 20 | 95% | 0.64 |

The judge was the stricter side in all three disagreements, each a borderline case.

## Development plan (as first written)

1. **Corpus and examples.** Pin the text documentation from OpenUSD 26.08, retain license notices and exact line references, and write evaluation questions with expected passages or refusals. *Done: all 76 RST files.*
2. **Working local API.** Index documents in Qdrant. Use a small LangGraph workflow for retrieval, generation and citation validation. Run inference through a configurable model and expose the workflow through FastAPI. A repeated index build should not duplicate points. *Done.*
3. **Evaluation and tests.** Compare lexical, dense, hybrid and reranked retrieval, measure whether answers are supported by sources and whether the system refuses appropriately, and keep a held-out set. *Done: results below.*
4. **Reproduction and demo.** Document setup, provide Docker Compose and CI checks, and record a short demo showing an answer, its source and a refusal. *Done: [CI](../.github/workflows/checks.yml) runs ruff lint and format checks and pytest on Ubuntu and Windows for every push, [docs/demo.md](demo.md) records real `/ask` responses, and a motion demo is rendered from them. Docker Compose was built and run on 2026-11-24: the container indexed the 952 chunks and answered the demo questions the same way as the local server (a refusal in 2.1 s; “Payload” with the same three sources in 20 s).*

The first public release covers English questions on OpenUSD documentation. A Houdini integration, one render-log diagnosis scenario and hosted deployment are later options.

## Reproducing the evaluation

With `OPENUSD_QDRANT_PATH=data/qdrant`, Ollama running and the keys in `.env`:

```powershell
uv run --locked openusd-assistant eval-retrieval --report reports/retrieval_dev.md
uv run --locked openusd-assistant eval-answers --models "gemini:gemini-3.5-flash-lite,ollama:qwen3:4b@think,ollama:qwen3.5:4b@nothink"
uv run --locked openusd-assistant compare-variants
uv run --locked openusd-assistant judge-answers --tier free --models "gemini:gemini-3.5-flash-lite,ollama:qwen3:4b@think,ollama:qwen3.5:4b@nothink"
uv run --locked openusd-assistant calibrate-judge
```

`compare-variants` reads every answer file in `reports/answers/dev`. The dev report there also covers the variants that were not chosen, such as `ollama:qwen3:4b@nothink` and `gemini:gemini-3.5-flash-lite@level=low`.

`openusd-assistant answers-page` writes the side-by-side HTML page, and `refusal-report` summarises a run made with `OPENUSD_RERANK_MIN_SCORE=-1000000` and `eval-answers --ids ... --out-dir reports/answers/dev_nogate`.

The judge needs `OPENUSD_JUDGE_MODEL`, plus either the Gemini key or `OPENUSD_JUDGE_PROVIDER=openai-compatible` with a gateway URL and key. Held-out commands take `--final`, `--questions eval/heldout_v3.jsonl` (or an earlier set) and their own `--out-dir`, `--answers-dir` or `--report`. Without `--final`, the CLI refuses held-out questions. The later passes add `compare-gates`, `compare-citations`, `compare-prompts`, `compare-models` and `compare-passes`; the comparison ADRs from [15](decisions/0015-refusal-gate-second-pass.md) on name the report behind each result, and each report's header lists its inputs.

