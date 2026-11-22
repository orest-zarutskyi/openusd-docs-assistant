import json
from types import SimpleNamespace

import pytest
from google.genai import errors

from openusd_assistant.adapters import OllamaModels, Settings
from openusd_assistant.chat import GeminiChat, Usage, make_chat
from openusd_assistant.models import Chunk, DependencyUnavailable, InvalidModelOutput

CHUNK = Chunk(
    id="c1",
    path="docs/intro.rst",
    title="Payloads",
    start_line=1,
    end_line=2,
    text="A payload is a deferred reference.",
    url="https://example.invalid/1",
)
ANSWER = {
    "status": "answer",
    "answer": "Use a payload.",
    "evidence": [{"chunk_id": "c1", "quote": "deferred reference"}],
}


class FakeModels:
    def __init__(self, text, error=None):
        self.text, self.error, self.calls = text, error, []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        usage = SimpleNamespace(
            prompt_token_count=120, candidates_token_count=30, thoughts_token_count=7
        )
        return SimpleNamespace(text=self.text, usage_metadata=usage)


def gemini(text, error=None, **settings):
    fake = FakeModels(text, error)
    config = Settings(
        _env_file=None, chat_provider="gemini", gemini_model="gemini-test", **settings
    )
    return GeminiChat(config, client=SimpleNamespace(models=fake)), fake


def test_gemini_returns_structured_answer_and_usage():
    chat, fake = gemini(json.dumps(ANSWER))
    draft, usage = chat.generate_with_usage("What defers loading?", [CHUNK])
    assert draft.evidence[0].quote == "deferred reference"
    assert usage == Usage(input_tokens=120, output_tokens=30, thinking_tokens=7)
    call = fake.calls[0]
    assert call["model"] == "gemini-test"
    assert json.loads(call["contents"])["excerpts"][0]["chunk_id"] == "c1"
    assert call["config"].temperature == 0
    assert call["config"].response_mime_type == "application/json"
    assert call["config"].thinking_config is None
    assert call["config"].response_json_schema["required"] == ["status", "answer", "evidence"]


def test_gemini_thinking_settings_are_passed_through():
    chat, fake = gemini(json.dumps(ANSWER), gemini_thinking_budget=0)
    chat.generate("q?", [CHUNK])
    assert fake.calls[0]["config"].thinking_config.thinking_budget == 0


def test_invalid_gemini_json_keeps_the_billed_usage():
    chat, _ = gemini('{"status": "maybe"}')
    with pytest.raises(InvalidModelOutput) as caught:
        chat.generate_with_usage("q?", [CHUNK])
    assert caught.value.usage.input_tokens == 120


def test_gemini_api_errors_become_dependency_errors():
    error = errors.ClientError(429, {"error": {"message": "quota", "status": "RESOURCE_EXHAUSTED"}})
    chat, _ = gemini("", error=error)
    with pytest.raises(DependencyUnavailable):
        chat.generate("q?", [CHUNK])


def test_gemini_requires_a_model_and_a_key_from_settings():
    with pytest.raises(ValueError, match="OPENUSD_GEMINI_MODEL"):
        GeminiChat(Settings(_env_file=None, chat_provider="gemini"))
    with pytest.raises(ValueError, match="OPENUSD_GEMINI_API_KEY"):
        GeminiChat(Settings(_env_file=None, chat_provider="gemini", gemini_model="m"))


def test_api_key_is_secret_and_blank_means_unset():
    settings = Settings(_env_file=None, gemini_api_key="AIza-not-a-real-key")
    assert "AIza-not-a-real-key" not in repr(settings)
    assert settings.gemini_api_key.get_secret_value() == "AIza-not-a-real-key"
    assert Settings(_env_file=None, gemini_api_key="").gemini_api_key is None


def test_make_chat_keeps_ollama_by_default():
    ollama = object.__new__(OllamaModels)
    assert make_chat(Settings(_env_file=None), ollama) is ollama


class FakeOllamaChat:
    def __init__(self, result):
        self.result = result

    def invoke(self, messages):
        return self.result


def test_ollama_reports_usage_and_flags_parse_errors():
    models = object.__new__(OllamaModels)
    raw = SimpleNamespace(usage_metadata={"input_tokens": 50, "output_tokens": 9})
    models.chat = FakeOllamaChat({"raw": raw, "parsed": ANSWER, "parsing_error": None})
    draft, usage = models.generate_with_usage("q?", [CHUNK])
    assert draft.status == "answer" and usage == Usage(50, 9)
    models.chat = FakeOllamaChat({"raw": raw, "parsed": None, "parsing_error": ValueError("x")})
    with pytest.raises(InvalidModelOutput) as caught:
        models.generate("q?", [CHUNK])
    assert caught.value.usage == Usage(50, 9)


def test_generation_schema_requires_answer_text_and_evidence(monkeypatch):
    from openusd_assistant import adapters
    from openusd_assistant.chat import answer_schema

    assert answer_schema()["required"] == ["status", "answer", "evidence"]
    seen = {}

    class RecordingChat:
        def __init__(self, **kwargs):
            seen["init"] = kwargs

        def with_structured_output(self, schema, **kwargs):
            seen["schema"] = schema
            return self

    monkeypatch.setattr(adapters, "ChatOllama", RecordingChat)
    OllamaModels(Settings(_env_file=None, ollama_reasoning=True))
    assert seen["schema"]["required"] == ["status", "answer", "evidence"]
    assert seen["init"]["num_ctx"] == 16384 and seen["init"]["reasoning"] is True
