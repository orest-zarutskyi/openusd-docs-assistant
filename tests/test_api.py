import pytest
from fastapi.testclient import TestClient

from openusd_assistant.api import create_app
from openusd_assistant.models import Chunk, DependencyTimeout, DraftAnswer, Evidence

PAYLOAD = Chunk(
    id="payload",
    path="docs/intro.rst",
    title="Composition operators",
    start_line=174,
    end_line=183,
    text="A payload may\n be loaded or unloaded after the stage has been opened.",
    url=(
        "https://github.com/PixarAnimationStudios/OpenUSD/blob/"
        "ee47c679abde5b467a7b6a41f3b2285564a4222e/docs/intro.rst#L174-L183"
    ),
)


def test_answer_has_verified_provenance():
    def retrieve(question):
        assert question == "Can I load payloads later?"
        return [PAYLOAD]

    def generate(question, context):
        assert context == [PAYLOAD]
        return DraftAnswer(
            status="answer",
            answer="Yes, you can load a payload after opening the stage.",
            evidence=[Evidence(chunk_id=PAYLOAD.id, quote="may be loaded or unloaded")],
        )

    with TestClient(create_app(retrieve, generate, lambda: True)) as client:
        response = client.post("/ask", json={"question": "  Can I load payloads later?  "})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "answer"
    assert body["sources"] == [
        {
            "chunk_id": PAYLOAD.id,
            "path": PAYLOAD.path,
            "title": PAYLOAD.title,
            "start_line": PAYLOAD.start_line,
            "end_line": PAYLOAD.end_line,
            "url": PAYLOAD.url,
            "quote": "may be loaded or unloaded",
        }
    ]


def test_empty_retrieval_skips_generation():
    def generate(*args):
        pytest.fail("generation must not run with empty retrieval")

    with TestClient(create_app(lambda question: [], generate, lambda: True)) as client:
        response = client.post("/ask", json={"question": "What setup did our studio use?"})

    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_context"
    assert response.json()["sources"] == []


def test_model_can_decline_even_when_search_returns_context():
    def generate(question, context):
        return DraftAnswer(status="insufficient_context")

    with TestClient(create_app(lambda question: [PAYLOAD], generate, lambda: True)) as client:
        response = client.post("/ask", json={"question": "Which settings should I use for smoke?"})

    assert response.json()["status"] == "insufficient_context"
    assert response.json()["sources"] == []


@pytest.mark.parametrize(
    ("chunk_id", "quote"),
    [
        ("not-retrieved", "may be loaded or unloaded"),
        (PAYLOAD.id, "a fabricated quotation"),
    ],
)
def test_unverified_evidence_is_rejected(chunk_id, quote):
    def generate(question, context):
        return DraftAnswer(
            status="answer",
            answer="An unverified answer.",
            evidence=[Evidence(chunk_id=chunk_id, quote=quote)],
        )

    with TestClient(create_app(lambda question: [PAYLOAD], generate, lambda: True)) as client:
        response = client.post("/ask", json={"question": "How do I load a payload?"})

    assert response.status_code == 502
    assert "An unverified answer" not in response.text


def test_readiness_validation_and_timeout_are_distinct():
    def retrieve(question):
        raise DependencyTimeout("sensitive provider error")

    def generate(*args):
        pytest.fail("generation must not run after a retrieval failure")

    with TestClient(create_app(retrieve, generate, lambda: False)) as client:
        assert client.get("/healthz").status_code == 200
        assert client.get("/readyz").status_code == 503
        assert client.post("/ask", json={"question": "   "}).status_code == 422
        response = client.post("/ask", json={"question": "How can I load a payload?"})

    assert response.status_code == 504
    assert "sensitive provider error" not in response.text
