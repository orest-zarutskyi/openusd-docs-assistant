"""LLM-judge scoring of answers and its calibration against reference labels."""

import hashlib
import json
import random
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

import httpx
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


class GeminiBackend:
    """The judge on the Gemini API (google-genai)."""

    def __init__(self, client, model: str, system: str):
        from google.genai import types

        self.client, self.model = client, model
        self.config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=0,
            response_mime_type="application/json",
            response_json_schema=Verdict.model_json_schema(),
        )

    def complete(self, contents: str) -> tuple[str, Usage]:
        from google.genai import errors

        try:
            response = self.client.models.generate_content(
                model=self.model, contents=contents, config=self.config
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
        return response.text or "", usage


class OpenAICompatibleBackend:
    """The judge on any OpenAI-compatible /chat/completions endpoint (e.g. a gateway).

    The schema goes into the system message and the response is requested as a JSON
    object, since gateways differ in support for strict json_schema output.
    """

    RETRY_STATUS = {429, 500, 502, 503, 504}

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        system: str,
        *,
        timeout: float = 180,
        attempts: int = 4,
        transport: httpx.BaseTransport | None = None,
        sleep=time.sleep,
    ):
        schema = json.dumps(Verdict.model_json_schema(), ensure_ascii=False)
        self.system = f"{system}\n\nResponse JSON schema:\n{schema}"
        self.model, self.attempts, self.sleep = model, attempts, sleep
        self.http = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
            transport=transport,
        )

    def complete(self, contents: str) -> tuple[str, Usage]:
        body = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": self.system},
                {"role": "user", "content": contents},
            ],
        }
        for attempt in range(self.attempts):
            try:
                response = self.http.post("/chat/completions", json=body)
            except httpx.TimeoutException as exc:
                raise DependencyTimeout("The judge model timed out.") from exc
            except httpx.HTTPError as exc:
                raise DependencyUnavailable("The judge model is unavailable.") from exc
            if response.status_code in self.RETRY_STATUS and attempt + 1 < self.attempts:
                self.sleep(min(60, 2 * 2**attempt))
                continue
            if response.status_code >= 400:
                raise DependencyUnavailable(f"The judge endpoint returned {response.status_code}.")
            data = response.json()
            usage = data.get("usage") or {}
            reasoning = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
            text = data["choices"][0]["message"].get("content") or ""
            return _strip_fence(text), Usage(
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0) - reasoning,
                reasoning,
            )
        raise DependencyUnavailable("The judge endpoint kept failing.")


def _strip_fence(text: str) -> str:
    """Some gateways wrap JSON in a Markdown code fence despite json_object mode."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    return text.strip()


class Judge:
    def __init__(
        self,
        settings,
        *,
        compared_models: Sequence[str],
        client=None,
        prompt_path=PROMPT_PATH,
        backend=None,
    ):
        if not settings.judge_model:
            raise ValueError("Set OPENUSD_JUDGE_MODEL to the judge's model ID.")
        if settings.judge_model in compared_models:
            raise ValueError("The judge must not be one of the compared models.")
        self.model = settings.judge_model
        self.prompt = prompt_path.read_text(encoding="utf-8")
        self.prompt_sha256 = hashlib.sha256(self.prompt.encode()).hexdigest()[:12]
        self.provider = getattr(settings, "judge_provider", "gemini")
        if backend is None and self.provider == "openai-compatible":
            if not settings.judge_base_url or settings.judge_api_key is None:
                raise ValueError("Set OPENUSD_JUDGE_BASE_URL and OPENUSD_JUDGE_API_KEY in .env.")
            backend = OpenAICompatibleBackend(
                settings.judge_base_url,
                settings.judge_api_key.get_secret_value(),
                self.model,
                self.prompt,
                timeout=settings.judge_timeout,
            )
        if backend is None:
            client = client or gemini_client(settings, timeout=settings.judge_timeout)
            backend = GeminiBackend(client, self.model, self.prompt)
        self.backend = backend

    def grade(self, record: AnswerRecord, question: Question) -> tuple[Verdict | None, Usage]:
        payload = {
            "question": question.question,
            "answer": record.answer,
            "excerpts": [{"chunk_id": c["chunk_id"], "text": c["text"]} for c in record.context],
            "expected_facts": question.expected_facts,
        }
        text, usage = self.backend.complete(json.dumps(payload, ensure_ascii=False))
        try:
            verdict = Verdict.model_validate_json(text)
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
