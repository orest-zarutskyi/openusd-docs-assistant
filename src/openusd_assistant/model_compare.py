"""Compare local model variants on the third-pass dev set (ADR 21)."""

from pathlib import Path

from .answer_eval import (
    ANSWER,
    INVALID_CITATION,
    INVALID_OUTPUT,
    REFUSED_MODEL,
    AnswerRecord,
    Price,
    answer_metrics,
    variant_score,
)
from .prompt_compare import fresh_run, replayed_baseline

MAX_P95_MS = 60_000


def current_variants(
    baseline: Path, nogate: Path, scores: Path, former_heldout: Path, threshold, check
):
    """Current variants' answers on all dev questions, from saved runs under the frozen settings."""
    replayed = replayed_baseline(baseline, nogate, scores, threshold, check)
    former = fresh_run(former_heldout, check)
    return {spec: replayed[spec] + former.get(spec, []) for spec in replayed}


def summarize(records: list[AnswerRecord]) -> dict:
    metrics = answer_metrics(records, Price())
    answerable = [r for r in records if r.answerable]
    return {
        "questions": len(records),
        "score": variant_score(metrics),
        "answered": sum(r.outcome == ANSWER for r in answerable),
        "answerable": len(answerable),
        "refused": sum(r.outcome == REFUSED_MODEL for r in answerable),
        "invalid_citation": sum(r.outcome == INVALID_CITATION for r in answerable),
        "invalid_output": sum(r.outcome == INVALID_OUTPUT for r in records),
        "unanswerable_refused": sum(
            r.outcome in {"refused_retrieval", REFUSED_MODEL} for r in records if not r.answerable
        ),
        "unanswerable": len(records) - len(answerable),
        "leaks": sum(not r.answerable and r.outcome in {ANSWER, INVALID_CITATION} for r in records),
        "p50_ms": metrics["latency_ms"]["p50"],
        "p95_ms": metrics["latency_ms"]["p95"],
    }


def choose_model(results: dict[str, dict], answerable: int) -> str:
    """ADR 21: no leaks and p95 within the cap; best score; within half an answerable question,
    the lower p50 latency."""
    allowed = {
        s: r for s, r in results.items() if r["leaks"] == 0 and (r["p95_ms"] or 0) <= MAX_P95_MS
    }
    if not allowed:
        raise ValueError("No variant meets the leak and latency limits.")
    best = max(r["score"] for r in allowed.values())
    tolerance = 0.5 / (2 * answerable) + 1e-9
    close = [s for s, r in allowed.items() if best - r["score"] <= tolerance]
    return min(close, key=lambda s: (allowed[s]["p50_ms"] or float("inf"), s))


def models_report(results: dict[str, dict], chosen: str, setup: list[str]) -> str:
    def sec(ms):
        return "—" if ms is None else f"{ms / 1000:.1f}"

    lines = [
        "# Local model comparison: third pass, dev",
        "",
        *setup,
        "",
        "Rule (ADR 21, committed before the runs): exclude variants that answer an unanswerable "
        "question or whose p95 latency exceeds 60 s; highest score = (answerable answered with valid "
        "citations + correct refusals) / 2; within half an answerable question, lower p50.",
        "",
        "| Variant | Answered (valid) | Refused by model | Invalid citation | Invalid output | "
        "Unanswerable refused | Score | p50 s | p95 s | Chosen |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for spec, r in sorted(results.items(), key=lambda kv: -kv[1]["score"]):
        lines.append(
            f"| `{spec}` | {r['answered']} / {r['answerable']} | {r['refused']} | "
            f"{r['invalid_citation']} | {r['invalid_output']} | "
            f"{r['unanswerable_refused']} / {r['unanswerable']} | {r['score']:.3f} | "
            f"{sec(r['p50_ms'])} | {sec(r['p95_ms'])} | {'yes' if spec == chosen else ''} |"
        )
    return "\n".join(lines) + "\n"
