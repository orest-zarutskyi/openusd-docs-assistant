"""Replay first-pass settings on second-pass answers to compare the passes on one set (ADR 19)."""

from collections.abc import Sequence

from .answer_eval import (
    ANSWER,
    REFUSED_MODEL,
    REFUSED_RETRIEVAL,
    AnswerRecord,
    answer_metrics,
    reverify,
)
from .gate_compare import apply_gate
from .judge import Verdict, judge_metrics


def replay(
    records: Sequence[AnswerRecord], scores: dict[str, float | None], threshold: float, check
) -> list[AnswerRecord]:
    """Outcomes under another gate and citation check. Exact when ``threshold`` refuses a superset
    of what the saved run refused, since context and model output do not depend on either."""
    saved_refused = {r.id for r in records if r.outcome == REFUSED_RETRIEVAL}
    # A question the saved run refused but this threshold would pass has no answer to replay.
    missing = {q for q in saved_refused if scores[q] is not None and scores[q] >= threshold}
    if missing:
        raise ValueError(
            f"The replay would need answers the saved run never made: {sorted(missing)}"
        )
    replayed = apply_gate({r.id: r for r in records}, scores, threshold)
    return [reverify(r, check) for r in replayed]


def summarize(records: Sequence[AnswerRecord], verdicts: dict[str, Verdict | None], price) -> dict:
    metrics = answer_metrics(records, price) | judge_metrics(records, verdicts)
    answerable = [r for r in records if r.answerable]
    return metrics | {
        "answerable": len(answerable),
        "answered": sum(r.outcome == ANSWER for r in answerable),
        "refused_retrieval": sum(r.outcome == REFUSED_RETRIEVAL for r in answerable),
        "refused_model": sum(r.outcome == REFUSED_MODEL for r in answerable),
        "unanswerable": len(records) - len(answerable),
        "unanswerable_refused": sum(
            r.outcome in {REFUSED_RETRIEVAL, REFUSED_MODEL} for r in records if not r.answerable
        ),
    }


def passes_report(results: dict[str, dict[str, dict]], setup: Sequence[str]) -> str:
    def pct(v):
        return "—" if v is None else f"{v:.0%}"

    lines = [
        "# First pass vs second pass on held-out v2",
        "",
        *setup,
        "",
        "| Settings | Model | Answered with valid citations | Refused at retrieval | Refused by model | "
        "Unanswerable refused | Facts covered | Fully grounded | p50 s | $ / 100 q |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name, models in results.items():
        for spec, m in models.items():
            p50 = m["latency_ms"]["p50"]
            lines.append(
                f"| {name} | `{spec}` | {m['answered']} / {m['answerable']} | "
                f"{m['refused_retrieval']} | {m['refused_model']} | "
                f"{m['unanswerable_refused']} / {m['unanswerable']} | {pct(m['fact_coverage'])} | "
                f"{pct(m['fully_grounded'])} | {'—' if p50 is None else f'{p50 / 1000:.1f}'} | "
                f"${m['cost_per_100']:.4f} |"
            )
    lines += [
        "",
        "Facts covered and fully grounded come from the judge and cover the answers each setting "
        "accepts. Latency is that of the saved run for both rows: a replayed retrieval refusal "
        "keeps the generation time it had, so first-pass latency here is an upper bound.",
    ]
    return "\n".join(lines) + "\n"
