"""Run the full question-answering workflow per model and score the answers."""

import json
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .chat import Usage
from .graph import _verified_answer
from .models import Chunk, DependencyTimeout, DependencyUnavailable, DraftAnswer, InvalidModelOutput
from .questions import Question
from .quotes import quote_in_text
from .retrieval_eval import percentile

# Outcomes of one question. Refusals can come from the retrieval gate or the model.
ANSWER = "answer"  # status answer, every quote found in a retrieved chunk
REFUSED_RETRIEVAL = "refused_retrieval"
REFUSED_MODEL = "refused_model"
INVALID_CITATION = "invalid_citation"  # status answer, but a quote or chunk ID is not in context
INVALID_OUTPUT = "invalid_output"  # response did not match the answer schema
ERROR = "error"  # provider unavailable or timed out after retries
REFUSALS = {REFUSED_RETRIEVAL, REFUSED_MODEL}


@dataclass
class AnswerRecord:
    id: str
    kind: str
    answerable: bool
    model: str
    outcome: str
    answer: str = ""
    quotes: list[dict] = field(default_factory=list)
    context: list[dict] = field(default_factory=list)
    latency_ms: float = 0.0
    generation_ms: float = 0.0
    usage: dict = field(default_factory=lambda: asdict(Usage()))


def answer_question(question: Question, retrieve, chat, model: str) -> AnswerRecord:
    record = AnswerRecord(question.id, question.kind, question.answerable, model, ERROR)
    started = time.perf_counter()
    context: list[Chunk] = retrieve(question.question)
    record.context = [
        {"chunk_id": c.id, "path": c.path, "lines": [c.start_line, c.end_line], "text": c.text}
        for c in context
    ]
    if not context:
        record.outcome = REFUSED_RETRIEVAL
        record.latency_ms = (time.perf_counter() - started) * 1000
        return record
    generation_started = time.perf_counter()
    try:
        draft, usage = chat.generate_with_usage(question.question, context)
        record.usage = asdict(usage)
        record.answer = draft.answer
        record.quotes = [e.model_dump() for e in draft.evidence]
        try:
            verified = _verified_answer(draft, context)
            record.outcome = ANSWER if verified.status == "answer" else REFUSED_MODEL
        except InvalidModelOutput:
            record.outcome = INVALID_CITATION
    except InvalidModelOutput as exc:
        record.outcome = INVALID_OUTPUT
        record.usage = asdict(getattr(exc, "usage", Usage()))
    except (DependencyUnavailable, DependencyTimeout):
        record.outcome = ERROR
    finished = time.perf_counter()
    record.generation_ms = (finished - generation_started) * 1000
    record.latency_ms = (finished - started) * 1000
    return record


def run_answers(
    questions: Sequence[Question],
    retrieve: Callable[[str], list[Chunk]],
    chat,
    model: str,
    *,
    progress: Callable[[AnswerRecord], None] = lambda record: None,
) -> list[AnswerRecord]:
    records = []
    for question in questions:
        record = answer_question(question, retrieve, chat, model)
        progress(record)
        records.append(record)
    return records


def save_records(path: Path, records: Sequence[AnswerRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = (json.dumps(asdict(r), ensure_ascii=False) for r in records)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def load_records(path: Path) -> list[AnswerRecord]:
    rows = path.read_text(encoding="utf-8").splitlines()
    return [AnswerRecord(**json.loads(row)) for row in rows if row.strip()]


@dataclass(frozen=True)
class Price:
    """USD per million tokens; thinking tokens are billed at the output rate."""

    input_per_million: float = 0.0
    output_per_million: float = 0.0

    def cost(self, usage: dict) -> float:
        output = usage["output_tokens"] + usage["thinking_tokens"]
        return (
            usage["input_tokens"] * self.input_per_million + output * self.output_per_million
        ) / 1e6


def rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def quote_is_valid(quote: dict, record: AnswerRecord) -> bool:
    """The same check as the API, applied to one quote."""
    text = next((c["text"] for c in record.context if c["chunk_id"] == quote["chunk_id"]), None)
    return text is not None and quote_in_text(quote["quote"], text)


def answer_metrics(records: Sequence[AnswerRecord], price: Price) -> dict:
    """Metrics that need no judge: citations, refusals, failures, latency and cost."""
    answerable = [r for r in records if r.answerable]
    unanswerable = [r for r in records if not r.answerable]
    claimed = [r for r in records if r.outcome in {ANSWER, INVALID_CITATION}]
    generated = [r for r in records if r.outcome != REFUSED_RETRIEVAL]
    latencies = [r.latency_ms for r in records if r.outcome != ERROR]
    return {
        "questions": len(records),
        # Of the answers the model claimed, the share whose every quote is in the context.
        "citation_validity": rate(sum(r.outcome == ANSWER for r in claimed), len(claimed)),
        # Of all quotes in claimed answers, the share found verbatim in the quoted chunk.
        "quote_validity": rate(
            sum(quote_is_valid(q, r) for r in claimed for q in r.quotes),
            sum(len(r.quotes) for r in claimed),
        ),
        "no_evidence_answers": sum(not r.quotes for r in claimed),
        "correct_refusal": rate(
            sum(r.outcome in REFUSALS for r in unanswerable), len(unanswerable)
        ),
        # Unanswerable questions that reached the model, and how many of those it refused.
        "unanswerable_reaching_model": sum(r.outcome != REFUSED_RETRIEVAL for r in unanswerable),
        "model_refused_unanswerable": sum(r.outcome == REFUSED_MODEL for r in unanswerable),
        "false_refusal": rate(sum(r.outcome in REFUSALS for r in answerable), len(answerable)),
        "answered_answerable": rate(sum(r.outcome == ANSWER for r in answerable), len(answerable)),
        "invalid_output": rate(sum(r.outcome == INVALID_OUTPUT for r in generated), len(generated)),
        "errors": sum(r.outcome == ERROR for r in records),
        "latency_ms": {
            "p50": percentile(latencies, 0.5) if latencies else None,
            "p95": percentile(latencies, 0.95) if latencies else None,
        },
        "tokens": {
            key: sum(r.usage[key] for r in records)
            for key in ("input_tokens", "output_tokens", "thinking_tokens")
        },
        "cost_per_100": sum(price.cost(r.usage) for r in records) / len(records) * 100
        if records
        else None,
    }


def variant_score(metrics: dict) -> float:
    """Balanced accuracy: answerable questions answered with valid citations, and correct refusals."""
    return ((metrics["answered_answerable"] or 0) + (metrics["correct_refusal"] or 0)) / 2


def choose_variants(results: dict[str, dict], answerable: int) -> dict[str, str]:
    """Pre-registered rule: per model, highest ``variant_score``; variants within one
    answerable question of the best are decided by lower p50 latency.

    The rule uses no judge output, so tuning settings cannot bias the judge's calibration.
    """
    by_model: dict[str, list[str]] = {}
    for spec in results:
        by_model.setdefault(spec.partition("@")[0], []).append(spec)
    tolerance = 1 / (2 * answerable) + 1e-9
    chosen = {}
    for model, specs in by_model.items():
        best = max(variant_score(results[s]) for s in specs)
        close = [s for s in specs if best - variant_score(results[s]) <= tolerance]
        chosen[model] = min(close, key=lambda s: results[s]["latency_ms"]["p50"] or float("inf"))
    return chosen


def reverify(record: AnswerRecord) -> AnswerRecord:
    """Re-apply the API's citation check to a saved answer without calling the model again."""
    if record.outcome not in {ANSWER, INVALID_CITATION}:
        return record
    context = [
        Chunk(
            id=c["chunk_id"],
            path=c["path"],
            title="",
            start_line=c["lines"][0],
            end_line=c["lines"][1],
            text=c["text"],
            url="https://example.invalid/",
        )
        for c in record.context
    ]
    try:
        draft = DraftAnswer(status="answer", answer=record.answer, evidence=record.quotes)
        _verified_answer(draft, context)
        outcome = ANSWER
    except (InvalidModelOutput, ValueError):
        outcome = INVALID_CITATION
    return AnswerRecord(**{**asdict(record), "outcome": outcome})
