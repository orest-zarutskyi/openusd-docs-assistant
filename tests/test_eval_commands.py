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
