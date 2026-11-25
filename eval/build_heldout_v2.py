"""Build eval/heldout_v2.jsonl from eval/heldout_v2_source.csv and apply the review (2026-11-25).

The CSV lists 60 new questions with expected facts and GitHub links to the pinned sources.
Every answerable question was checked against its cited lines and every unanswerable one
against the whole corpus by an LLM reviewer; the fixes below are the confirmed findings.
Run once from the project root: python eval/build_heldout_v2.py
"""

import csv
import re
from pathlib import Path

from openusd_assistant.questions import Question, SourceSpan, dump_questions

SOURCE = Path("eval/heldout_v2_source.csv")
OUT = Path("eval/heldout_v2.jsonl")
LINK = re.compile(r"/docs/(?P<path>[^?#\s]+\.rst)(?:\?plain=1)?#L(?P<a>\d+)(?:-L(?P<b>\d+))?")


def span(path: str, start: int, end: int, alternative: bool = False) -> SourceSpan:
    return SourceSpan(path=f"docs/{path}", start_line=start, end_line=end, alternative=alternative)


def convert(rows: list[dict]) -> list[Question]:
    questions = []
    for i, row in enumerate(rows, 1):
        kind = row["type"].strip()
        answerable = kind != "unanswerable"
        spans = [
            span(m["path"], int(m["a"]), int(m["b"] or m["a"])) for m in LINK.finditer(row["where"])
        ]
        facts = [row[k].strip() for k in ("fact1", "fact2", "fact3") if row[k].strip()]
        questions.append(
            Question(
                id=f"v2-{i:02d}",
                question=row["question"].strip(),
                kind=kind,
                answerable=answerable,
                sources=spans if answerable else [],
                expected_facts=facts if answerable else [],
                uncertain=row["unsure"].strip() or None,
            )
        )
    return questions


# Review findings: corrected facts, kinds and source spans.
FIXES = {
    # The answer is "none"; say so instead of only implying it.
    "v2-39": {
        "add_fact": "B needs no reciprocal relationship; the relationship from B to A is implicit."
    },
    # The rule is current behaviour in the render guide; the white paper only proposed it.
    "v2-53": {
        "sources": [
            span("user_guides/render_user_guide.rst", 889, 893),
            span("wp_usdshade.rst", 123, 128, alternative=True),
        ],
        "facts": [
            "The binding authored first in the prim's property order is the strongest and wins."
        ],
    },
    # The source describes layer metadata, not stage times.
    "v2-17": {
        "replace_fact": (
            1,
            "startTimeCode and endTimeCode only set the initial playback range that clients "
            "show; they do not limit value resolution.",
        )
    },
    # Situations that apply a rule rather than direct lookups.
    "v2-22": {"kind": "paraphrase"},
    "v2-23": {"kind": "paraphrase"},
    # The reason for preferring property namespaces is in the parent bullet.
    "v2-18": {"add_source": span("maxperf.rst", 183, 192)},
    # Only the usda example shows elementSize as metadata.
    "v2-30": {"sources": [span("user_guides/primvars.rst", 574, 599)]},
    "v2-42": {"sources": [span("user_guides/color_user_guide.rst", 51, 58)]},
    "v2-43": {"sources": [span("toolset.rst", 222, 236)]},
    "v2-57": {"sources": [span("spec_usdpreviewsurface.rst", 727, 734)]},
    # An 89-line span would count almost any nearby chunk as a hit.
    "v2-46": {
        "sources": [
            span("tut_simple_shading.rst", 113, 115),
            span("tut_simple_shading.rst", 184, 187),
        ]
    },
    "v2-16": {"add_source": span("spec_usdz.rst", 124, 127, alternative=True)},
    "v2-26": {
        "sources": [
            span("user_guides/color_user_guide.rst", 177, 196),
            span("user_guides/color_user_guide.rst", 230, 235),
        ]
    },
}


def apply(questions: list[Question]) -> list[Question]:
    out = []
    for q in questions:
        fix = FIXES.get(q.id)
        if not fix:
            out.append(q)
            continue
        data = q.model_dump()
        if "kind" in fix:
            data["kind"] = fix["kind"]
        if "sources" in fix:
            data["sources"] = [s.model_dump() for s in fix["sources"]]
        if "add_source" in fix:
            data["sources"].append(fix["add_source"].model_dump())
        if "facts" in fix:
            data["expected_facts"] = fix["facts"]
        if "add_fact" in fix:
            data["expected_facts"].append(fix["add_fact"])
        if "replace_fact" in fix:
            index, text = fix["replace_fact"]
            data["expected_facts"][index] = text
        out.append(Question.model_validate(data))
    missing = set(FIXES) - {q.id for q in questions}
    if missing:
        raise ValueError(f"Fixes for unknown ids: {sorted(missing)}")
    return out


if __name__ == "__main__":
    rows = list(csv.DictReader(SOURCE.open(encoding="utf-8-sig", newline="")))
    questions = apply(convert(rows))
    OUT.write_text(dump_questions(questions), encoding="utf-8", newline="\n")
    print(f"Wrote {len(questions)} questions to {OUT}")
