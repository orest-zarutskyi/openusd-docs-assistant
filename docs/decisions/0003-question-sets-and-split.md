# 3. Separate dev and held-out question sets with a fixed split

Status: accepted, 2026-11-23.

## Context

Retrieval settings, refusal thresholds and model variants are all tuned on questions. If the
same questions also produce the reported numbers, the numbers overstate quality.

## Decision

- `eval/questions.jsonl` (dev, 31 questions) is used for every choice;
  `eval/heldout.jsonl` (24 questions) is run once at the end with `--final`. The CLI refuses
  held-out files without that flag.
- Questions were assigned by `sha256("2608:" + id)` within each kind, so the split does not
  depend on how hard a question looked.
- Each set has at least five unanswerable and five reworded (paraphrase or comparison)
  questions.
- The two sets may not share a primary source passage. Alternative sources (other passages
  that also answer the question) are exempt.
- Each question lists its expected source spans and the facts a complete answer states.
- Every source span was checked against the snapshot in a separate review, and only confirmed
  fixes were applied (`eval/review_fixes.py`).

## Consequences

- Held-out numbers measure settings that were frozen before the run.
- The sets are small: one held-out question moves a rate by 4–11 points, so differences
  between dev and held-out are partly noise.
- The source-span review checks agreement with the snapshot; it is not a domain-expert assessment.
