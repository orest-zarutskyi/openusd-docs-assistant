import threading

import pytest

from openusd_assistant.models import Chunk
from openusd_assistant.retrieval import (
    Bm25Searcher,
    HybridSearcher,
    RerankSearcher,
    SearchResult,
    gated,
    reciprocal_rank_fusion,
)


def chunk(name: str, text: str = "") -> Chunk:
    return Chunk(
        id=name,
        path="docs/x.rst",
        title=name,
        start_line=1,
        end_line=1,
        text=text or name,
        url=f"https://example.invalid/{name}",
    )


A, B, C, D = (chunk(n) for n in "abcd")


class Fixed:
    def __init__(self, chunks, scores, confidence=None):
        self.result = SearchResult(chunks, scores, confidence)
        self.limits = []

    def search(self, question, limit):
        self.limits.append(limit)
        r = self.result
        return SearchResult(r.chunks[:limit], r.scores[:limit], r.confidence)


def test_rrf_sums_reciprocal_ranks():
    fused = reciprocal_rank_fusion([[A, B, C], [B, D]], k=60)
    scores = {c.id: s for c, s in fused}
    assert [c.id for c, _ in fused] == ["b", "a", "d", "c"]
    assert scores["b"] == pytest.approx(1 / 62 + 1 / 61)
    assert scores["a"] == pytest.approx(1 / 61)
    assert scores["d"] == pytest.approx(1 / 62)


def test_bm25_ranks_matching_text_first_and_is_thread_safe():
    chunks = [
        chunk("intro", "Stages compose layers."),
        chunk("payload", "A payload is a deferred reference that can be unloaded."),
        chunk("other", "Variants select alternatives."),
    ]
    searcher = Bm25Searcher(chunks)
    result = searcher.search("What is a deferred payload?", 2)
    assert [c.id for c in result.chunks] == ["payload"]
    assert result.confidence is None
    assert searcher.search("!!!", 5).chunks == []
    errors = []

    def run():
        try:
            searcher.search("payload", 3)
        except Exception as exc:  # pragma: no cover - would be a failure
            errors.append(exc)

    threads = [threading.Thread(target=run) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []


def test_hybrid_gate_uses_best_dense_cosine_among_returned_chunks():
    lexical = Fixed([A, B, C], [9.0, 5.0, 1.0])
    dense = Fixed([D, B, A], [0.80, 0.62, 0.40], 0.80)
    hybrid = HybridSearcher(lexical, dense, depth=3)
    result = hybrid.search("q", 2)
    # b is 2nd in both lists, a is 1st and 3rd: b and a fuse ahead of d.
    assert [c.id for c in result.chunks] == ["a", "b"]
    assert result.confidence == pytest.approx(0.62)  # d (0.80) is not among the two returned
    assert lexical.limits == dense.limits == [3]
    only_lexical = HybridSearcher(Fixed([A], [1.0]), Fixed([], [])).search("q", 3)
    assert only_lexical.confidence is None


def test_rerank_reorders_candidates_and_reports_the_top_score():
    base = Fixed([A, B, C], [3.0, 2.0, 1.0])
    seen = []

    def score(question, documents):
        seen.append(documents)
        return [0.1, -2.0, 4.5]

    result = RerankSearcher(base, score, depth=3).search("q", 2)
    assert [c.id for c in result.chunks] == ["c", "a"]
    assert result.scores == [4.5, 0.1]
    assert result.confidence == 4.5
    assert seen[0][0] == "a\na"  # title and text are both given to the cross-encoder
    assert RerankSearcher(Fixed([], []), score).search("q", 2).chunks == []


@pytest.mark.parametrize(
    ("confidence", "min_score", "expected"),
    [(0.7, 0.5, ["a"]), (0.4, 0.5, []), (None, 0.5, []), (None, None, ["a"])],
)
def test_gate_refuses_below_threshold_or_without_a_score(confidence, min_score, expected):
    retrieve = gated(Fixed([A], [1.0], confidence), top_k=3, min_score=min_score)
    assert [c.id for c in retrieve("q")] == expected


def test_build_retriever_applies_each_modes_own_gate():
    from openusd_assistant.retrieval import build_retriever

    chunks = [chunk("payload", "A payload is a deferred reference.")]
    dense = Fixed(chunks, [0.6], 0.6)
    loaded = []

    def scorer():
        loaded.append(True)
        return lambda question, documents: [2.0 for _ in documents]

    def make(mode, min_score=0.5, rerank_min_score=1.0):
        return build_retriever(
            mode,
            chunks=chunks,
            dense=dense,
            scorer=scorer,
            top_k=3,
            min_score=min_score,
            rerank_min_score=rerank_min_score,
        )

    question = "What is a payload?"
    assert make("dense")(question) == chunks
    assert make("dense", min_score=0.7)(question) == []
    assert make("bm25", min_score=0.99)(question) == chunks  # BM25 never refuses
    assert make("hybrid", min_score=0.7)(question) == []
    assert loaded == []  # the cross-encoder is loaded only for hybrid-rerank
    assert make("hybrid-rerank")(question) == chunks
    assert make("hybrid-rerank", rerank_min_score=3.0)(question) == []
    with pytest.raises(ValueError):
        make("sparse")
