# 21. Choose the local model for the third pass by a rule fixed in advance

Status: accepted, 2026-11-25. The candidates and rule below were committed before any candidate ran
(`8494813`); the result was added after the runs.

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

## Result

From [models_dev.md](../../reports/pass3/models_dev.md), on the 115 dev questions (92 answerable,
23 unanswerable):

| Variant | Answered (valid) | Refused by model | Invalid citation | Invalid output | Score | p50 s | p95 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **qwen3.5:9b, thinking** | **74 / 92** | 6 | 8 | 0 | **0.902** | 15.7 | 54.7 |
| qwen3:4b, thinking | 68 / 92 | 11 | 3 | 7 | 0.848 | 15.7 | 61.2 |
| qwen3:8b, thinking | 62 / 92 | 9 | 16 | 1 | 0.837 | 41.4 | 149.2 |
| qwen3.5:4b, no thinking | 49 / 92 | 37 | 2 | 0 | 0.766 | 2.0 | 8.7 |
| qwen3:8b, no thinking | 22 / 92 | 61 | 3 | 2 | 0.620 | 4.7 | 16.2 |
| qwen3.5:9b, no thinking | 7 / 92 | 79 | 1 | 1 | 0.538 | 6.1 | 11.6 |

No variant answered an unanswerable question. The latency cap excludes qwen3:4b with thinking
(61.2 s) and qwen3:8b with thinking (149.2 s). **qwen3.5:9b with thinking is chosen.** It leads the
next variant by 5 answerable questions, so the tie rule did not apply.

- **Without thinking, the larger models refuse more.** qwen3.5:9b refused 79 of the 92 answerable
  questions and qwen3:8b refused 61, against 37 for qwen3.5:4b. With thinking, qwen3.5:9b refused 6.
- **The cap was not set blind.** When it was written, qwen3:4b with thinking was known to have a p95
  of 62.9 s on held-out v2. The cap therefore excludes that variant on dev by 1.2 s. It does not
  decide the result: qwen3.5:9b with thinking also has the best score among all variants.
- **Three answers were rerun.** Ollama stopped responding for about a minute during the qwen3:8b
  thinking run, and three consecutive questions (`usda-encoding`, `v2-32`, `v2-33`) ended in a
  provider error. They were rerun once with `eval-answers --ids` and the new records replaced the
  errors. That variant is excluded by latency either way.

## Consequences

- The default local model becomes `qwen3.5:9b` with `OPENUSD_OLLAMA_REASONING=true`, in `Settings`,
  `.env.example` and `compose.yaml`. Ollama reports 6.1 GB loaded, fully on the GPU, at `num_ctx` 16,384.
- Its dev p95 of 54.7 s is close to the cap, so `/ask` with a local model is slow for long answers.
  qwen3.5:4b without thinking stays the fast option (p95 8.7 s), at 25 fewer valid answers on dev.
- Held-out v3 runs Gemini Flash-Lite, qwen3:4b with thinking, qwen3.5:4b without thinking and
  qwen3.5:9b with thinking, after the third-pass settings are frozen.
