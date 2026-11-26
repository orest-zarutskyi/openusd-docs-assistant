# 23. Fold held-out v3 into dev for the fourth pass

Status: accepted, 2026-11-26.

## Context

Held-out v3 was run once at the end of the third pass ([22](0022-pass-3-freeze-and-heldout-v3.md)).
Its results are known, so it can no longer serve as held-out data, as happened to v1 and v2
([14](0014-second-pass-split.md), [20](0020-third-pass-split.md)).

## Decision

- The third pass stays reproducible from the tag `pass-3-frozen` and the reports under `reports/pass3/`.
- The 60 v3 questions are appended to `eval/questions.jsonl`. Dev is now 175 questions: 77 lookup,
  39 paraphrase, 18 comparison and 41 unanswerable. `eval/heldout_v3.jsonl` stays as the record of
  the v3 split, but it is no longer held out.
- The fourth pass tunes only on the 175 dev questions, under rules committed before each comparison.
  Its held-out set (v4) is collected from public forums by the method of
  [20](0020-third-pass-split.md) and needs the author's approval before it is frozen. Until then,
  no fourth-pass setting is frozen.
- Held-out v4 is `eval/heldout_v4.jsonl`: 46 real forum questions (8 lookup, 20 paraphrase,
  18 unanswerable; no comparison questions), approved by the author on 2026-11-26. The 100
  candidates and the selection are in `eval/heldout_v4_candidates.csv`,
  `eval/heldout_v4_proposal.md` and `eval/build_heldout_v4.py`. 13 suggested answerable candidates
  were dropped because they share a primary passage with dev. `check-questions` passes.

## Consequences

- Fourth-pass comparisons that were motivated by held-out v3 results say so in their ADR, because
  those questions are now part of the dev set the comparison runs on.
- With 175 dev questions, one question moves a dev rate by about 0.6 points.
