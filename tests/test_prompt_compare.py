from openusd_assistant.prompt_compare import choose_prompt


def result(score, leaks=0):
    return {"mean_score": score, "leaks": leaks, "models": {}}


def test_choose_prompt_keeps_current_on_near_ties_and_excludes_leaks():
    assert choose_prompt({"v1": result(0.90), "v2": result(0.905)}, answerable=44) == "v1"
    assert choose_prompt({"v1": result(0.90), "v2": result(0.95)}, answerable=44) == "v2"
    assert choose_prompt({"v1": result(0.90), "v2": result(0.99, leaks=1)}, answerable=44) == "v1"
