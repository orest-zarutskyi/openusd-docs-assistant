# 19. Freeze the second-pass settings and run held-out v2 once

Status: accepted, 2026-11-25. This protocol was committed and tagged `pass-2-frozen` before any
held-out v2 question was run through the system.

## Frozen settings

These were chosen on the 55 dev questions by the pre-registered rules of ADRs 15–18.

| Setting | Value | Decided in |
| --- | --- | --- |
| Retrieval | hybrid RRF (top 50 BM25 + top 50 dense), `bge-reranker-base` over the top 20, `top_k` 8 | [6](0006-cross-encoder-reranker.md), [18](0018-rerank-depth-second-pass.md) |
| Refusal gate | rerank score −6.2459 | [15](0015-refusal-gate-second-pass.md) |
| Citation check | `fragments` | [16](0016-citation-check-second-pass.md) |
| Answer prompt | `v1` | [17](0017-answer-prompt-second-pass.md) |
| Models | `gemini:gemini-3.5-flash-lite` (default thinking), `ollama:qwen3:4b@think`, `ollama:qwen3.5:4b@nothink` | [8](0008-pre-registered-selection-rules.md), [17](0017-answer-prompt-second-pass.md) |
| Judge | `gemini-3.8-flash`, prompt `eval/prompts/judge.md` | [13](0013-llm-judge-and-calibration.md) |

## Protocol

Every step runs once, with `--final`:

1. `eval-retrieval` on `eval/heldout_v2.jsonl` with the frozen settings. The report marks the deployed
   mode and fits nothing ([8](0008-pre-registered-selection-rules.md)).
2. `eval-answers` for the three models with the frozen settings.
3. `judge-answers` on those answers.
4. **Same-question comparison with the first pass.** The first-pass settings differ from the
   frozen ones only in the gate (−0.9831) and the citation check (`strict`). Both are replayed on
   the step-2 answers: a question whose top rerank score is below −0.9831 counts as refused at
   retrieval, and quotes are re-checked strictly. This is exact, because the context and the
   model's output do not depend on either setting ([15](0015-refusal-gate-second-pass.md)), and
   every question refused at −6.2459 is also refused at −0.9831.

A provider error or timeout may be retried for the affected questions only. No setting changes
after this point, whatever held-out v2 shows. A further change would need a new dev cycle and a
new held-out set.

## What is reported

For both settings on held-out v2 and each model:

- answerable questions answered with valid citations;
- correct refusals on the 12 unanswerable questions;
- false refusals, split into retrieval and model;
- facts covered and fully grounded (judge);
- p50 latency;
- cost per 100 questions.

The second pass is judged by the difference between the two settings on the same 60 questions. A
comparison with held-out v1 numbers would mix different questions.

## Result

The protocol was run once on 2026-11-25. There were no provider errors in the answers. The judge's
gateway failed more than once mid-run, and judging resumed from its saved verdicts each time, as the protocol allows.
The rerank scores computed for the replay reproduced the saved run's retrieval refusals exactly, so the replay is exact.

| Model | First pass | Second pass |
| --- | --- | --- |
| Gemini 3.5 Flash-Lite | 26 / 48 | 37 / 48 |
| qwen3:4b, thinking | 19 / 48 | 31 / 48 |
| qwen3.5:4b, no thinking | 12 / 48 | 17 / 48 |

The table counts answerable held-out v2 questions answered with valid citations. With either
setting, no model answered an unanswerable question.

Full table: `reports/pass2/heldout_v2_passes.md`. Retrieval: `reports/pass2/retrieval_heldout_v2.md`.
Judge: `reports/pass2/answers_heldout_v2.md`.
