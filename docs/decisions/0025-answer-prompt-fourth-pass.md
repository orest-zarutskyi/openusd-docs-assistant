# 25. Retest the relaxed answer prompt with the new local model

Status: accepted, 2026-11-26: keep `v1`. The candidates and rule below were committed before the new
run (commit `0485f8a`).

## Context

The relaxed refusal wording (`v2`) was rejected in the second pass
([17](0017-answer-prompt-second-pass.md)). With it, qwen3:4b's refusals turned into invalid output
near the thinking-token limit, and qwen3.5:4b without thinking refused more. Neither model is the
local default any more.

The default is now qwen3.5:9b with thinking ([21](0021-local-model-third-pass.md)). On held-out v3
it refused 17 of the 42 answerable questions, against 10 for qwen3:4b
([22](0022-pass-3-freeze-and-heldout-v3.md)). Real forum questions are often only partly covered
by the documentation, and `v1` asks for a refusal whenever the excerpts "do not support a complete
answer". This comparison was prompted by those held-out v3 results; those questions are now part
of dev ([23](0023-fourth-pass-split.md)).

On the 175 dev questions, qwen3.5:9b with thinking under `v1` answers 94 of 134 answerable
questions with valid citations, refuses 23 and claims no answer to an unanswerable question. Its
p95 latency is 62.2 s.

## Candidates

- `v1`, current: the saved answers of qwen3.5:9b with thinking on all 175 dev questions
  (`reports/answers/pass3_dev_models/` and `reports/answers/pass3_heldout_v3/`).
- `v2`: the same model and settings, run on the 175 dev questions with `OPENUSD_ANSWER_PROMPT=v2`.

Retrieval, gate (−6.2459), `fragments` check, `num_ctx` and output caps are unchanged.

## Selection rule

1. Score each prompt with the variant score of [8](0008-pre-registered-selection-rules.md):
   (answerable answered with valid citations + correct refusals) / 2.
2. Exclude `v2` if it claims an answer to any unanswerable question, valid citation or not.
3. `v2` replaces `v1` only if its score is higher by more than half an answerable question
   (0.5 / 268) and its p95 latency is not higher than 62.2 s.
4. The prompt is shared by all models. If `v2` passes step 3, Gemini Flash-Lite is also run on
   the 175 dev questions with `v2`. The switch then also requires that Flash-Lite claims no answer
   to an unanswerable question and scores within half an answerable question of its `v1` score.
   Otherwise `v1` stays.

The judge is not used for the choice. Any change is validated on the next held-out set.

## Result

[prompt_v2_dev.md](../../reports/pass4/prompt_v2_dev.md), qwen3.5:9b with thinking on the 175 dev
questions (134 answerable, 41 unanswerable), written by `compare-runs`:

| Prompt | Answered (valid) | Refused by model | Invalid citation | Invalid output | Unanswerable refused | Score | p50 s | p95 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **v1** | **94 / 134** | 23 | 12 | 2 | 40 / 41 | **0.839** | 17.8 | 62.2 |
| v2 | 72 / 134 | 39 | 16 | 4 | 40 / 41 | 0.756 | 26.4 | 79.6 |

Neither prompt claimed an answer to an unanswerable question. `v2` scores lower and is slower, so
step 3 fails and Flash-Lite was not run. The rule keeps **v1**.

The v2 run was started once at 01:49 and lost when the machine shut down two minutes later, before
any answer was saved. It was rerun from the start; the reported run is the only complete one.

## Consequences

- As with the 4B models in [17](0017-answer-prompt-second-pass.md), the relaxed wording makes the
  model refuse more, not less: 39 refusals against 23. It also writes more: 1,997 output tokens per
  question on average against 1,484, and answers of 647 characters against 419. p50 rises by 8.6 s.
- The prompt is not the lever for qwen3.5:9b's false refusals. `answer_prompt` stays `v1`.
