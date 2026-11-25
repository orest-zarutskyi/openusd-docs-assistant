# 14. Fold the spent held-out set into dev and add held-out v2 for the second pass

Status: accepted, 2026-11-25.

## Context

The first pass ran held-out v1 (24 questions) once, with settings frozen on dev
([3](0003-question-sets-and-split.md), [8](0008-pre-registered-selection-rules.md)). Those
results are now known. If the second pass tuned anything while still reporting v1 as
held-out, the "held-out" numbers would be fitted to it. The first-pass sets were also small:
one question moved a held-out rate by 4–11 points.

## Decision

- The first pass is frozen at the git tag `pass-1`. Its reports and settings stay
  reproducible from there.
- The 24 v1 held-out questions are appended to `eval/questions.jsonl`, making dev 55 questions
  (30 lookup, 8 paraphrase, 6 comparison, 11 unanswerable). `eval/heldout.jsonl` stays unchanged
  as the record of the v1 split that the first-pass reports refer to. It is no longer a
  held-out set.
- Held-out v2 is `eval/heldout_v2.jsonl`: 60 new questions (28 lookup, 12 paraphrase,
  8 comparison, 12 unanswerable) written by the project author. An LLM reviewer checked them
  against the corpus, and the 13 confirmed fixes are in `eval/build_heldout_v2.py`. No primary
  source overlaps dev.
- `check-questions` now validates dev against held-out v2. Any command on held-out v2 needs
  `--final`, as before.
- The second pass tunes only on the 55 dev questions. It runs held-out v2 once, after its
  settings are frozen, under the same pre-registered rules.

## Consequences

- Second-pass results will not be comparable one-to-one with first-pass dev numbers, because
  the dev set grew. The comparison that matters is first-pass held-out v1 against second-pass
  held-out v2, both run once with frozen settings.
- With 60 held-out questions, one question moves a rate by about 2 points.
- Unlike v1, the v2 questions were not written by an LLM, which weakens the
  "LLM evaluates LLM" limitation. The source review is still an LLM's.
