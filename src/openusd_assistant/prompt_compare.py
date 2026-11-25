"""Compare answer prompts on dev under the deployed gate and citation check (ADR 17)."""

import json
from pathlib import Path

from .answer_eval import (
    ANSWER,
    INVALID_CITATION,
    REFUSED_MODEL,
    AnswerRecord,
    Price,
    answer_metrics,
    load_records,
    reverify,
    variant_score,
)
from .gate_compare import apply_gate, merge_outcomes


def _runs(directory: Path) -> dict[str, list[AnswerRecord]]:
    files = [f for f in sorted(directory.glob("*.jsonl")) if f.name != "verdicts.jsonl"]
    return {load_records(f)[0].model: load_records(f) for f in files}


def replayed_baseline(baseline: Path, nogate: Path, scores: Path, threshold: float, check) -> dict:
    """The first-pass prompt's answers under the deployed gate and citation check."""
    gate_scores = json.loads(scores.read_text(encoding="utf-8"))
    gate_off = _runs(nogate)
    return {
        spec: [
            reverify(r, check)
            for r in apply_gate(
                merge_outcomes(records, gate_off.get(spec, [])), gate_scores, threshold
            )
        ]
        for spec, records in _runs(baseline).items()
    }


def fresh_run(directory: Path, check) -> dict:
    return {
        spec: [reverify(r, check) for r in records] for spec, records in _runs(directory).items()
    }


def summarize(per_model: dict[str, list[AnswerRecord]]) -> dict:
    models = {}
    for spec, records in per_model.items():
        metrics = answer_metrics(records, Price())
        models[spec] = {
            "score": variant_score(metrics),
            "answered": sum(r.answerable and r.outcome == ANSWER for r in records),
            "refused": sum(r.answerable and r.outcome == REFUSED_MODEL for r in records),
            "invalid": sum(r.answerable and r.outcome == INVALID_CITATION for r in records),
            "leaks": sum(
                not r.answerable and r.outcome in {ANSWER, INVALID_CITATION} for r in records
            ),
        }
    return {
        "models": models,
        "mean_score": sum(m["score"] for m in models.values()) / len(models),
        "leaks": sum(m["leaks"] for m in models.values()),
    }


def choose_prompt(results: dict[str, dict], answerable: int, current: str = "v1") -> str:
    """ADR 17: no leaks; higher mean score; within half an answerable question, keep current."""
    allowed = {name: r for name, r in results.items() if r["leaks"] == 0}
    if not allowed:
        raise ValueError("Every prompt lets a model answer an unanswerable question.")
    best = max(r["mean_score"] for r in allowed.values())
    tolerance = 0.5 / (2 * answerable) + 1e-9
    if current in allowed and best - allowed[current]["mean_score"] <= tolerance:
        return current
    return max(allowed, key=lambda n: allowed[n]["mean_score"])


def prompt_report(results: dict[str, dict], chosen: str, setup: list[str]) -> str:
    specs = list(next(iter(results.values()))["models"])
    lines = [
        "# Answer prompt comparison: second pass, dev",
        "",
        *setup,
        "",
        "Rule (ADR 17, committed before the runs): exclude prompts with which any model answers an "
        "unanswerable question; higher mean score over the models; within half an answerable "
        "question of the best, keep v1.",
        "",
        "| Prompt | Model | Answered (valid) | Refused by model | Invalid citation | "
        "Unanswerable answered | Score |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name, r in results.items():
        for spec in specs:
            m = r["models"][spec]
            lines.append(
                f"| {name} | `{spec}` | {m['answered']} | {m['refused']} | {m['invalid']} | "
                f"{m['leaks']} | {m['score']:.3f} |"
            )
    lines += [
        "",
        "| Prompt | Mean score | Unanswerable answered | Chosen |",
        "| --- | --- | --- | --- |",
    ]
    for name, r in results.items():
        mark = "yes" if name == chosen else ""
        lines.append(f"| {name} | {r['mean_score']:.3f} | {r['leaks']} | {mark} |")
    return "\n".join(lines) + "\n"
