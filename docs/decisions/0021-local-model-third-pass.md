# 21. Choose the local model for the third pass by a rule fixed in advance

Status: proposed, 2026-11-25. The candidates and rule below were committed before any candidate ran.

## Context

After the second pass, the local models' false refusals are the largest gap. On held-out v2,
qwen3.5:4b refused 27 of the 44 answerable questions that reached it, and qwen3:4b refused 6.
qwen3:4b also ended 7 answers in invalid output. A prompt change did not help
([17](0017-answer-prompt-second-pass.md)). The remaining lever is a larger model that still runs
locally on the evaluation machine (RTX 4070 Ti, 12 GB).

## Candidates

Every candidate uses the frozen second-pass settings: retrieval, gate −6.2459, `fragments`
citation check, prompt `v1`, `num_ctx` 16,384, and output caps of 800 tokens (6,144 with thinking).

- Current: `ollama:qwen3:4b@think`, `ollama:qwen3.5:4b@nothink`.
- New: `ollama:qwen3:8b@think`, `ollama:qwen3:8b@nothink`, `ollama:qwen3.5:9b@think`,
  `ollama:qwen3.5:9b@nothink`.

## Evaluation

All candidates are scored on the 115 dev questions ([20](0020-third-pass-split.md)). The current
variants need no new run, because every part of their dev answers already exists under the frozen
settings:

- the 55 earlier dev questions are replayed from `reports/answers/pass2_dev_baseline/` and
  `pass2_dev_nogate/` with the gate and check applied;
- the 60 former held-out v2 questions come from `reports/answers/pass2_heldout_v2/`.

The new variants run on all 115 questions in one session.

## Selection rule

1. Score = (answerable answered with valid citations + correct refusals) / 2, the variant score of
   [8](0008-pre-registered-selection-rules.md).
2. Exclude a variant that answers any unanswerable question (a claimed answer, valid citation or
   not). Also exclude one whose p95 latency exceeds 60 s, so that `/ask` stays usable.
3. The best remaining variant becomes the default local model (`OPENUSD_CHAT_MODEL`,
   `OPENUSD_OLLAMA_REASONING`). Within half an answerable question of the best, the lower p50
   latency wins.
4. Held-out v3 then runs Gemini Flash-Lite, the two current local variants and the chosen variant,
   if it is new. The old and new local models are thus compared on the same questions.

The judge is not used for the choice. It is reported on held-out v3.

## Consequences

Filled in after the comparison.
