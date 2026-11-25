from openusd_assistant.model_compare import choose_model


def r(score, p50=1000, p95=2000, leaks=0):
    return {"score": score, "p50_ms": p50, "p95_ms": p95, "leaks": leaks}


def test_choose_model_applies_leak_and_latency_limits_then_ties_by_p50():
    results = {
        "fast": r(0.900, p50=2000),
        "slow": r(0.902, p50=20000),
        "too-slow": r(0.990, p95=70000),
        "leaky": r(0.995, leaks=1),
    }
    assert choose_model(results, answerable=92) == "fast"  # within half a question: lower p50
    results["slow"] = r(0.95, p50=20000)
    assert choose_model(results, answerable=92) == "slow"


def _record(qid, outcome="answer", answerable=True, model="ollama:m"):
    from openusd_assistant.answer_eval import AnswerRecord

    return AnswerRecord(qid, "lookup", answerable, model, outcome, latency_ms=1000.0)


def test_merged_runs_joins_directories_and_rejects_duplicates(tmp_path):
    import pytest

    from openusd_assistant.answer_eval import save_records
    from openusd_assistant.model_compare import merged_runs

    save_records(tmp_path / "a" / "m.jsonl", [_record("q1", "refused_model")])
    save_records(tmp_path / "b" / "m.jsonl", [_record("q2", "refused_model")])
    merged = merged_runs([tmp_path / "a", tmp_path / "b"], "strict")
    assert [r.id for r in merged["ollama:m"]] == ["q1", "q2"]
    with pytest.raises(ValueError, match="more than once"):
        merged_runs([tmp_path / "a", tmp_path / "a"], "strict")


def test_runs_report_lists_runs_in_order_with_claimed_unanswerable():
    from openusd_assistant.model_compare import runs_report, summarize

    first = summarize([_record("q1", "refused_model"), _record("u1", "answer", answerable=False)])
    second = summarize([_record("q1", "refused_model"), _record("u1", "refused_model", False)])
    report = runs_report({"v1 `m`": first, "v2 `m`": second}, ["- setup"])
    rows = [line for line in report.splitlines() if line.startswith("| v")]
    assert [row.split(" | ")[0] for row in rows] == ["| v1 `m`", "| v2 `m`"]
    assert rows[0].split(" | ")[6] == "1" and rows[1].split(" | ")[6] == "0"
