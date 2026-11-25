import pytest

from openusd_assistant.answer_eval import AnswerRecord
from openusd_assistant.gate_compare import (
    apply_gate,
    choose_gate,
    evaluate_gate,
    gate_report,
    merge_outcomes,
    recall_first_threshold,
)


def rec(qid, answerable, outcome, model="m"):
    return AnswerRecord(qid, "lookup" if answerable else "unanswerable", answerable, model, outcome)


def test_merge_fills_gated_questions_and_requires_every_one():
    behind = [rec("a", True, "answer"), rec("b", True, "refused_retrieval")]
    merged = merge_outcomes(behind, [rec("b", True, "answer")])
    assert merged["b"].outcome == "answer" and merged["a"].outcome == "answer"
    with pytest.raises(ValueError, match="No gate-off answer"):
        merge_outcomes(behind, [])


def test_apply_gate_refuses_below_threshold_and_missing_scores():
    answers = {"a": rec("a", True, "answer"), "u": rec("u", False, "refused_model")}
    out = {r.id: r.outcome for r in apply_gate(answers, {"a": 0.5, "u": None}, 0.0)}
    assert out == {"a": "answer", "u": "refused_retrieval"}
    assert all(
        r.outcome != "refused_retrieval" for r in apply_gate(answers, {"a": -9, "u": -9}, None)
    )


def test_recall_first_keeps_every_answerable_question():
    scores = {"a": 0.2, "b": -1.0, "u1": -3.0, "u2": 1.5}
    t = recall_first_threshold(scores, {"a", "b"})
    assert t == pytest.approx(-2.0)
    assert recall_first_threshold({"a": 1.0, "u": 2.0}, {"a"}) == pytest.approx(0.0)


def test_choose_gate_excludes_leaks_and_breaks_ties_by_model_calls():
    scores = {"a": 1.0, "b": -2.0, "u": -5.0}
    answers = {
        "m": {
            "a": rec("a", True, "answer"),
            "b": rec("b", True, "answer"),
            "u": rec("u", False, "refused_model"),
        }
    }
    results = {
        "G0": evaluate_gate(answers, scores, None),
        "G3": evaluate_gate(answers, scores, -3.5),
        "G2": evaluate_gate(answers, scores, 0.0),
    }
    assert results["G0"]["mean_score"] == results["G3"]["mean_score"] == 1.0
    assert results["G2"]["models"]["m"]["answered_answerable"] == 1
    assert choose_gate(results, answerable=2) == "G3"  # same score, one fewer model call
    leaky = {"m": {**answers["m"], "u": rec("u", False, "answer")}}
    results["G0"] = evaluate_gate(leaky, scores, None)
    assert results["G0"]["leaks"] == 1 and choose_gate(results, answerable=2) == "G3"
    assert "| G3 | -3.5000 | 1.000 | 0 | 2 | 2 | yes |" in gate_report(results, "G3", [])
