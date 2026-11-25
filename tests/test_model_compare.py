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
