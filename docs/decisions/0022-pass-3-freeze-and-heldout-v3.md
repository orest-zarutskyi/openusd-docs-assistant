# 22. Freeze the third-pass settings and run held-out v3 once

Status: proposed, 2026-11-25. This protocol is committed and tagged `pass-3-frozen` before any
held-out v3 question is run through the system.

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

Filled in after the run.
