import pytest
from pydantic import ValidationError

from openusd_assistant.corpus import Manifest, SourceFile
from openusd_assistant.questions import Question, validate_question_sets

MANIFEST = Manifest(
    "v26.08", "a" * 40, "Example", (SourceFile("docs/intro.rst", "0" * 64, "Intro"),), ()
)


def make(id, kind="lookup", line=1, **extra):
    answerable = kind != "unanswerable"
    fields = dict(
        id=id,
        question=f"What does question {id} ask about USD?",
        kind=kind,
        answerable=answerable,
        sources=[{"path": "docs/intro.rst", "start_line": line, "end_line": line + 1}]
        if answerable
        else [],
        expected_facts=["A fact."] if answerable else [],
    )
    return Question.model_validate(fields | extra)


def balanced(prefix):
    line = 1 if prefix == "d" else 6  # dev and held-out cite different passages
    return [
        *(make(f"{prefix}-u{i}", "unanswerable") for i in range(5)),
        *(make(f"{prefix}-p{i}", "paraphrase", line) for i in range(3)),
        *(make(f"{prefix}-c{i}", "comparison", line) for i in range(2)),
    ]


@pytest.fixture
def source_dir(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/intro.rst").write_text(
        "Intro\n=====\n\n\nText.\nMore.\nEnd.\n", encoding="utf-8"
    )
    return tmp_path


def test_balanced_sets_pass(source_dir):
    result = validate_question_sets(
        {"dev": balanced("d"), "heldout": balanced("h")}, MANIFEST, source_dir
    )
    assert result["errors"] == []
    assert result["sets"]["dev"]["unanswerable"] == 5


@pytest.mark.parametrize(
    "fields",
    [
        {"kind": "unanswerable", "answerable": True},
        {"kind": "lookup", "answerable": False, "sources": [], "expected_facts": []},
        {"sources": []},
        {"sources": [{"path": "docs/intro.rst", "start_line": 3, "end_line": 2}]},
        {"surprise": 1},
    ],
)
def test_inconsistent_questions_are_rejected(fields):
    with pytest.raises(ValidationError):
        make("x", **fields)


def test_set_errors_name_the_problem(source_dir):
    dev = balanced("d") + [
        make("blank", sources=[{"path": "docs/intro.rst", "start_line": 3, "end_line": 4}]),
        make("past-end", sources=[{"path": "docs/intro.rst", "start_line": 5, "end_line": 9}]),
        make("unknown", sources=[{"path": "docs/other.rst", "start_line": 1, "end_line": 1}]),
    ]
    leaked = make("h-leak", question=dev[0].question.upper())
    heldout = [*balanced("h")[1:], make("d-u0", "unanswerable"), leaked]
    errors = validate_question_sets({"dev": dev, "heldout": heldout}, MANIFEST, source_dir)[
        "errors"
    ]
    assert "dev: blank cites only blank lines in docs/intro.rst" in errors
    assert "dev: past-end cites past the end of docs/intro.rst" in errors
    assert any("docs/other.rst" in error for error in errors)
    assert "heldout: duplicate id d-u0 (also in dev)" in errors
    assert "heldout: h-leak repeats a question from dev" in errors


def test_minimum_counts_apply_to_each_set(source_dir):
    errors = validate_question_sets(
        {"dev": balanced("d"), "heldout": [make("h1", line=6)]}, MANIFEST, source_dir
    )["errors"]
    assert errors == [
        "heldout: needs at least 5 unanswerable questions",
        "heldout: needs at least 5 paraphrase/comparison questions",
    ]


def test_overlapping_passages_across_sets_are_reported(source_dir):
    span = [{"path": "docs/intro.rst", "start_line": 2, "end_line": 5}]
    dev = balanced("d") + [make("dev-span", sources=span)]
    heldout = balanced("h") + [make("held-span", kind="paraphrase")]
    errors = validate_question_sets({"dev": dev, "heldout": heldout}, MANIFEST, source_dir)[
        "errors"
    ]
    # balanced() questions all cite lines 1-2, so every dev/held-out pair overlaps too.
    assert "dev: dev-span shares a passage with heldout: held-span" in errors
    apart = [make("far", sources=[{"path": "docs/intro.rst", "start_line": 5, "end_line": 5}])]
    only_dev_spans = {"dev": balanced("d") + apart, "heldout": [make("h-u", "unanswerable")]}
    assert not any(
        "shares a passage" in e
        for e in validate_question_sets(only_dev_spans, MANIFEST, source_dir)["errors"]
    )


def test_alternative_sources_may_overlap_across_sets(source_dir):
    alt = [
        {"path": "docs/intro.rst", "start_line": 6, "end_line": 7},
        {"path": "docs/intro.rst", "start_line": 1, "end_line": 2, "alternative": True},
    ]
    heldout = balanced("h") + [make("h-alt", sources=alt)]
    result = validate_question_sets(
        {"dev": balanced("d"), "heldout": heldout}, MANIFEST, source_dir
    )
    assert result["errors"] == []
    assert any(m.endswith("heldout: h-alt") for m in result["shared_alternative_passages"])
