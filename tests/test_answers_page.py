import json

from openusd_assistant.answer_eval import AnswerRecord, save_records
from openusd_assistant.answers_page import render_answers_page
from openusd_assistant.questions import Question, SourceSpan


def test_answers_page_escapes_model_text_and_shows_judge_and_sources(tmp_path):
    question = Question(
        id="payload",
        question="What is a <payload>?",
        kind="lookup",
        answerable=True,
        sources=[SourceSpan(path="docs/glossary.rst", start_line=1, end_line=2)],
        expected_facts=["Deferred reference.", "Loaded later."],
    )
    context = [{"chunk_id": "c1", "path": "docs/glossary.rst", "lines": [10, 12], "text": "t"}]
    save_records(
        tmp_path / "a.jsonl",
        [
            AnswerRecord(
                "payload",
                "lookup",
                True,
                "ollama:m",
                "answer",
                answer="<script>alert(1)</script> A deferred reference.",
                quotes=[{"chunk_id": "c1", "quote": 'a "deferred" <b>reference</b>'}],
                context=context,
                latency_ms=1500,
            )
        ],
    )
    save_records(
        tmp_path / "b.jsonl",
        [AnswerRecord("payload", "lookup", True, "gemini:g", "refused_retrieval")],
    )
    verdict = {
        "facts": [{"fact": "f1", "covered": True}, {"fact": "f2", "covered": False}],
        "claims": [{"claim": "It loads <later>.", "verdict": "unsupported"}],
    }
    (tmp_path / "verdicts.jsonl").write_text(
        json.dumps({"model": "ollama:m", "id": "payload", "verdict": verdict}) + "\n",
        encoding="utf-8",
    )
    html = render_answers_page([question], tmp_path, title="Dev", commit="abc")
    assert "<script>" not in html and "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "What is a &lt;payload&gt;?" in html and "&lt;b&gt;reference&lt;/b&gt;" in html
    assert (
        "https://github.com/PixarAnimationStudios/OpenUSD/blob/abc/docs/glossary.rst#L10-L12"
        in html
    )
    assert "judge: 1/2 facts, 1 claim(s) not supported" in html
    assert "unsupported: It loads &lt;later&gt;." in html
    assert "refused by retrieval gate" in html and "1.5 s" in html
    assert html.index("gemini:g") < html.index("ollama:m")  # models in a stable order
