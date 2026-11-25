"""Compare citation-check levels on saved answers (ADR 16). No model is called."""

import json
from pathlib import Path

from .answer_eval import (
    ANSWER,
    AnswerRecord,
    Price,
    answer_metrics,
    load_records,
    reverify,
    variant_score,
)
from .gate_compare import apply_gate, merge_outcomes
from .questions import load_questions
from .quotes import CITATION_CHECKS, match_quote


def _runs(directory: Path) -> dict[str, list[AnswerRecord]]:
    files = [f for f in sorted(directory.glob("*.jsonl")) if f.name != "verdicts.jsonl"]
    return {load_records(f)[0].model: load_records(f) for f in files}


def _accepted_quotes(record: AnswerRecord, check) -> list[tuple[str, str, str]]:
    """(quote as written, quote as shown, path) for every quote of an accepted answer."""
    out = []
    for q in record.quotes:
        chunks = sorted(record.context, key=lambda c: c["chunk_id"] != q["chunk_id"])
        for c in chunks if check != "strict" else chunks[:1]:
            shown = match_quote(q["quote"], c["text"], check)
            if shown is not None:
                out.append((q["quote"], shown, f"{c['path']}#L{c['lines'][0]}-L{c['lines'][1]}"))
                break
    return out


def choose_check(results: dict[str, dict], answerable: int) -> str:
    """ADR 16: no leaks; best mean score; within half an answerable question, the stricter."""
    allowed = [c for c in CITATION_CHECKS if results[c]["leaks"] == 0]
    if not allowed:
        raise ValueError("Every citation check lets an unanswerable question be answered.")
    best = max(results[c]["mean_score"] for c in allowed)
    tolerance = 0.5 / (2 * answerable) + 1e-9
    return next(c for c in allowed if best - results[c]["mean_score"] <= tolerance)


def compare_citations(
    questions_path: Path, baseline_dir: Path, nogate_dir: Path, scores_path: Path, threshold: float
) -> tuple[dict[str, dict], str, list[str]]:
    questions = load_questions(questions_path)
    answerable = sum(q.answerable for q in questions)
    scores = json.loads(scores_path.read_text(encoding="utf-8"))
    gate_off = _runs(nogate_dir)
    per_model = {
        spec: apply_gate(merge_outcomes(records, gate_off.get(spec, [])), scores, threshold)
        for spec, records in _runs(baseline_dir).items()
    }
    results: dict[str, dict] = {}
    newly: list[str] = []
    previous: dict[tuple[str, str], str] = {}
    for check in CITATION_CHECKS:
        models = {}
        for spec, records in per_model.items():
            checked = [reverify(r, check) for r in records]
            metrics = answer_metrics(checked, Price())
            models[spec] = {
                "score": variant_score(metrics),
                "answered": sum(r.answerable and r.outcome == ANSWER for r in checked),
                "leaks": sum(not r.answerable and r.outcome == ANSWER for r in checked),
            }
            for r in checked:
                key = (spec, r.id)
                if r.outcome == ANSWER and previous.get(key) != ANSWER and check != "strict":
                    for written, shown, where in _accepted_quotes(r, check):
                        newly.append(
                            f"| {check} | `{spec}` | `{r.id}` | {where} | {_cell(written)} | {_cell(shown)} |"
                        )
                previous[key] = r.outcome
        results[check] = {
            "models": models,
            "mean_score": sum(m["score"] for m in models.values()) / len(models),
            "leaks": sum(m["leaks"] for m in models.values()),
        }
    return results, choose_check(results, answerable), newly


def _cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|")[:220]


def citation_report(results: dict, chosen: str, newly: list[str], setup: list[str]) -> str:
    specs = list(results["strict"]["models"])
    lines = [
        "# Citation check comparison: second pass, dev",
        "",
        *setup,
        "",
        "Rule (ADR 16, committed before this run): exclude checks that make an unanswerable question "
        "count as answered; highest mean score over the models; within half an answerable question "
        "of the best, the stricter check.",
        "",
        "| Check | Mean score | Unanswerable answered | "
        + " | ".join(f"`{s}` answered" for s in specs)
        + " | Chosen |",
        "| --- | --- | --- | " + " | ".join("---" for _ in specs) + " | --- |",
    ]
    for check, r in results.items():
        cells = " | ".join(str(r["models"][s]["answered"]) for s in specs)
        mark = "yes" if check == chosen else ""
        lines.append(f"| {check} | {r['mean_score']:.3f} | {r['leaks']} | {cells} | {mark} |")
    lines += [
        "",
        "## Answers each check newly accepts",
        "",
        "Every quote of each newly accepted answer, as written by the model and as shown to the "
        "reader, with the chunk that supports it.",
        "",
        "| Check | Model | Question | Source | Quote as written | Quote as shown |",
        "| --- | --- | --- | --- | --- | --- |",
        *(newly or ["| — | — | — | — | — | — |"]),
    ]
    return "\n".join(lines) + "\n"
