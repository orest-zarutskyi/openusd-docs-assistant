import json
from types import SimpleNamespace

import pytest

from openusd_assistant.answer_eval import (
    ANSWER,
    ERROR,
    INVALID_CITATION,
    INVALID_OUTPUT,
    REFUSED_MODEL,
    REFUSED_RETRIEVAL,
    Price,
    answer_metrics,
    answer_question,
    load_records,
    save_records,
)
from openusd_assistant.chat import Usage, invalid_output
from openusd_assistant.judge import (
    Judge,
    Verdict,
    calibrate,
    cohen_kappa,
    judge_metrics,
    label_template,
)
from openusd_assistant.models import Chunk, DependencyUnavailable, DraftAnswer
from openusd_assistant.questions import Question

CHUNK = Chunk(
    id="c1",
    path="docs/intro.rst",
    title="Payloads",
    start_line=3,
    end_line=4,
    text="A payload is a deferred reference.",
    url="https://example.invalid/1",
)


def question(id="q", answerable=True, facts=("A payload defers loading.",)):
    return Question(
        id=id,
        question=f"What is asked in {id}?",
        kind="lookup" if answerable else "unanswerable",
        answerable=answerable,
        sources=[{"path": "docs/intro.rst", "start_line": 3, "end_line": 4}] if answerable else [],
        expected_facts=list(facts) if answerable else [],
    )


class Chat:
    def __init__(self, outcome):
        self.outcome = outcome

    def generate_with_usage(self, question, context):
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome, Usage(100, 20, 5)


def draft(quote="deferred reference", chunk_id="c1", status="answer"):
    evidence = [{"chunk_id": chunk_id, "quote": quote}] if status == "answer" else []
    return DraftAnswer(
        status=status, answer="Use a payload." if status == "answer" else "", evidence=evidence
    )


@pytest.mark.parametrize(
    ("context", "chat", "outcome"),
    [
        ([CHUNK], Chat(draft()), ANSWER),
        ([], Chat(draft()), REFUSED_RETRIEVAL),
        ([CHUNK], Chat(draft(status="insufficient_context")), REFUSED_MODEL),
        ([CHUNK], Chat(draft(quote="not in the excerpt")), INVALID_CITATION),
        ([CHUNK], Chat(draft(chunk_id="c9")), INVALID_CITATION),
        ([CHUNK], Chat(invalid_output(Usage(70, 3))), INVALID_OUTPUT),
        ([CHUNK], Chat(DependencyUnavailable()), ERROR),
    ],
)
def test_each_outcome_is_classified(context, chat, outcome):
    record = answer_question(question(), lambda q: context, chat, "m")
    assert record.outcome == outcome
    if outcome == INVALID_OUTPUT:
        assert record.usage["input_tokens"] == 70  # billed tokens survive a bad answer
    if outcome == REFUSED_RETRIEVAL:
        assert record.usage["input_tokens"] == 0 and record.context == []


def test_metrics_cost_and_round_trip(tmp_path):
    records = [
        answer_question(question("a1"), lambda q: [CHUNK], Chat(draft()), "m"),
        answer_question(question("a2"), lambda q: [CHUNK], Chat(draft(quote="x")), "m"),
        answer_question(question("a3"), lambda q: [], Chat(draft()), "m"),
        answer_question(question("u1", False), lambda q: [], Chat(draft()), "m"),
        answer_question(question("u2", False), lambda q: [CHUNK], Chat(draft()), "m"),
    ]
    path = tmp_path / "answers.jsonl"
    save_records(path, records)
    assert [r.outcome for r in load_records(path)] == [r.outcome for r in records]

    m = answer_metrics(records, Price(input_per_million=0.10, output_per_million=0.40))
    assert m["citation_validity"] == pytest.approx(2 / 3)  # a1 and u2 valid, a2 invalid
    assert m["correct_refusal"] == 0.5
    assert m["false_refusal"] == pytest.approx(1 / 3)
    assert m["answered_answerable"] == pytest.approx(1 / 3)
    assert m["tokens"] == {"input_tokens": 300, "output_tokens": 60, "thinking_tokens": 15}
    # 300 input tokens x $0.10 + 75 output tokens x $0.40 per million, over 5 questions.
    assert m["cost_per_100"] == pytest.approx((300 * 0.10 + 75 * 0.40) / 1e6 / 5 * 100)
    assert answer_metrics(records, Price())["cost_per_100"] == 0.0


def verdict(covered=(True,), claims=("supported",)):
    return Verdict.model_validate(
        {
            "facts": [{"fact": f"f{i}", "covered": c} for i, c in enumerate(covered)],
            "claims": [{"claim": f"c{i}", "verdict": v} for i, v in enumerate(claims)],
        }
    )


def test_judge_metrics():
    records = [
        answer_question(question("a1", facts=("x", "y")), lambda q: [CHUNK], Chat(draft()), "m"),
        answer_question(question("a2"), lambda q: [CHUNK], Chat(draft()), "m"),
        answer_question(question("a3"), lambda q: [], Chat(draft()), "m"),
    ]
    verdicts = {
        "a1": verdict((True, False), ("supported", "unsupported")),
        "a2": verdict((True,), ("supported",)),
    }
    m = judge_metrics(records, verdicts)
    assert m["judged"] == 2 and m["judge_failures"] == 0
    assert m["fact_coverage"] == pytest.approx((0.5 + 1.0) / 2)
    assert m["claims_supported"] == pytest.approx(2 / 3)
    assert m["fully_grounded"] == 0.5


class FakeJudgeModels:
    def __init__(self, text):
        self.text, self.calls = text, []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        usage = SimpleNamespace(
            prompt_token_count=900, candidates_token_count=80, thoughts_token_count=0
        )
        return SimpleNamespace(text=self.text, usage_metadata=usage)


def make_judge(text, tmp_path, judge_model="judge-m", compared=("other",)):
    prompt = tmp_path / "judge.md"
    prompt.write_text("Grade it.", encoding="utf-8")
    settings = SimpleNamespace(judge_model=judge_model)
    fake = FakeJudgeModels(text)
    judge = Judge(
        settings, compared_models=compared, client=SimpleNamespace(models=fake), prompt_path=prompt
    )
    return judge, fake


def test_judge_sends_context_and_rejects_misaligned_facts(tmp_path):
    record = answer_question(question(), lambda q: [CHUNK], Chat(draft()), "m")
    good = json.dumps({"facts": [{"fact": "f", "covered": True}], "claims": []})
    judge, fake = make_judge(good, tmp_path)
    result, usage = judge.grade(record, question())
    assert result.facts[0].covered and usage.input_tokens == 900
    payload = json.loads(fake.calls[0]["contents"])
    assert payload["excerpts"][0]["text"] == CHUNK.text
    assert payload["expected_facts"] == ["A payload defers loading."]
    assert fake.calls[0]["config"].system_instruction == "Grade it."
    misaligned, _ = make_judge(json.dumps({"facts": [], "claims": []}), tmp_path)
    assert misaligned.grade(record, question())[0] is None


def test_judge_cannot_be_a_compared_model(tmp_path):
    with pytest.raises(ValueError, match="must not be one of the compared"):
        make_judge("{}", tmp_path, judge_model="flash-lite", compared=("flash-lite",))


def test_label_template_balances_models_and_hides_order():
    qs = {f"q{i}": question(f"q{i}") for i in range(12)}
    records = [
        answer_question(q, lambda _: [CHUNK], Chat(draft()), model)
        for model in ("a", "b", "c")
        for q in qs.values()
    ]
    labels = label_template(records, qs, n=20)
    models = [label["record"]["model"] for label in labels]
    assert len(labels) == 20
    assert sorted(models.count(m) for m in "abc") == [6, 7, 7]
    assert labels[0]["human"] == {"facts_covered": [None], "fully_grounded": None, "notes": ""}
    assert labels[0]["excerpts"][0]["source"] == "docs/intro.rst#L3-L4"
    assert label_template(records, qs, n=20) == labels  # seeded, reproducible


def test_cohen_kappa_and_calibration():
    assert cohen_kappa([True, False, True, False], [True, False, True, False]) == pytest.approx(1.0)
    assert cohen_kappa([True, True, False, False], [True, False, True, False]) == pytest.approx(0.0)
    labels = [
        {
            "label_id": "L01",
            "record": {"id": "a", "model": "m"},
            "human": {"facts_covered": [True, False], "fully_grounded": True},
        },
        {
            "label_id": "L02",
            "record": {"id": "b", "model": "m"},
            "human": {"facts_covered": [True], "fully_grounded": False},
        },
    ]
    verdicts = {
        ("m", "a"): verdict((True, True), ("supported",)),
        ("m", "b"): verdict((True,), ("unsupported",)),
    }
    result = calibrate(labels, verdicts)
    assert result["facts"]["agreement"] == pytest.approx(2 / 3)
    assert result["fully_grounded"]["agreement"] == 1.0
    assert result["disagreements"] == ["L01: fact 2 human=False judge=True"]
    labels[0]["human"]["fully_grounded"] = None
    with pytest.raises(ValueError, match="L01 is not fully labelled"):
        calibrate(labels, verdicts)
