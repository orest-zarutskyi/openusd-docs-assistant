# 26. Freeze the fourth-pass settings and run held-out v4 once

Status: proposed, 2026-11-26. This protocol is committed and tagged `pass-4-frozen` before any
held-out v4 question is run through the system.

## Frozen settings

The fourth pass tested two changes on the 175 dev questions and kept neither: the reranker stays
`bge-reranker-base` ([24](0024-retrieval-mode-fourth-pass.md)) and the prompt stays `v1`
([25](0025-answer-prompt-fourth-pass.md)). The settings are therefore those frozen in
[22](0022-pass-3-freeze-and-heldout-v3.md):

| Setting | Value |
| --- | --- |
| Retrieval | hybrid RRF (top 50 BM25 + top 50 dense), `bge-reranker-base` over the top 20, `top_k` 8 |
| Refusal gate | rerank score −6.2459 |
| Citation check | `fragments` |
| Answer prompt | `v1` |
| Models | `gemini:gemini-3.5-flash-lite`, `ollama:qwen3:4b@think`, `ollama:qwen3.5:4b@nothink`, `ollama:qwen3.5:9b@think` (default local model) |
| Judge | `gemini-3.8-flash`, prompt `eval/prompts/judge.md` |

The local default's p95 latency on the 175 dev questions is 62.2 s, above the 60 s cap of
[21](0021-local-model-third-pass.md). The cap was a selection rule for that comparison, not a
setting, so it is reported here as a known limitation rather than acted on.

## Protocol

Every step runs once, with `--final`, on `eval/heldout_v4.jsonl` (46 questions, 28 answerable):

1. `eval-retrieval` with the frozen settings.
2. `eval-answers` for the four models in one session, with nothing else using the GPU.
3. `judge-answers` on those answers.
4. `compare-passes` on the step-2 answers: the first-pass gate and `strict` check replayed exactly,
   as in [22](0022-pass-3-freeze-and-heldout-v3.md).

A provider error or timeout may be retried for the affected questions only. No setting changes
after this point.

## What is reported

The same measures as for held-out v3. Held-out v4 is the final evaluation of this project; v3 and
v4 come from the same kind of source and selection method, so their numbers can be read side by
side, but they are different questions.

## Result

Filled in after the run.
