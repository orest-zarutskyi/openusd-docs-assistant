# Judge calibration: eval/llm_labels.jsonl

- Judge: `gemini-3.8-flash`; verdicts from `reports/answers/dev/verdicts.jsonl`.
- Reference labels: 20 answers.

| Decision | n | Agreement | Cohen's kappa |
| --- | --- | --- | --- |
| Expected fact covered | 44 | 95% | 0.85 |
| Answer fully grounded | 20 | 95% | 0.64 |

Disagreements:

- L03: fact 1 reference=True judge=False
- L08: fact 2 reference=True judge=False
- L09: grounded reference=True judge=False
