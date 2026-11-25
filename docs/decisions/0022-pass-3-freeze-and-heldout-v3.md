# 22. Freeze the third-pass settings and run held-out v3 once

Status: accepted, 2026-11-26. This protocol was committed and tagged `pass-3-frozen` before any
held-out v3 question was run through the system.

## Frozen settings

The third pass changed only the default local model ([21](0021-local-model-third-pass.md)). All
other settings are those frozen in [19](0019-pass-2-freeze-and-heldout-v2.md).

| Setting | Value | Decided in |
| --- | --- | --- |
| Retrieval | hybrid RRF (top 50 BM25 + top 50 dense), `bge-reranker-base` over the top 20, `top_k` 8 | [6](0006-cross-encoder-reranker.md), [18](0018-rerank-depth-second-pass.md) |
| Refusal gate | rerank score −6.2459 | [15](0015-refusal-gate-second-pass.md) |
| Citation check | `fragments` | [16](0016-citation-check-second-pass.md) |
| Answer prompt | `v1` | [17](0017-answer-prompt-second-pass.md) |
| Models | `gemini:gemini-3.5-flash-lite` (default thinking), `ollama:qwen3:4b@think`, `ollama:qwen3.5:4b@nothink`, `ollama:qwen3.5:9b@think` | [17](0017-answer-prompt-second-pass.md), [21](0021-local-model-third-pass.md) |
| Judge | `gemini-3.8-flash`, prompt `eval/prompts/judge.md` | [13](0013-llm-judge-and-calibration.md) |

## Protocol

Every step runs once, with `--final`, on `eval/heldout_v3.jsonl` (60 questions, 42 answerable):

1. `eval-retrieval` with the frozen settings. The report fits nothing.
2. `eval-answers` for the four models, in one session on the same machine as dev.
3. `judge-answers` on those answers.
4. `compare-passes` on the step-2 answers. It replays the first-pass gate (−0.9831) and `strict`
   citation check, as in [19](0019-pass-2-freeze-and-heldout-v2.md). The replay is exact only if
   the rerank scores computed for it reproduce the saved run's retrieval refusals; the report
   checks this.

The second and third passes differ only in the local model. Their like-for-like comparison is
therefore `qwen3.5:9b@think` against the two second-pass local models in the same step-2 run.

A provider error or timeout may be retried for the affected questions only. No setting changes
after this point, whatever held-out v3 shows.

## What is reported

For each model: answerable questions answered with valid citations; correct refusals on the 18
unanswerable questions; false refusals, split into retrieval and model; facts covered and fully
grounded (judge); p50 and p95 latency; cost per 100 questions. Held-out v3 numbers are not compared
with v2's, because the questions come from different sources ([20](0020-third-pass-split.md)).

## Result

The protocol was run once on 2026-11-25 and 2026-11-26. There were no provider errors in the
answers and no judge failures. The rerank scores computed for step 4 reproduced the saved run's
retrieval refusals, so the first-pass replay is exact.

| Model | Answered with valid citations | Refused by model | Unanswerable refused | Facts covered | Fully grounded | p50 s | p95 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Gemini 3.5 Flash-Lite | 29 / 42 | 11 | 17 / 18 | 52% | 97% | 4.7 | 11.0 |
| qwen3:4b, thinking | 28 / 42 | 10 | 13 / 18 | 38% | 72% | 27.1 | 67.3 |
| qwen3.5:9b, thinking | 20 / 42 | 17 | 17 / 18 | 53% | 90% | 21.5 | 70.6 |
| qwen3.5:4b, no thinking | 8 / 42 | 31 | 18 / 18 | 56% | 100% | 0.9 | 5.2 |

- **The dev choice of local model did not hold for coverage.** qwen3.5:9b with thinking answered
  20 questions with valid citations, against 28 for qwen3:4b with thinking. On dev it led by 6.
- **It did hold for safety and grounding.** qwen3:4b claimed answers to 2 unanswerable questions
  (`v3-c050` with a valid citation, `v3-c046` with an invalid one) and ended 3 more in invalid
  output. 72% of its judged answers are fully grounded and they cover 38% of the expected facts.
  qwen3.5:9b claimed no answer to an unanswerable question; one ended in invalid output.
- **Under ADR 21's rule, qwen3:4b would have been excluded on held-out too**, by its 2 claimed
  answers and by latency. qwen3.5:9b would also exceed the 60 s cap here (p95 70.6 s).
- **Flash-Lite answered `v3-c050`**, whether a camera's projection should be uniform, from the
  general statement that every attribute not marked uniform can be animated. The judge found its
  claims supported, but the question is labelled unanswerable and the label was not changed.
- **The refusal gate refused none of the 60 questions.** The 18 unanswerable questions are real
  user questions close to the documentation, so every refusal came from the models.
- **Retrieval is weaker on these questions.** The deployed mode has nDCG@10 0.557 and hit@5 0.738.
  `ms-marco-MiniLM-L-6-v2` scored 0.601 and plain hybrid 0.559
  ([retrieval_heldout_v3.md](../../reports/pass3/retrieval_heldout_v3.md)).
- **Against the first-pass settings** on the same outputs, the frozen settings add 5, 10, 7 and 1
  valid answers for the four models, at the cost of 1, 2, 1 and 0 unanswerable questions not refused.

Full tables: `reports/pass3/answers_heldout_v3.md` (judge) and `reports/pass3/heldout_v3_passes.md`
(first-pass replay). The judge's calls cost $0.65 at official prices.
