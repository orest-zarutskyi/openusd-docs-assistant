# 17. Relax the refusal wording of the answer prompt, if a fixed rule supports it

Status: proposed, 2026-11-25. The candidates and rule below were committed before the new runs.

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

## Consequences

Filled in after the comparison.
