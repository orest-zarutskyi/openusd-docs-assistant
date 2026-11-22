"""Lexical, dense, hybrid (RRF) and reranked retrieval behind one interface."""

import re
import sqlite3
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

from .models import Chunk

Mode = Literal["bm25", "dense", "hybrid", "hybrid-rerank"]
MODES: tuple[Mode, ...] = ("bm25", "dense", "hybrid", "hybrid-rerank")


@dataclass(frozen=True)
class SearchResult:
    """Ranked chunks plus the score used to decide whether to refuse.

    ``confidence`` is on the scale of the mode's own gate (cosine similarity for dense
    and hybrid, cross-encoder score for reranking) and is ``None`` when the mode has no
    calibrated score, as with BM25.
    """

    chunks: list[Chunk]
    scores: list[float]
    confidence: float | None


class Searcher(Protocol):
    def search(self, question: str, limit: int) -> SearchResult: ...


class Bm25Searcher:
    """SQLite FTS5 BM25 over chunk titles and text, kept in memory."""

    def __init__(self, chunks: Sequence[Chunk]) -> None:
        self.chunks = list(chunks)
        self._lock = threading.Lock()  # FastAPI runs sync handlers on worker threads
        self._db = sqlite3.connect(":memory:", check_same_thread=False)
        self._db.execute("CREATE VIRTUAL TABLE chunks USING fts5(title, text)")
        self._db.executemany(
            "INSERT INTO chunks(rowid, title, text) VALUES(?, ?, ?)",
            ((i, chunk.title, chunk.text) for i, chunk in enumerate(self.chunks, 1)),
        )

    def search(self, question: str, limit: int) -> SearchResult:
        terms = dict.fromkeys(re.findall(r"[^\W_]+", question.lower()))
        if not terms:
            return SearchResult([], [], None)
        match = " OR ".join(f'"{term}"' for term in terms)
        with self._lock:
            rows = self._db.execute(
                "SELECT rowid, bm25(chunks) FROM chunks WHERE chunks MATCH ? "
                "ORDER BY bm25(chunks), rowid LIMIT ?",
                (match, limit),
            ).fetchall()
        # SQLite's bm25() is lower-is-better; negate it so every searcher ranks descending.
        return SearchResult(
            [self.chunks[rowid - 1] for rowid, _ in rows], [-score for _, score in rows], None
        )


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[Chunk]], k: int = 60
) -> list[tuple[Chunk, float]]:
    """Fuse rankings by summing 1 / (k + rank); ties keep first-seen order."""
    scores: dict[str, float] = {}
    chunks: dict[str, Chunk] = {}
    for ranking in rankings:
        for rank, chunk in enumerate(ranking, 1):
            chunks.setdefault(chunk.id, chunk)
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (k + rank)
    order = sorted(scores, key=lambda chunk_id: -scores[chunk_id])
    return [(chunks[chunk_id], scores[chunk_id]) for chunk_id in order]


class HybridSearcher:
    """Fuse BM25 and dense rankings with RRF.

    RRF uses ranks only, so BM25 scores and cosine similarities never need a shared
    scale. The refusal gate uses the best dense cosine among the fused candidates,
    because an RRF score says nothing about absolute relevance.
    """

    def __init__(self, lexical: Searcher, dense: Searcher, *, depth: int = 50, rrf_k: int = 60):
        self.lexical, self.dense, self.depth, self.rrf_k = lexical, dense, depth, rrf_k

    def search(self, question: str, limit: int) -> SearchResult:
        lexical = self.lexical.search(question, self.depth)
        dense = self.dense.search(question, self.depth)
        fused = reciprocal_rank_fusion([lexical.chunks, dense.chunks], self.rrf_k)[:limit]
        cosine = dict(zip((c.id for c in dense.chunks), dense.scores, strict=True))
        kept = [cosine[chunk.id] for chunk, _ in fused if chunk.id in cosine]
        return SearchResult(
            [chunk for chunk, _ in fused], [score for _, score in fused], max(kept, default=None)
        )


Scorer = Callable[[str, list[str]], list[float]]


class RerankSearcher:
    """Rescore the first ``depth`` candidates of another searcher with a cross-encoder."""

    def __init__(self, base: Searcher, score: Scorer, *, depth: int = 20) -> None:
        self.base, self.score, self.depth = base, score, depth

    def search(self, question: str, limit: int) -> SearchResult:
        candidates = self.base.search(question, self.depth).chunks
        if not candidates:
            return SearchResult([], [], None)
        scores = self.score(question, [f"{c.title}\n{c.text}" for c in candidates])
        ranked = sorted(zip(candidates, scores, strict=True), key=lambda pair: -pair[1])[:limit]
        return SearchResult(
            [chunk for chunk, _ in ranked], [score for _, score in ranked], ranked[0][1]
        )


def fastembed_scorer(model_name: str, cache_dir: str | None = None) -> Scorer:
    from fastembed.rerank.cross_encoder import TextCrossEncoder

    encoder = TextCrossEncoder(model_name=model_name, cache_dir=cache_dir)

    def score(question: str, documents: list[str]) -> list[float]:
        return [float(value) for value in encoder.rerank(question, documents)]

    return score


def gated(searcher: Searcher, top_k: int, min_score: float | None) -> Callable[[str], list[Chunk]]:
    """Return the graph's retriever: top_k chunks, or none when confidence is too low."""

    def retrieve(question: str) -> list[Chunk]:
        result = searcher.search(question, top_k)
        if min_score is not None and (result.confidence is None or result.confidence < min_score):
            return []
        return result.chunks

    return retrieve
