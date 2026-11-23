from pathlib import Path

import pytest

from openusd_assistant.adapters import Settings
from openusd_assistant.answer_eval import Price
from openusd_assistant.chat import GeminiChat
from openusd_assistant.eval_commands import chat_for, load_prices, parse_model, price_for, slug


def test_parse_model_keeps_colons_in_ollama_tags():
    assert parse_model("ollama:qwen3.5:4b") == ("ollama", "qwen3.5:4b")
    assert parse_model("gemini:gemini-x-flash-lite") == ("gemini", "gemini-x-flash-lite")
    for bad in ("qwen3:4b", "openai:gpt", "gemini:"):
        with pytest.raises(ValueError):
            parse_model(bad)
    assert slug("ollama:qwen3.5:4b") == "ollama_qwen3.5_4b"


def test_repository_pricing_file_loads_and_local_models_are_free():
    prices = load_prices(Path("eval/pricing.json"))
    assert all(p.input_per_million > 0 and p.output_per_million > 0 for p in prices.values())
    assert price_for("ollama:qwen3:4b", prices) == Price()
    with pytest.raises(ValueError, match="No price"):
        price_for("gemini:unpriced-model", prices)


def test_chat_for_overrides_only_the_model():
    settings = Settings(_env_file=None, gemini_api_key="k", chat_model="base")
    seen = []
    chat_for("ollama:qwen3.5:4b", settings, lambda s: seen.append(s.chat_model) or "ollama")
    assert seen == ["qwen3.5:4b"]
    gemini = chat_for("gemini:gemini-test", settings, None)
    assert isinstance(gemini, GeminiChat) and gemini.model == "gemini-test"
    assert settings.chat_model == "base"  # the shared settings are not mutated


def test_variants_parse_into_settings():
    from openusd_assistant.eval_commands import variant_settings

    assert parse_model("ollama:qwen3:4b@think") == ("ollama", "qwen3:4b")
    assert variant_settings("ollama:qwen3:4b@think") == {"ollama_reasoning": True}
    assert variant_settings("ollama:qwen3:4b@nothink") == {"ollama_reasoning": False}
    assert variant_settings("gemini:g@budget=0")["gemini_thinking_budget"] == 0
    assert variant_settings("gemini:g@level=low")["gemini_thinking_level"] == "low"
    assert variant_settings("gemini:g") == {}
    for bad in ("ollama:q@budget=1", "gemini:g@think", "gemini:g@budget=x"):
        with pytest.raises(ValueError):
            variant_settings(bad)
    seen = []
    chat_for("ollama:q:4b@think", Settings(_env_file=None), seen.append)
    assert seen[0].ollama_reasoning is True and seen[0].chat_model == "q:4b"


def test_choose_variants_prefers_score_then_latency():
    from openusd_assistant.answer_eval import choose_variants

    def m(answered, refused, p50):
        return {
            "answered_answerable": answered,
            "correct_refusal": refused,
            "latency_ms": {"p50": p50},
        }

    results = {
        "ollama:a@nothink": m(0.0, 1.0, 1000),
        "ollama:a@think": m(0.8, 1.0, 9000),
        "ollama:b@nothink": m(0.60, 1.0, 2000),
        "ollama:b@think": m(0.64, 1.0, 9000),  # +1 of 25 answerable: within tolerance
    }
    chosen = choose_variants(results, answerable=25)
    assert chosen == {"ollama:a": "ollama:a@think", "ollama:b": "ollama:b@nothink"}


def test_compare_variants_writes_a_report(tmp_path):
    from types import SimpleNamespace

    from openusd_assistant.answer_eval import AnswerRecord, save_records
    from openusd_assistant.eval_commands import compare_variants

    questions = tmp_path / "questions.jsonl"
    questions.write_text(
        '{"id":"a","question":"What is a payload in USD?","kind":"lookup","answerable":true,'
        '"sources":[{"path":"docs/x.rst","start_line":1,"end_line":1}],"expected_facts":["F."]}\n'
        '{"id":"u","question":"What does Pyro need here?","kind":"unanswerable","answerable":false}\n',
        encoding="utf-8",
    )
    answers = tmp_path / "answers"
    for spec, outcome, ms in (
        ("ollama:m@nothink", "refused_model", 100),
        ("ollama:m@think", "answer", 900),
    ):
        save_records(
            answers / f"{spec.replace(':', '_').replace('@', '_')}.jsonl",
            [
                AnswerRecord("a", "lookup", True, spec, outcome, latency_ms=ms),
                AnswerRecord("u", "unanswerable", False, spec, "refused_retrieval", latency_ms=ms),
            ],
        )
    report = tmp_path / "variants.md"
    args = SimpleNamespace(
        questions=questions, answers_dir=answers, pricing=Path("eval/pricing.json"), report=report
    )
    compare_variants(args)
    text = report.read_text(encoding="utf-8")
    assert "| `ollama:m@think` | 100% | 100% | 0% |" in text and text.count("| yes |") == 1


def test_judge_answers_keeps_verdicts_when_a_run_fails_midway(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from openusd_assistant import eval_commands
    from openusd_assistant.answer_eval import AnswerRecord, save_records
    from openusd_assistant.chat import Usage
    from openusd_assistant.judge import Judge
    from openusd_assistant.models import DependencyUnavailable

    questions = tmp_path / "questions.jsonl"
    questions.write_text(
        "".join(
            f'{{"id":"{i}","question":"What is a payload in USD?","kind":"lookup","answerable":true,'
            f'"sources":[{{"path":"docs/x.rst","start_line":1,"end_line":1}}],"expected_facts":["F."]}}\n'
            for i in ("a", "b")
        ),
        encoding="utf-8",
    )
    answers = tmp_path / "answers"
    for spec in ("ollama:m@think", "ollama:m@nothink"):
        save_records(
            answers / f"{spec.replace(':', '_').replace('@', '_')}.jsonl",
            [AnswerRecord(i, "lookup", True, spec, "answer", answer="A.") for i in ("a", "b")],
        )
    verdict = '{"facts":[{"fact":"F.","covered":true}],"claims":[]}'
    calls = []

    class FlakyBackend:
        def __init__(self, fail_after):
            self.fail_after = fail_after

        def complete(self, contents):
            calls.append(contents)
            if len(calls) > self.fail_after:
                raise DependencyUnavailable("quota")
            return verdict, Usage()

    settings = SimpleNamespace(judge_model="judge-x", judge_provider="gemini")
    args = SimpleNamespace(
        questions=questions,
        answers_dir=answers,
        pricing=Path("eval/pricing.json"),
        report=tmp_path / "answers.md",
        tier="free",
        models="ollama:m@think",
    )
    backend = FlakyBackend(fail_after=1)
    monkeypatch.setattr(eval_commands, "Judge", lambda s, **kw: Judge(s, backend=backend, **kw))
    with pytest.raises(DependencyUnavailable):
        eval_commands.judge_answers(args, settings)
    assert len((answers / "verdicts.jsonl").read_text(encoding="utf-8").splitlines()) == 1

    backend.fail_after = 10  # the quota is back: only the missing verdict is requested
    eval_commands.judge_answers(args, settings)
    rows = (answers / "verdicts.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(calls) == 3 and len(rows) == 2  # the other variant was never judged
    assert "ollama:m@nothink" not in args.report.read_text(encoding="utf-8")
