# 17. Relax the refusal wording of the answer prompt, if a fixed rule supports it

Status: accepted, 2026-11-25: keep v1 and qwen3.5:4b without thinking. The candidates and rule below were committed before the new runs (commit `b1bdf8a`).

## Context

With the second-pass gate ([15](0015-refusal-gate-second-pass.md)) and citation check
([16](0016-citation-check-second-pass.md)), the local models still refuse answerable dev
questions:

- qwen3.5:4b refuses 10, and in 9 of them the context holds a passage from the expected source;
- qwen3:4b refuses 5, and in 4 the context holds one.

qwen3:4b's refusals say "the excerpts do not provide a complete answer". The current prompt asks
for a refusal whenever the excerpts "do not support a complete answer", so a partly answerable
question is refused.

## Candidates

- **P1, current prompt** (`v1`): "If the excerpts do not support a complete answer, return status
  insufficient_context."
- **P2, relaxed** (`v2`): "If no excerpt addresses the question, return status
  insufficient_context. If the excerpts answer it only in part, answer that part and say briefly
  what they do not cover." The rest of the prompt is unchanged: untrusted data, literal quotes for
  each claim, no invented evidence.

The prompt is shared by all three models. P2 is run on the 55 dev questions for each chosen
variant with the deployed settings (gate −6.2459, `fragments` check). P1's results are the replayed
second-pass answers under the same settings.

## Selection rule

1. Per prompt and model, compute the variant score ([8](0008-pre-registered-selection-rules.md)):
   (answerable answered with valid citations + correct refusals) / 2.
2. Exclude a prompt if any model answers an unanswerable question with it, with a claimed answer
   whether or not its citations are valid.
3. Pick the higher mean score over the three models. Within half an answerable question of the
   best, keep P1.
4. Then re-apply the reasoning-variant rule of [8](0008-pre-registered-selection-rules.md) to
   qwen3.5:4b (thinking off or on) under the chosen prompt. Its first-pass choice was made under
   the strict citation check, which penalized the thinking variant's quotes most.

The judge is not used for the choice. It is reported afterwards for the chosen setup, because a
relaxed prompt may produce partial answers with lower fact coverage.

## Result

`reports/pass2/prompts_dev.md`. Answerable dev questions are out of 44.

| Prompt | Model | Answered (valid) | Refused by model | Invalid citation | Invalid output |
| --- | --- | --- | --- | --- | --- |
| v1 | Flash-Lite | 41 | 0 | 3 | 0 |
| v1 | qwen3.5:4b | 32 | 10 | 2 | 0 |
| v1 | qwen3:4b | 37 | 5 | 2 | 0 |
| v2 | Flash-Lite | 40 | 0 | 3 | 1 |
| v2 | qwen3.5:4b | 25 | 13 | 3 | 3 |
| v2 | qwen3:4b | 37 | 0 | 4 | 3 |

Neither prompt let a model answer an unanswerable question. The mean scores are 0.917 for v1 and 0.886 for v2, so the rule keeps **v1**.

Under v1, the reasoning-variant rule keeps qwen3.5:4b **without thinking**: score 0.864, against 0.818 with thinking.

## Consequences

- The relaxed wording did not convert refusals into answers. qwen3:4b stopped refusing, but its five refusals became invalid citations or invalid output (about 63 s each, consistent with running into the 6,144-token limit), with no net gain. qwen3.5:4b refused more, not less. The instruction to describe what the excerpts do not cover made answers longer and more likely to break.
- With thinking on, qwen3.5:4b answers 4 more answerable questions and stops refusing them. But two unanswerable questions end in invalid output instead of a refusal, and p50 latency rises from 2.7 s to 30.4 s.
- The local models' false refusals stay the main open gap: 10 for qwen3.5:4b and 5 for qwen3:4b on dev. A prompt wording change is not the lever. Remaining candidates are a larger token budget for thinking variants, or a different local model, each needing its own pre-registered comparison.
- `answer_prompt` stays `v1`, and `v2` is kept in the code (`chat.PROMPTS`) so the comparison can be reproduced.
