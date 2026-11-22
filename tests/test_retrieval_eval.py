import math

import pytest

from openusd_assistant.models import Chunk
from openusd_assistant.questions import Question, SourceSpan
from openusd_assistant.retrieval import SearchResult
from openusd_assistant.retrieval_eval import (
    Gate,
    best_gate,
    choose_top_k,
    choose_winner,
    contains,
    evaluate_searcher,
    markdown_report,
    ndcg,
    overlaps,
    percentile,
)


def chunk(start, end, path="docs/a.rst"):
    return Chunk(
        id=f"{path}:{start}",
        path=path,
        title="T",
        start_line=start,
        end_line=end,
        text="x",
        url=f"https://example.invalid/{start}",
    )


SPAN = SourceSpan(path="docs/a.rst", start_line=10, end_line=14)


@pytest.mark.parametrize(
    ("start", "end", "overlap", "contained"),
    [(1, 9, False, False), (1, 10, True, False), (12, 20, True, False), (8, 15, True, True)],
)
def test_relevance_rules(start, end, overlap, contained):
    assert overlaps(chunk(start, end), SPAN) is overlap
    assert contains(chunk(start, end), SPAN) is contained
    assert not overlaps(chunk(start, end, "docs/b.rst"), SPAN)


def test_ndcg_matches_a_hand_computed_value():
    relevant_a, relevant_b, other = chunk(8, 11), chunk(12, 13), chunk(30, 31)
    # Relevant at ranks 2 and 3; two relevant chunks exist in the corpus.
    value = ndcg([other, relevant_a, relevant_b], [SPAN], relevant_total=2, k=10)
    expected = (1 / math.log2(3) + 1 / math.log2(4)) / (1 + 1 / math.log2(3))
    assert value == pytest.approx(expected)
    assert ndcg([relevant_a, relevant_b], [SPAN], 2, 10) == pytest.approx(1.0)
    assert ndcg([other], [SPAN], 2, 10) == 0.0


def test_percentile_uses_nearest_rank():
    values = list(range(1, 21))  # 1..20
    assert percentile(values, 0.5) == 10
    assert percentile(values, 0.95) == 19
    assert percentile([7.0], 0.95) == 7.0


def test_best_gate_maximizes_balanced_accuracy_and_prefers_lower_thresholds():
    gate = best_gate([0.9, 0.8, 0.6], [0.5, 0.7])
    assert gate.threshold == 0.6 or gate.threshold == 0.8
    # 0.6: keeps 3/3, refuses 1/2 -> 0.75; 0.8: keeps 2/3, refuses 2/2 -> 0.833
    assert gate == Gate(0.8, 2 / 3, 1.0)
    assert best_gate([0.5, 0.5], [0.1]).threshold == 0.5
    assert best_gate([None], [None]) == Gate(None, 1.0, 0.0)
    missing = best_gate([0.9], [None])  # no candidates for the refusal case: already refused
    assert missing == Gate(0.9, 1.0, 1.0)


def test_winner_rule_breaks_near_ties_on_latency():
    results = {
        "dense": {"ndcg@10": 0.700, "latency_ms": {"p95": 30}},
        "hybrid": {"ndcg@10": 0.705, "latency_ms": {"p95": 40}},
        "rerank": {"ndcg@10": 0.650, "latency_ms": {"p95": 5}},
    }
    assert choose_winner(results) == "dense"
    results["hybrid"]["ndcg@10"] = 0.75
    assert choose_winner(results) == "hybrid"


def test_top_k_is_smallest_cut_off_within_one_question_of_hit_at_10():
    hits = {1: 0.5, 3: 0.7, 5: 0.85, 8: 0.9, 10: 0.9}
    assert choose_top_k(hits, answerable=20) == 5  # 0.85 >= 0.9 - 0.05
    assert choose_top_k(hits, answerable=100) == 8


class Scripted:
    def __init__(self, ranking):
        self.ranking = ranking

    def search(self, question, limit):
        chunks, confidence = self.ranking[question]
        return SearchResult(chunks[:limit], [1.0] * len(chunks[:limit]), confidence)


def make_question(id, answerable=True):
    return Question(
        id=id,
        question=f"Question {id} about stages?",
        kind="lookup" if answerable else "unanswerable",
        answerable=answerable,
        sources=[SPAN] if answerable else [],
        expected_facts=["F."] if answerable else [],
    )


def test_evaluate_searcher_end_to_end_and_report():
    hit, near, miss = chunk(9, 12), chunk(12, 30), chunk(40, 41)
    questions = [make_question("q1"), make_question("q2"), make_question("u1", answerable=False)]
    searcher = Scripted(
        {
            questions[0].question: ([hit], 0.9),
            questions[1].question: ([miss] * 5 + [near], 0.7),
            questions[2].question: ([miss], 0.4),
        }
    )
    result = evaluate_searcher(questions, searcher, chunks=[hit, near, miss])
    assert result["hit@5"] == 0.5
    assert result["hit@k"][10] == 1.0
    assert result["mrr@5"] == 0.5
    assert result["hit@5_strict"] == 0.0  # neither chunk contains all of lines 10-14
    assert result["gate"] == Gate(0.7, 1.0, 1.0)
    report = markdown_report(
        {"dense": result}, winner="dense", top_k=5, title="Dev", setup=["Setup line."]
    )
    assert "| dense **(winner)** | 0.500 | 0.500 |" in report
    assert "| dense | `q2` |" in report
