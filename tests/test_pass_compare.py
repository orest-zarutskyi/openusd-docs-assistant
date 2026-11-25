import pytest

from openusd_assistant.answer_eval import AnswerRecord
from openusd_assistant.pass_compare import replay, summarize


def rec(qid, answerable, outcome, quote="kept text here"):
    context = [{"chunk_id": "c", "path": "docs/x.rst", "lines": [1, 2], "text": "kept text here"}]
    return AnswerRecord(
        qid,
        "lookup" if answerable else "unanswerable",
        answerable,
        "m",
        outcome,
        answer="A.",
        quotes=[{"chunk_id": "c", "quote": quote}] if outcome == "answer" else [],
        context=context if outcome != "refused_retrieval" else [],
        latency_ms=1000,
    )


def test_replay_applies_a_stricter_gate_and_check():
    records = [
        rec("a", True, "answer"),
        rec("b", True, "answer", quote="Kept text here."),  # passes fragments, not strict
        rec("c", True, "answer"),
        rec("u", False, "refused_retrieval"),
    ]
    scores = {"a": 0.5, "b": 0.4, "c": -3.0, "u": -9.0}
    out = {r.id: r.outcome for r in replay(records, scores, -1.0, "strict")}
    assert out == {
        "a": "answer",
        "b": "invalid_citation",
        "c": "refused_retrieval",
        "u": "refused_retrieval",
    }
    summary = summarize(list(replay(records, scores, -1.0, "strict")), {}, _price())
    assert summary["answered"] == 1 and summary["refused_retrieval"] == 1
    assert summary["unanswerable_refused"] == 1


def test_replay_refuses_to_invent_answers_for_a_looser_gate():
    records = [rec("u", False, "refused_retrieval")]
    with pytest.raises(ValueError, match="never made"):
        replay(records, {"u": -9.0}, -10.0, "strict")


def _price():
    from openusd_assistant.answer_eval import Price

    return Price()
