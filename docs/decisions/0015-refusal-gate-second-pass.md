# 15. Choose the refusal gate for the second pass by a rule fixed in advance

Status: accepted, 2026-11-25. The rule below was committed before any gate comparison ran (commit `cce1d58`).

## Context

The second-pass baseline ([14](0014-second-pass-split.md), `reports/pass2/baseline_dev.md`)
showed three problems with the deployed rerank gate (−0.9831, fitted on 31 questions):

- it refuses 3 answerable dev questions, which then fail for every model;
- the unanswerable question it let through was refused by all three models anyway;
- the same balanced-accuracy fit on the 55-question dev set lands at 0.4724, so the
  threshold's position depends heavily on which questions happen to be in dev.

## Variants

All variants use the deployed retrieval (hybrid + `bge-reranker-base`, `top_k` 8) and the
top cross-encoder score of each question:

- **G0, no gate:** every question reaches the model.
- **G1, current:** −0.9831.
- **G2, refit:** the balanced-accuracy fit on the 55 dev questions ([7](0007-refusal-gates.md)'s
  rule), 0.4724.
- **G3, recall-first:** the highest threshold that keeps every answerable dev question. It sits
  midway between the lowest answerable score and the next lower observed score. Its only job
  is to stop questions that are far from the corpus before they reach the model.

The gate decides only whether the model sees the retrieved context, and the context is the same
under every variant. Each variant is therefore evaluated exactly, without a separate run:

- a question under the threshold is `refused_retrieval`;
- any other question takes its model outcome from `reports/answers/pass2_dev_baseline/`;
- for the questions the current gate refused, the model outcome comes from a run with the gate
  disabled.

## Selection rule

1. For each variant and each of the three chosen model variants, compute the score already used
   to choose reasoning variants ([8](0008-pre-registered-selection-rules.md)):
   (answerable questions answered with valid citations + correct refusals) / 2.
2. A variant is excluded if, for any model, it lets an unanswerable question be answered
   (claimed answer, valid citation or not).
3. Among the remaining variants, pick the one with the highest mean score over the three models.
   Variants within half an answerable question (0.5 / 44 of the score) of the best are decided
   by fewer model calls on dev, which is the gate's remaining purpose: cost and latency.

The judge is not used, as in [8](0008-pre-registered-selection-rules.md).

## Result

`reports/pass2/gates_dev.md`. The replayed current gate reproduced the saved run's refusals exactly.

| Variant | Threshold | Mean score | Unanswerable answered | Model calls |
| --- | --- | --- | --- | --- |
| G0 no gate | none | 0.867 | 0 | 55 |
| G1 current | −0.9831 | 0.852 | 0 | 42 |
| G2 refit | 0.4724 | 0.852 | 0 | 41 |
| **G3 recall-first** | **−6.2459** | **0.867** | 0 | 54 |

No variant let a model answer an unanswerable question. G0 and G3 tie on score, and G3 makes one fewer model call, so the rule picks G3. `/ask` now uses `rerank_min_score = -6.2459`.

## Consequences

- Compared with the first-pass gate, Flash-Lite and qwen3:4b each answer 2 more answerable dev questions with valid citations (`working-set`, `broadcast-edit`). qwen3.5:4b gains none: it refused both.
- Refusing unanswerable questions is now mainly the model's job. On dev all three models refused all 11 unanswerable questions without the gate. The gate only stops questions far from the corpus (on dev, one: `aousd-fee`, −6.54).
- The margin is thin. The lowest-scoring answerable dev question (`working-set`) scores −5.95, so a held-out answerable question can still fall below the threshold. Held-out v2 measures this.
- More questions reach the model (54 of 55 on dev, against 42), which costs latency and, for Gemini, money.
