"""Rank-quality, refusal-gate and latency metrics for retrieval modes, scored on source lines."""

import math
import time
from collections.abc import Sequence
from dataclasses import dataclass

from .models import Chunk
from .questions import Question, SourceSpan
from .retrieval import Searcher

DEPTH = 10  # deepest cut-off any metric needs (nDCG@10)
HIT_KS = (1, 3, 5, 8, 10)
WARMUP_QUERIES = 3


def overlaps(chunk: Chunk, span: SourceSpan) -> bool:
    """Primary relevance rule: the chunk shares at least one line with an expected span."""
    return (
        chunk.path == span.path
        and chunk.start_line <= span.end_line
        and span.start_line <= chunk.end_line
    )


def contains(chunk: Chunk, span: SourceSpan) -> bool:
    """Stage-1 rule, kept for comparison: the chunk holds the whole expected span."""
    return (
        chunk.path == span.path
        and chunk.start_line <= span.start_line
        and chunk.end_line >= span.end_line
    )


def first_rank(ranked: Sequence[Chunk], spans: Sequence[SourceSpan], rule, k: int) -> int | None:
    return next(
        (rank for rank, chunk in enumerate(ranked[:k], 1) if any(rule(chunk, s) for s in spans)),
        None,
    )


def ndcg(
    ranked: Sequence[Chunk], spans: Sequence[SourceSpan], relevant_total: int, k: int
) -> float:
    """Binary-gain nDCG@k; the ideal ranking puts every relevant corpus chunk first."""
    gains = [any(overlaps(chunk, s) for s in spans) for chunk in ranked[:k]]
    dcg = sum(1 / math.log2(rank + 1) for rank, gain in enumerate(gains, 1) if gain)
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(relevant_total, k) + 1))
    return dcg / ideal if ideal else 0.0


def percentile(values: Sequence[float], q: float) -> float:
    """Nearest-rank percentile, so p95 is an observed latency rather than an interpolation."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q * len(ordered)) - 1)]


@dataclass(frozen=True)
class Gate:
    threshold: float | None
    answerable_kept: float
    unanswerable_refused: float

    @property
    def balanced_accuracy(self) -> float:
        return (self.answerable_kept + self.unanswerable_refused) / 2


def best_gate(answerable: Sequence[float | None], unanswerable: Sequence[float | None]) -> Gate:
    """Pick the threshold that maximizes balanced accuracy; ties go to the lower threshold.

    The gate only decides whether the model sees any context, so a lower threshold is
    preferred on ties: the model can still refuse, but it cannot answer from nothing.
    """
    if all(score is None for score in (*answerable, *unanswerable)):
        return Gate(None, 1.0, 0.0)  # no calibrated score: never refuse at retrieval time
    # A missing score (no candidate at all) is refused by gated(), like the lowest score.
    answerable = [-math.inf if s is None else s for s in answerable]
    unanswerable = [-math.inf if s is None else s for s in unanswerable]
    observed = sorted({s for s in (*answerable, *unanswerable) if s != -math.inf})
    # Cut midway between neighbouring observed scores, so the chosen threshold keeps a
    # margin on both sides instead of sitting exactly on a dev question's score.
    candidates = [observed[0], *((a + b) / 2 for a, b in zip(observed, observed[1:]))]
    best = None
    for threshold in candidates:
        gate = Gate(
            threshold,
            sum(s >= threshold for s in answerable) / len(answerable),
            sum(s < threshold for s in unanswerable) / len(unanswerable),
        )
        if best is None or gate.balanced_accuracy > best.balanced_accuracy:
            best = gate
    return best


def evaluate_searcher(
    questions: Sequence[Question], searcher: Searcher, chunks: Sequence[Chunk]
) -> dict:
    for question in questions[:WARMUP_QUERIES]:
        searcher.search(question.question, DEPTH)  # load models and caches before timing

    cases, latencies = [], []
    for q in questions:
        started = time.perf_counter()
        result = searcher.search(q.question, DEPTH)
        latencies.append((time.perf_counter() - started) * 1000)
        case = {
            "id": q.id,
            "kind": q.kind,
            "answerable": q.answerable,
            "confidence": result.confidence,
        }
        if q.answerable:
            relevant_total = sum(any(overlaps(c, s) for s in q.sources) for c in chunks)
            case |= {
                "first_rank": first_rank(result.chunks, q.sources, overlaps, DEPTH),
                "first_rank_strict": first_rank(result.chunks, q.sources, contains, DEPTH),
                "ndcg10": ndcg(result.chunks, q.sources, relevant_total, DEPTH),
            }
        cases.append(case)

    scored = [case for case in cases if case["answerable"]]
    if not scored:
        raise ValueError("The evaluation needs at least one answerable question.")

    def hit(k: int, key: str = "first_rank") -> float:
        return sum(c[key] is not None and c[key] <= k for c in scored) / len(scored)

    def mrr(k: int) -> float:
        return sum(
            1 / c["first_rank"] for c in scored if c["first_rank"] and c["first_rank"] <= k
        ) / len(scored)

    gate = (
        best_gate(
            [c["confidence"] for c in scored],
            [c["confidence"] for c in cases if not c["answerable"]],
        )
        if len(scored) < len(cases)
        else Gate(None, 1.0, 0.0)
    )
    return {
        "answerable": len(scored),
        "unanswerable": len(cases) - len(scored),
        "hit@5": hit(5),
        "mrr@5": mrr(5),
        "ndcg@10": sum(c["ndcg10"] for c in scored) / len(scored),
        "hit@5_strict": hit(5, "first_rank_strict"),
        "hit@k": {k: hit(k) for k in HIT_KS},
        "latency_ms": {"p50": percentile(latencies, 0.50), "p95": percentile(latencies, 0.95)},
        "gate": gate,
        "cases": cases,
    }


def gate_at(
    threshold: float | None,
    answerable: Sequence[float | None],
    unanswerable: Sequence[float | None],
) -> Gate:
    """How a fixed threshold (frozen on dev) performs; a missing score is refused, as in gated()."""
    if threshold is None:
        return Gate(None, 1.0, 0.0)
    kept = sum(s is not None and s >= threshold for s in answerable)
    refused = sum(s is None or s < threshold for s in unanswerable)
    return Gate(
        threshold,
        kept / len(answerable) if answerable else 0.0,
        refused / len(unanswerable) if unanswerable else 0.0,
    )


def apply_frozen_gates(results: dict[str, dict], thresholds: dict[str, float | None]) -> None:
    """Replace each mode's fitted gate with its dev threshold; modes without one get no gate."""
    for name, r in results.items():
        cases = r["cases"]
        r["gate"] = (
            gate_at(
                thresholds[name],
                [c["confidence"] for c in cases if c["answerable"]],
                [c["confidence"] for c in cases if not c["answerable"]],
            )
            if name in thresholds
            else None
        )


def choose_winner(results: dict[str, dict], tie: float = 0.01) -> str:
    """Pre-registered rule: highest nDCG@10; within ``tie`` of the best, lowest p95 latency."""
    best = max(result["ndcg@10"] for result in results.values())
    close = [name for name, result in results.items() if best - result["ndcg@10"] < tie]
    return min(close, key=lambda name: results[name]["latency_ms"]["p95"])


def choose_top_k(hit_at_k: dict[int, float], answerable: int, options=(3, 5, 8)) -> int:
    """Smallest k whose hit rate is within one question of hit@10."""
    target = hit_at_k[DEPTH] - 1 / answerable
    return next((k for k in options if hit_at_k[k] >= target - 1e-9), options[-1])


def markdown_report(
    results: dict[str, dict],
    *,
    winner: str,
    top_k: int,
    title: str,
    setup: Sequence[str],
    frozen: bool = False,
) -> str:
    """Comparison report. With ``frozen`` (held-out), ``winner``, ``top_k`` and the gates are
    the dev choices applied unchanged, and nothing is selected on these questions."""

    def f(value: float) -> str:
        return f"{value:.3f}"

    label = "deployed" if frozen else "winner"

    lines = [
        f"# {title}",
        "",
        *setup,
        "",
        "Relevance: a chunk is relevant if it shares a line with an expected source span. "
        "`hit@5 strict` uses the stage-1 rule (the chunk contains the whole span).",
        "",
        "| Mode | hit@5 | MRR@5 | nDCG@10 | hit@5 strict | p50 ms | p95 ms |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name, r in results.items():
        mark = f" **({label})**" if name == winner else ""
        lines.append(
            f"| {name}{mark} | {f(r['hit@5'])} | {f(r['mrr@5'])} | {f(r['ndcg@10'])} | "
            f"{f(r['hit@5_strict'])} | {r['latency_ms']['p50']:.0f} | {r['latency_ms']['p95']:.0f} |"
        )
    lines += [
        "",
        (
            "Held-out run: every setting was frozen on dev (`reports/retrieval_dev.md`) and "
            "nothing below was selected on these questions. **(deployed)** marks the mode "
            "`/ask` uses."
            if frozen
            else "Winner rule, fixed before the run: highest nDCG@10; modes within 0.01 of it "
            "are decided by the lower p95 latency."
        ),
        "",
        "## Hit rate by cut-off",
        "",
        "| Mode | " + " | ".join(f"hit@{k}" for k in HIT_KS) + " |",
        "| --- |" + " --- |" * len(HIT_KS),
        *(
            f"| {name} | " + " | ".join(f(r["hit@k"][k]) for k in HIT_KS) + " |"
            for name, r in results.items()
        ),
        "",
        (
            f"top_k for `/ask`: **{top_k}**, frozen on dev."
            if frozen
            else f"top_k for `/ask`: **{top_k}**, the smallest of 3, 5, 8 whose hit rate for "
            "the winner is within one question of its hit@10."
        ),
        "",
        "## Refusal gate",
        "",
        (
            "Thresholds are the dev settings `/ask` applies (`min_score` for dense and hybrid, "
            "`rerank_min_score` for the deployed reranker); a mode with no frozen threshold "
            "shows none. BM25 has no calibrated score, so it cannot refuse at retrieval time."
            if frozen
            else "The threshold maximizes balanced accuracy over dev questions: answerable "
            "questions must pass, unanswerable ones must be refused. BM25 has no calibrated "
            "score, so it cannot refuse at retrieval time."
        ),
        "",
        "| Mode | Gate score | Threshold | Answerable kept | Unanswerable refused |",
        "| --- | --- | --- | --- | --- |",
    ]
    gate_score = {"bm25": "none", "dense": "top cosine", "hybrid": "best dense cosine"}
    for name, r in results.items():
        g = r["gate"]
        score = gate_score.get(name, "top cross-encoder score")
        if g is None:
            lines.append(f"| {name} | {score} | not frozen on dev | — | — |")
            continue
        threshold = "—" if g.threshold is None else f"{g.threshold:.4f}"
        lines.append(
            f"| {name} | {score} | {threshold} | {f(g.answerable_kept)} | {f(g.unanswerable_refused)} |"
        )
    lines += ["", "## Missed at 5", "", "| Mode | Questions |", "| --- | --- |"]
    for name, r in results.items():
        misses = [
            c["id"]
            for c in r["cases"]
            if c["answerable"] and not (c["first_rank"] and c["first_rank"] <= 5)
        ]
        lines.append(f"| {name} | {', '.join(f'`{m}`' for m in misses) or 'none'} |")
    return "\n".join(lines) + "\n"
