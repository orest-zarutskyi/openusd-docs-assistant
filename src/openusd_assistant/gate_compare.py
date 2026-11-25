"""Compare refusal-gate thresholds exactly by replaying saved answers (ADR 15).

The gate only decides whether the model sees the retrieved context, and that context does not
depend on the threshold. So any threshold can be evaluated from three inputs: each question's
top rerank score, the answers given behind the current gate, and answers given with the gate
off for the questions the current gate refused.
"""

from collections.abc import Sequence
from dataclasses import replace

from .answer_eval import (
    ANSWER,
    INVALID_CITATION,
    REFUSED_RETRIEVAL,
    AnswerRecord,
    Price,
    answer_metrics,
    variant_score,
)

CLAIMED = {ANSWER, INVALID_CITATION}


def merge_outcomes(
    behind_gate: Sequence[AnswerRecord], gate_off: Sequence[AnswerRecord]
) -> dict[str, AnswerRecord]:
    """The model's answer to every question: gate-off answers fill in what the gate refused."""
    merged = {r.id: r for r in behind_gate}
    for r in gate_off:
        if merged.get(r.id) is None or merged[r.id].outcome == REFUSED_RETRIEVAL:
            merged[r.id] = r
    missing = [i for i, r in merged.items() if r.outcome == REFUSED_RETRIEVAL]
    if missing:
        raise ValueError(f"No gate-off answer for {sorted(missing)}")
    return merged


def apply_gate(
    model_answers: dict[str, AnswerRecord], scores: dict[str, float | None], threshold: float | None
) -> list[AnswerRecord]:
    """Outcomes under ``threshold``: below it (or with no candidate) the retrieval refuses."""
    out = []
    for qid, record in model_answers.items():
        score = scores[qid]
        refused = threshold is not None and (score is None or score < threshold)
        out.append(replace(record, outcome=REFUSED_RETRIEVAL) if refused else record)
    return out


def recall_first_threshold(scores: dict[str, float | None], answerable: set[str]) -> float:
    """Highest threshold that keeps every answerable question: midway below the lowest one."""
    kept = [scores[q] for q in answerable]
    if any(s is None for s in kept):
        raise ValueError("An answerable question has no retrieval score.")
    lowest = min(kept)
    below = [s for s in scores.values() if s is not None and s < lowest]
    return (lowest + max(below)) / 2 if below else lowest - 1.0


def evaluate_gate(per_model: dict[str, dict[str, AnswerRecord]], scores, threshold) -> dict:
    """Score one threshold for every model with the variant rule; count leaks and model calls."""
    models = {}
    for spec, answers in per_model.items():
        records = apply_gate(answers, scores, threshold)
        metrics = answer_metrics(records, Price())
        models[spec] = {
            "score": variant_score(metrics),
            "answered_answerable": sum(r.answerable and r.outcome == ANSWER for r in records),
            "unanswerable_answered": sum(
                not r.answerable and r.outcome in CLAIMED for r in records
            ),
            "model_calls": sum(r.outcome != REFUSED_RETRIEVAL for r in records),
        }
    return {
        "threshold": threshold,
        "models": models,
        "mean_score": sum(m["score"] for m in models.values()) / len(models),
        "leaks": sum(m["unanswerable_answered"] for m in models.values()),
        "model_calls": max(m["model_calls"] for m in models.values()),
    }


def choose_gate(results: dict[str, dict], answerable: int) -> str:
    """ADR 15: drop variants that let any model answer an unanswerable question; take the best
    mean score; within half an answerable question of it, the variant with fewer model calls."""
    allowed = {name: r for name, r in results.items() if r["leaks"] == 0}
    if not allowed:
        raise ValueError("Every gate variant lets an unanswerable question be answered.")
    best = max(r["mean_score"] for r in allowed.values())
    tolerance = 0.5 / (2 * answerable) + 1e-9
    close = [n for n, r in allowed.items() if best - r["mean_score"] <= tolerance]
    return min(close, key=lambda n: (allowed[n]["model_calls"], n))


def gate_report(results: dict[str, dict], chosen: str, setup: Sequence[str]) -> str:
    specs = list(next(iter(results.values()))["models"])

    def fmt(t):
        return "none" if t is None else f"{t:.4f}"

    lines = [
        "# Refusal gate comparison: second pass, dev",
        "",
        *setup,
        "",
        "Rule (ADR 15, committed before this run): exclude variants that let any model answer an "
        "unanswerable question; highest mean score over the models, where score = (answerable "
        "answered with valid citations + correct refusals) / 2; within half an answerable "
        "question of the best, fewer model calls.",
        "",
        "| Variant | Threshold | Mean score | Unanswerable answered | Model calls | "
        + " | ".join(f"`{s}` answered" for s in specs)
        + " | Chosen |",
        "| --- | --- | --- | --- | --- | " + " | ".join("---" for _ in specs) + " | --- |",
    ]
    for name, r in results.items():
        cells = " | ".join(str(r["models"][s]["answered_answerable"]) for s in specs)
        lines.append(
            f"| {name} | {fmt(r['threshold'])} | {r['mean_score']:.3f} | {r['leaks']} | "
            f"{r['model_calls']} | {cells} | {'yes' if name == chosen else ''} |"
        )
    return "\n".join(lines) + "\n"
