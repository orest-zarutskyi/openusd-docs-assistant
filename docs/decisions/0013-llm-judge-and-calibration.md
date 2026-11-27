# 13. Grade answers with a separate LLM judge and calibrate it against reference labels

Status: accepted, 2026-11-24.

## Context

Citation checks prove that quotes exist, not that the answer is complete or that every claim
is supported. Grading 60–100 answers per run by hand does not scale, but an unchecked LLM judge
is only an opinion.

## Decision

- The judge prompt lives in `eval/prompts/judge.md`. For each expected fact the judge decides
  whether it is covered. It splits the answer into atomic claims and marks each one
  supported, unsupported or contradicted, using only the retrieved excerpts.
- Verdicts are cached with the judge model and the prompt's hash, and appended one by one.
  A crash keeps finished verdicts, and an unusable reply is asked again on the next run.
- The judge model must not be one of the compared models. It is `gemini-3.8-flash`.
- The Gemini free tier allows 20 judge requests a day, too few for one run, so the judge ran
  through the apils.in OpenAI-compatible gateway. The gateway is a reseller, and the report
  names it.
- Calibration uses 20 answers, sampled evenly across the three chosen variants and shuffled.
  Reference labels were prepared before the judge ran (`eval/llm_labels.jsonl`).
  Agreement and Cohen's kappa are reported for facts and for full groundedness.

## Consequences

- On dev the judge agreed with the reference on 95% of facts (κ 0.85) and on 95% of
  groundedness calls (κ 0.64). Kappa is lower for groundedness because only one of the 20
  references is ungrounded. The judge was the stricter side in all three disagreements, each
  a borderline case.
- Calibration measures agreement with the reference labels; it does not establish correctness
  on its own. The reference labels were fixed before the judge ran and were not adjusted to
  match its verdicts.
- Evidence: `reports/judge_calibration_dev.md`, `reports/answers_dev.md`,
  `reports/answers_heldout.md`.
