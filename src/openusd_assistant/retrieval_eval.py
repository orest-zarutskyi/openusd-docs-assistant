"""Compute retrieval metrics against source lines, without scoring model answers."""

import json
import re
import sqlite3
from collections.abc import Callable
from contextlib import closing
from pathlib import Path

from .models import Chunk


def evaluate_retrieval(
    questions_path: Path, retrieve: Callable[[str], list[Chunk]], top_k: int
) -> dict:
    questions = [
        json.loads(line)
        for line in questions_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    cases = []
    for case in questions:
        if not case["answerable"]:
            continue
        ranked = retrieve(case["question"])[:top_k]
        ranks = [
            next(
                (
                    rank
                    for rank, chunk in enumerate(ranked, 1)
                    if chunk.path == source["path"]
                    and chunk.start_line <= source["start_line"]
                    and chunk.end_line >= source["end_line"]
                ),
                None,
            )
            for source in case["sources"]
        ]
        hits = [rank for rank in ranks if rank is not None]
        cases.append(
            {
                "id": case["id"],
                "first_rank": min(hits, default=None),
                "source_recall": len(hits) / len(ranks),
            }
        )
    if not cases:
        raise ValueError("The evaluation needs at least one answerable question.")
    return {
        "k": top_k,
        "answerable": len(cases),
        "skipped_unanswerable": len(questions) - len(cases),
        "hit_rate": sum(case["first_rank"] is not None for case in cases) / len(cases),
        "recall": sum(case["source_recall"] for case in cases) / len(cases),
        "mrr": sum(1 / case["first_rank"] for case in cases if case["first_rank"]) / len(cases),
        "cases": cases,
    }


def evaluate_bm25(questions_path: Path, chunks: list[Chunk], top_k: int) -> dict:
    with closing(sqlite3.connect(":memory:")) as db:
        db.execute("CREATE VIRTUAL TABLE chunks USING fts5(title, text)")
        db.executemany(
            "INSERT INTO chunks(rowid, title, text) VALUES(?, ?, ?)",
            ((index, chunk.title, chunk.text) for index, chunk in enumerate(chunks, 1)),
        )

        def search(question: str) -> list[Chunk]:
            terms = dict.fromkeys(re.findall(r"[^\W_]+", question.lower()))
            match = " OR ".join(f'"{term}"' for term in terms)
            if not match:
                return []
            result = db.execute(
                "SELECT rowid FROM chunks WHERE chunks MATCH ? "
                "ORDER BY bm25(chunks), rowid LIMIT ?",
                (match, top_k),
            )
            return [chunks[rowid - 1] for (rowid,) in result]

        return evaluate_retrieval(questions_path, search, top_k)
