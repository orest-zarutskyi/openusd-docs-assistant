"""Build eval/heldout_v4.jsonl from the selected rows of eval/heldout_v4_candidates.csv.

The candidates are real questions from public forums (forum.aousd.org, OpenUSD GitHub issues,
the SideFX forum, the NVIDIA developer forum and Stack Overflow; the URL of each post is in the
CSV). They were collected without looking at the documentation, and none repeats a v3 candidate.
Each one was then checked against the 76-file corpus by reading the RST files directly, not
through this project's retrieval. An LLM wrote the questions' English wording, expected facts and
source spans. "partly" rows were narrowed to the part the documentation answers, and the original
wording is kept next to them. The author approved the selection: every suggested answerable or
partly row that shares no primary passage with the 175 dev questions (13 were dropped, see
why_not), plus 18 suggested unanswerable rows taken round-robin across sites in cid order.
Run from the project root: python eval/build_heldout_v4.py
"""

import csv
import re
from pathlib import Path

from openusd_assistant.questions import Question, SourceSpan, dump_questions

SOURCE = Path("eval/heldout_v4_candidates.csv")
OUT = Path("eval/heldout_v4.jsonl")
SPAN = re.compile(r"(?P<path>docs/[^#\s|]+\.rst)#L(?P<a>\d+)-L(?P<b>\d+)")


def build(rows: list[dict]) -> list[Question]:
    questions = []
    for row in rows:
        if row["selected"] != "yes":
            continue
        answerable = row["kind"] != "unanswerable"
        spans = [
            SourceSpan(path=m["path"], start_line=int(m["a"]), end_line=int(m["b"]))
            for m in SPAN.finditer(row["sources"])
        ]
        facts = [row[k].strip() for k in ("fact1", "fact2", "fact3") if row[k].strip()]
        questions.append(
            Question(
                id=f"v4-{row['cid']}",
                question=row["question"].strip(),
                kind=row["kind"],
                answerable=answerable,
                sources=spans if answerable else [],
                expected_facts=facts if answerable else [],
            )
        )
    return questions


if __name__ == "__main__":
    rows = list(csv.DictReader(SOURCE.open(encoding="utf-8-sig", newline="")))
    questions = build(rows)
    OUT.write_text(dump_questions(questions), encoding="utf-8", newline="\n")
    print(f"Wrote {len(questions)} questions to {OUT}")
