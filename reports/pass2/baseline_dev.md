# Second-pass baseline on dev (55 questions)

These are the first-pass settings (tag `pass-1`), unchanged, run on the enlarged dev set:
hybrid + `bge-reranker-base`, `top_k` 8, rerank gate −0.9831, and the reasoning variant chosen per
model. Every second-pass change is measured against this baseline on the same 55 questions.
Held-out v2 is not used until the second-pass settings are frozen.

Details: [retrieval_dev_baseline.md](retrieval_dev_baseline.md) and
[answers_dev_baseline.md](answers_dev_baseline.md). The answers are in
`reports/answers/pass2_dev_baseline/`.

## Retrieval

| Mode | hit@5 | MRR@5 | nDCG@10 | p95 ms |
| --- | --- | --- | --- | --- |
| hybrid (RRF) | 0.932 | 0.841 | 0.809 | 22 |
| hybrid + MiniLM | 0.932 | 0.864 | 0.824 | 584 |
| **hybrid + bge** (deployed) | 0.909 | 0.864 | 0.839 | 2636 |

The pre-registered rule still picks bge, and `top_k` stays 8. Missed at 5 by bge:
`pre-post-visit`, `working-set`, `broadcast-edit` and `switchable-asset-root`.

## Refusal gate

The deployed gate (−0.9831) refused 3 answerable questions: `working-set`, `broadcast-edit`
and `helper-geometry-in-renders`. It let 1 unanswerable question through, `webgpu-viewer`, and
all three models then refused it. Fitted again on these 55 questions, the balanced-accuracy
rule would move the threshold to 0.4724. The gate's position is therefore unstable across dev
sets.

## Answers

| Model | Answered with valid citations | False refusals (model) | Invalid citations | Facts covered | Fully grounded | p50 s |
| --- | --- | --- | --- | --- | --- | --- |
| Gemini 3.5 Flash-Lite | 37 / 44 | 0 | 4 | 82% | 100% | 5.7 |
| qwen3:4b, thinking | 30 / 44 | 5 | 6 | 80% | 93% | 13.1 |
| qwen3.5:4b, no thinking | 26 / 44 | 8 | 7 | 74% | 96% | 2.3 |

No model answered any of the 11 unanswerable questions. The 3 answerable questions refused by
the gate count against every model.

Answerable questions that failed, by model:

- **Flash-Lite, invalid citation:** `payload`, `reversible-hide`, `usdcat-to-text`,
  `specializes-vs-inherits`.
- **qwen3:4b, refused:** `stage`, `lightweight-asset-open`, `namespace-edit-ops`,
  `switchable-asset-root`, `specializes-vs-inherits`.
- **qwen3:4b, invalid citation:** `add-reference`, `reversible-hide`, `active-vs-visibility`,
  `constant-vs-uniform`, `session-layer-save`, `kind-model-abstract`.
- **qwen3.5:4b, refused:** `sublayers`, `default-prim`, `expression-targets`, `reversible-hide`,
  `languages`, `kind-model-abstract`, `instanceable-condition`, `move-without-touching-source`.
- **qwen3.5:4b, invalid citation:** `payload`, `attribute-block`, `active-vs-visibility`,
  `primvar-modes`, `collection-modes`, `switchable-asset-root`, `over-vs-def`.

Flash-Lite latency is higher than in the first pass (p50 5.7 s, against 2.0 s). The code path is
the same, so this is the free-tier API on the day of the run.

## What the second pass targets

1. **Retrieval misses.** Four answerable questions have no relevant chunk in the top 5.
2. **The refusal gate.** It costs 3 answerable questions, and models refused the one
   unanswerable question it let through. Its threshold also moves a lot between dev sets.
3. **Invalid citations.** These account for 4–7 answerable questions per model, mostly quotes
   that are close to the source but not word-exact.
4. **False refusals of the local models.** qwen3.5:4b refuses 8 answerable questions and
   qwen3:4b refuses 5, with the context in hand.
