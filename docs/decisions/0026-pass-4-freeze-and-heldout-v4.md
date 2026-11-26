# 26. Freeze the fourth-pass settings and run held-out v4 once

Status: accepted, 2026-11-26. This protocol was committed and tagged `pass-4-frozen` before any
held-out v4 question was run through the system.

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

The protocol was run once on 2026-11-26. There were no provider errors and no judge failures. The
rerank scores computed for step 4 reproduced the saved retrieval refusals, so the first-pass
replay is exact. Retrieval: nDCG@10 0.695, hit@5 0.857
([retrieval_heldout_v4.md](../../reports/pass4/retrieval_heldout_v4.md)).

| Model | Answered with valid citations | Refused by model | Unanswerable refused | Claimed on unanswerable | Facts covered | Fully grounded | p50 s | p95 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemini 3.5 Flash-Lite | 23 / 28 | 3 | 18 / 18 | 0 | 64% | 96% | 5.1 | 7.0 |
| qwen3:4b, thinking | 23 / 28 | 2 | 14 / 18 | 2 | 62% | 92% | 17.7 | 57.5 |
| qwen3.5:9b, thinking (default local) | 17 / 28 | 2 | 17 / 18 | 1 | 42% | 72% | 17.5 | 84.5 |
| qwen3.5:4b, no thinking | 13 / 28 | 14 | 18 / 18 | 0 | 63% | 92% | 1.4 | 6.1 |

- **Flash-Lite is the best configuration on both forum sets.** It answered 23 of 28 with valid
  citations, refused all 18 unanswerable questions, and 96% of its judged answers are fully
  grounded.
- **The dev choice of local model did not hold on v4.** qwen3.5:9b with thinking answered fewer
  questions than qwen3:4b (17 against 23), its answers are less grounded (72% against 92%), and it
  claimed an answer to one unanswerable question (`v4-c067`, per-instance visibility on a point
  instancer, answered from a passage about instance roots). qwen3:4b claimed answers to two.
- **No local model is both safe and useful on these questions.** qwen3.5:4b without thinking
  claimed nothing, but answered only 13 of 28.
- **The gate refused 1 of the 18 unanswerable questions and no answerable one.**
- **Against the first-pass settings** on the same outputs, the frozen settings add 1, 4, 3 and 4
  valid answers for Flash-Lite, qwen3:4b, qwen3.5:9b and qwen3.5:4b, at the cost of 2 unanswerable
  questions not refused for qwen3:4b and none for the others.

Full tables: `reports/pass4/answers_heldout_v4.md` (judge) and `reports/pass4/heldout_v4_passes.md`
(first-pass replay). The judge's calls cost $0.39 at official prices.

## Consequences

- The recommended configuration is Gemini Flash-Lite. The local models are an offline option with
  lower coverage and, for the thinking variants, occasional answers to questions the documentation
  does not cover.
- Choosing the local model on dev was not reliable across two held-out sets: the dev winner answered
  fewer questions than the runner-up on both. A better local choice would need more dev questions of the forum kind,
  or a rule that weighs grounding.
