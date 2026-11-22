"""LLM-judge scoring of answers and its calibration against reference labels."""

import hashlib
import json
import random
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError

from .answer_eval import ANSWER, AnswerRecord, rate
from .chat import Usage, gemini_client
from .models import DependencyTimeout, DependencyUnavailable
from .questions import Question

PROMPT_PATH = Path("eval/prompts/judge.md")


class FactVerdict(BaseModel):
    fact: str
    covered: bool


class ClaimVerdict(BaseModel):
    claim: str
    verdict: Literal["supported", "unsupported", "contradicted"]


class Verdict(BaseModel):
    facts: list[FactVerdict]
    claims: list[ClaimVerdict]

    @property
    def fully_grounded(self) -> bool:
        return all(c.verdict == "supported" for c in self.claims)


class Judge:
    def __init__(
        self, settings, *, compared_models: Sequence[str], client=None, prompt_path=PROMPT_PATH
    ):
        from google.genai import types

        if not settings.judge_model:
            raise ValueError("Set OPENUSD_JUDGE_MODEL to the judge's model ID.")
        if settings.judge_model in compared_models:
            raise ValueError("The judge must not be one of the compared models.")
        self.model = settings.judge_model
        self.prompt = prompt_path.read_text(encoding="utf-8")
        self.prompt_sha256 = hashlib.sha256(self.prompt.encode()).hexdigest()[:12]
        self.client = client or gemini_client(settings, timeout=settings.judge_timeout)
        self.config = types.GenerateContentConfig(
            system_instruction=self.prompt,
            temperature=0,
            response_mime_type="application/json",
            response_json_schema=Verdict.model_json_schema(),
        )

    def grade(self, record: AnswerRecord, question: Question) -> tuple[Verdict | None, Usage]:
        from google.genai import errors

        payload = {
            "question": question.question,
            "answer": record.answer,
            "excerpts": [{"chunk_id": c["chunk_id"], "text": c["text"]} for c in record.context],
            "expected_facts": question.expected_facts,
        }
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=json.dumps(payload, ensure_ascii=False),
                config=self.config,
            )
        except (errors.APIError, ConnectionError) as exc:
            raise DependencyUnavailable("The judge model is unavailable.") from exc
        except TimeoutError as exc:
            raise DependencyTimeout("The judge model timed out.") from exc
        meta = response.usage_metadata
        usage = Usage(
            (meta.prompt_token_count or 0) if meta else 0,
            (meta.candidates_token_count or 0) if meta else 0,
            (meta.thoughts_token_count or 0) if meta else 0,
        )
        try:
            verdict = Verdict.model_validate_json(response.text or "")
        except ValidationError:
            return None, usage
        if len(verdict.facts) != len(question.expected_facts):
            return None, usage  # misaligned facts cannot be scored
        return verdict, usage


def judge_metrics(records: Sequence[AnswerRecord], verdicts: dict[str, Verdict | None]) -> dict:
    """Fact coverage over answered answerable questions; groundedness over all answers."""
    answered = [r for r in records if r.outcome == ANSWER]
    graded = [(r, verdicts.get(r.id)) for r in answered]
    valid = [(r, v) for r, v in graded if v is not None]
    with_facts = [(r, v) for r, v in valid if r.answerable and v.facts]
    claims = [c for _, v in valid for c in v.claims]
    return {
        "judged": len(valid),
        "judge_failures": len(graded) - len(valid),
        # Mean per answer of the share of its expected facts the judge found.
        "fact_coverage": (
            sum(sum(f.covered for f in v.facts) / len(v.facts) for _, v in with_facts)
            / len(with_facts)
            if with_facts
            else None
        ),
        "claims_supported": rate(sum(c.verdict == "supported" for c in claims), len(claims)),
        "claims_contradicted": rate(sum(c.verdict == "contradicted" for c in claims), len(claims)),
        "fully_grounded": rate(sum(v.fully_grounded for _, v in valid), len(valid)),
    }


def label_template(
    records: Sequence[AnswerRecord], questions: dict[str, Question], n: int = 20, seed: int = 2608
) -> list[dict]:
    """Sample answered records evenly across models for blind reference labelling."""
    answered = [r for r in records if r.outcome == ANSWER and r.answerable]
    by_model: dict[str, list[AnswerRecord]] = {}
    for r in answered:
        by_model.setdefault(r.model, []).append(r)
    rng = random.Random(seed)
    for group in by_model.values():
        rng.shuffle(group)
    picked, models = [], sorted(by_model)
    while len(picked) < n and any(by_model.values()):
        for model in models:
            if by_model[model] and len(picked) < n:
                picked.append(by_model[model].pop())
    rng.shuffle(picked)  # hide the per-model order from the labeller
    return [
        {
            "label_id": f"L{i:02d}",
            "record": {"id": r.id, "model": r.model},
            "question": questions[r.id].question,
            "answer": r.answer,
            "excerpts": [
                {"source": f"{c['path']}#L{c['lines'][0]}-L{c['lines'][1]}", "text": c["text"]}
                for c in r.context
            ],
            "expected_facts": questions[r.id].expected_facts,
            "reference": {
                "facts_covered": [None] * len(questions[r.id].expected_facts),
                "fully_grounded": None,
                "notes": "",
            },
        }
        for i, r in enumerate(picked, 1)
    ]


def cohen_kappa(a: Sequence[bool], b: Sequence[bool]) -> float | None:
    if not a:
        return None
    observed = sum(x == y for x, y in zip(a, b, strict=True)) / len(a)
    pa, pb = sum(a) / len(a), sum(b) / len(b)
    expected = pa * pb + (1 - pa) * (1 - pb)
    return None if expected == 1 else (observed - expected) / (1 - expected)


def calibrate(labels: Sequence[dict], verdicts: dict[tuple[str, str], Verdict | None]) -> dict:
    """Agreement between reference labels and the judge on fact coverage and full groundedness."""
    reference_facts, judge_facts, reference_grounded, judge_grounded, disagreements = (
        [],
        [],
        [],
        [],
        [],
    )
    for label in labels:
        reference = label["reference"]
        if reference["fully_grounded"] is None or None in reference["facts_covered"]:
            raise ValueError(f"{label['label_id']} is not fully labelled")
        key = (label["record"]["model"], label["record"]["id"])
        verdict = verdicts.get(key)
        if verdict is None:
            disagreements.append(f"{label['label_id']}: judge produced no verdict")
            continue
        reference_facts += reference["facts_covered"]
        judge_facts += [f.covered for f in verdict.facts]
        reference_grounded.append(reference["fully_grounded"])
        judge_grounded.append(verdict.fully_grounded)
        if reference["fully_grounded"] != verdict.fully_grounded:
            disagreements.append(
                f"{label['label_id']}: grounded reference={reference['fully_grounded']} judge={verdict.fully_grounded}"
            )
        for i, (h, j) in enumerate(zip(reference["facts_covered"], verdict.facts, strict=True)):
            if h != j.covered:
                disagreements.append(
                    f"{label['label_id']}: fact {i + 1} reference={h} judge={j.covered}"
                )

    def agreement(a, b):
        return rate(sum(x == y for x, y in zip(a, b, strict=True)), len(a))

    return {
        "labels": len(labels),
        "facts": {
            "n": len(reference_facts),
            "agreement": agreement(reference_facts, judge_facts),
            "kappa": cohen_kappa(reference_facts, judge_facts),
        },
        "fully_grounded": {
            "n": len(reference_grounded),
            "agreement": agreement(reference_grounded, judge_grounded),
            "kappa": cohen_kappa(reference_grounded, judge_grounded),
        },
        "disagreements": disagreements,
    }
