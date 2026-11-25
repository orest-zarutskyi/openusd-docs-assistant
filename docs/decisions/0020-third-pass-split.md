# 20. Fold held-out v2 into dev and hold out v3 for the third pass

Status: accepted, 2026-11-25.

## Context

Held-out v2 was run once at the end of the second pass ([19](0019-pass-2-freeze-and-heldout-v2.md)).
Its results are known, so tuning on it while reporting it as held-out would fit the report to it.
The same happened to held-out v1 at the end of the first pass ([14](0014-second-pass-split.md)).

## Decision

- The second pass stays reproducible from the tag `pass-2-frozen` and the reports under `reports/pass2/`.
- The 60 v2 questions are appended to `eval/questions.jsonl`. Dev is now 115 questions: 58 lookup,
  20 paraphrase, 14 comparison and 23 unanswerable. `eval/heldout_v2.jsonl` stays as the record of the
  v2 split, but it is no longer held out.
- Held-out v3 is `eval/heldout_v3.jsonl`: 60 real questions from public forums (19 lookup,
  19 paraphrase, 4 comparison, 18 unanswerable). They were collected without looking at the
  documentation and checked against the corpus by reading it, not through this project's
  retrieval. An LLM drafted their English wording, expected facts and source spans. The author
  approved the selection. The provenance of every candidate is in `eval/heldout_v3_candidates.csv`
  and `eval/build_heldout_v3.py`.
- `check-questions` validates dev against held-out v3, and no primary source passage is shared.
- The third pass tunes only on the 115 dev questions. It runs held-out v3 once after its settings
  are frozen, under rules committed before each comparison, as in the second pass.

## Consequences

- With 115 dev questions, one question moves a dev rate by under 1 point.
- Held-out v3 mixes question sources unlike v1 and v2. Its questions come from real users and were
  not written from the documentation, so on many of them the documentation is less direct. Third-pass
  held-out numbers are therefore not comparable with v2's. The like-for-like comparison is again the
  replay of the previous settings on the same v3 outputs, where that replay is exact.
