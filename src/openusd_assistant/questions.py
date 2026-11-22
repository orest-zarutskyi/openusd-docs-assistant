"""Evaluation question schema and checks against the pinned corpus snapshot."""

import json
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .corpus import Manifest

Kind = Literal["lookup", "paraphrase", "comparison", "unanswerable"]
MIN_UNANSWERABLE = 5
MIN_REWORDED = 5  # paraphrase + comparison


class SourceSpan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    # Another passage that also answers the question (the corpus repeats itself).
    # Retrieval may hit it; it is exempt from the dev/held-out shared-passage rule.
    alternative: bool = False

    @model_validator(mode="after")
    def ordered(self) -> "SourceSpan":
        if self.end_line < self.start_line:
            raise ValueError("end_line must not precede start_line")
        return self


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    question: str = Field(min_length=10)
    kind: Kind
    answerable: bool
    sources: list[SourceSpan] = Field(default_factory=list)
    expected_facts: list[str] = Field(default_factory=list)
    # Why the author is unsure of the expected sources; reviewed by a person.
    uncertain: str | None = None

    @model_validator(mode="after")
    def consistent(self) -> "Question":
        if self.answerable != (self.kind != "unanswerable"):
            raise ValueError("Only unanswerable questions may have answerable=false")
        if self.answerable and not (self.sources and self.expected_facts):
            raise ValueError("Answerable questions need sources and expected facts")
        if not self.answerable and (self.sources or self.expected_facts):
            raise ValueError("Unanswerable questions must not list sources or facts")
        return self


def load_questions(path: Path) -> list[Question]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [Question.model_validate_json(line) for line in lines if line.strip()]


def validate_question_sets(
    sets: dict[str, list[Question]], manifest: Manifest, source_dir: Path
) -> dict:
    """Check ids, overlap between sets, minimum counts and that every span has text."""
    errors = []
    documents = {file.path for file in manifest.documents}
    line_cache: dict[str, list[str]] = {}
    seen_ids: dict[str, str] = {}
    seen_text: dict[str, str] = {}
    summary = {}
    for name, questions in sets.items():
        for q in questions:
            if q.id in seen_ids:
                errors.append(f"{name}: duplicate id {q.id} (also in {seen_ids[q.id]})")
            seen_ids.setdefault(q.id, name)
            text = " ".join(q.question.lower().split())
            if text in seen_text:
                errors.append(f"{name}: {q.id} repeats a question from {seen_text[text]}")
            seen_text.setdefault(text, name)
            for span in q.sources:
                if span.path not in documents:
                    errors.append(f"{name}: {q.id} cites {span.path}, which is not in the manifest")
                    continue
                if span.path not in line_cache:
                    content = source_dir.joinpath(span.path).read_text(encoding="utf-8")
                    line_cache[span.path] = content.splitlines()
                lines = line_cache[span.path]
                if span.end_line > len(lines):
                    errors.append(f"{name}: {q.id} cites past the end of {span.path}")
                elif not any(lines[i].strip() for i in range(span.start_line - 1, span.end_line)):
                    errors.append(f"{name}: {q.id} cites only blank lines in {span.path}")
        kinds = Counter(q.kind for q in questions)
        reworded = kinds["paraphrase"] + kinds["comparison"]
        if kinds["unanswerable"] < MIN_UNANSWERABLE:
            errors.append(f"{name}: needs at least {MIN_UNANSWERABLE} unanswerable questions")
        if reworded < MIN_REWORDED:
            errors.append(f"{name}: needs at least {MIN_REWORDED} paraphrase/comparison questions")
        summary[name] = {
            "questions": len(questions),
            **{
                kind: kinds[kind] for kind in ("lookup", "paraphrase", "comparison", "unanswerable")
            },
            "uncertain": sum(q.uncertain is not None for q in questions),
        }
    shared = _shared_passages(sets)
    errors.extend(message for message, primary in shared if primary)
    return {
        "sets": summary,
        "errors": errors,
        # Overlaps involving an alternative source: corpus repetition, not twin questions.
        "shared_alternative_passages": [message for message, primary in shared if not primary],
    }


def _shared_passages(sets: dict[str, list[Question]]) -> list[tuple[str, bool]]:
    """Source spans that overlap across sets, flagged True when both spans are primary.

    Two primary spans mean near-twin questions, so tuning on one set would see the other.
    """
    spans = [
        (name, q.id, span)
        for name, questions in sets.items()
        for q in questions
        for span in q.sources
    ]
    errors = []
    for i, (name, qid, span) in enumerate(spans):
        for other_name, other_id, other in spans[i + 1 :]:
            if other_name != name and other.path == span.path:
                if span.start_line <= other.end_line and other.start_line <= span.end_line:
                    message = f"{name}: {qid} shares a passage with {other_name}: {other_id}"
                    errors.append((message, not (span.alternative or other.alternative)))
    return errors


def dump_questions(questions: list[Question]) -> str:
    return "".join(
        json.dumps(q.model_dump(exclude_none=True), ensure_ascii=False) + "\n" for q in questions
    )
